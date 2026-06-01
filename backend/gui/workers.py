"""
QRunnable workers for all blocking physics/IO operations.
Each worker emits finished or error signals via a companion Signals QObject.
"""
import traceback
import numpy as np
import pandas as pd

from PyQt6.QtCore import QRunnable, QObject, pyqtSignal

from parsers.loader import load_data
from physics.cof import (
    cof_calculate, cof_offset, cof_filter, cof_step_filter,
    cof_find_minima, cof_evaluate, CoF_Discontstatistics,
)
from physics.stroke import (
    stroke_offset, stroke_filter, stroke_find_minima, stroke_evaluate,
)
from config import RESULT_COLUMNS
from database import SessionLocal, Test, save_evaluation
from gui.state import app_state


# ---------------------------------------------------------------------------
# Signals helper (QRunnable can't directly be a QObject)
# ---------------------------------------------------------------------------

class WorkerSignals(QObject):
    finished = pyqtSignal()
    error    = pyqtSignal(str)
    conflict = pyqtSignal(str, str)  # filename, existing_date (SaveWorker only)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pick_cof_col(df: pd.DataFrame) -> str:
    for col in ("cof_filtered", "cof_shifted", "cof"):
        if col in df.columns:
            return col
    raise ValueError("No CoF column found in working DataFrame.")


def _pick_stroke_col(df: pd.DataFrame) -> str:
    for col in ("stroke_filtered", "stroke_shifted", "stroke"):
        if col in df.columns:
            return col
    raise ValueError("No stroke column found in working DataFrame.")


def _build_df_work(df_raw: pd.DataFrame, data_type: str, header: dict | None) -> pd.DataFrame:
    """Replicate cof_api.calculate() logic — build df_work from df_raw."""
    df = df_raw.copy()

    if data_type == "OFT":
        correction = None
        if header and header.get("load_correction_factor") not in (None, 0):
            correction = float(header["load_correction_factor"])
        df = cof_calculate(df, correction)
    # SRV / SRV_FSA already have a "cof" column from the parser

    keep = ["time", "cof"]
    if "stroke" in df.columns:
        keep.append("stroke")
    if "external displacement" in df.columns:
        keep.append("external displacement")
    return df[[c for c in keep if c in df.columns]].reset_index(drop=True)


def _aggregate_stats(per_cycle: pd.DataFrame) -> dict:
    """Compute aggregate CoF statistics from per-cycle DataFrame."""
    static_abs = per_cycle["staticCoF"].abs().dropna()
    n_s = len(static_abs)
    if n_s == 0:
        return {}
    mean_s = float(static_abs.mean())
    sd_s   = float(static_abs.std(ddof=1)) if n_s > 1 else 0.0
    sum_s  = mean_s * n_s
    var_s  = sd_s**2 * (n_s - 1) + sum_s**2 / n_s if n_s > 0 else 0.0

    n_d   = int(per_cycle["dynamicCoFn"].sum())
    sum_d = float(per_cycle["dynamicCoFsigma"].sum())
    var_d = float(per_cycle["dynamicCoFvariance"].sum())
    mean_d = sum_d / n_d if n_d > 0 else 0.0
    sd_d   = (
        ((var_d - sum_d**2 / n_d) / (n_d - 1))**0.5
        if n_d > 1 else 0.0
    )

    return {
        "staticMeanCoF":    mean_s,
        "staticCoFSD_agg":  sd_s,
        "staticCoFN_agg":   n_s,
        "staticCoFSum_agg": sum_s,
        "staticCoFVar_agg": var_s,
        "dynamicMeanCoF":    mean_d,
        "dynamicCoFSD_agg":  sd_d,
        "dynamicCoFN_agg":   n_d,
        "dynamicCoFSum_agg": sum_d,
        "dynamicCoFVar_agg": var_d,
    }


def _build_df_result(df_work, per_cycle, minima, disp_minima, disp_maxima,
                     time_range, agg, cof_col):
    """Assemble the full RESULT_COLUMNS DataFrame."""
    n = len(per_cycle)

    def _pad(series_or_list, length=n):
        arr = list(series_or_list) if hasattr(series_or_list, '__iter__') else [series_or_list]
        arr = arr[:length]
        arr += [float('nan')] * (length - len(arr))
        return arr

    # Minima columns — rename from cof_col back to "CoF"
    def _col(df, name):
        return df[name].tolist() if (df is not None and name in df.columns) else [np.nan] * n

    neg_time  = _pad(_col(minima, "neg_time"))
    min_cof_n = _pad(_col(minima, f"-Min {cof_col}"))
    pos_time  = _pad(_col(minima, "pos_time"))
    min_cof_p = _pad(_col(minima, f"+Min {cof_col}"))
    zero_time = _pad(_col(minima, "zero_time"))

    # Displacement
    dneg  = _pad(_col(disp_minima, "neg_time"))
    dmin_n= _pad(_col(disp_minima, f"-Min stroke_filtered") or _col(disp_minima, "-Min stroke"))
    dpos  = _pad(_col(disp_minima, "pos_time"))
    dmin_p= _pad(_col(disp_minima, f"+Min stroke_filtered") or _col(disp_minima, "+Min stroke"))
    dzero = _pad(_col(disp_minima, "zero_time"))
    dmxt  = _pad(_col(disp_maxima, "maxstrokeTime"))
    dmx   = _pad(_col(disp_maxima, "maxstroke"))

    rows = []
    for i in range(n):
        row = {}
        for col in RESULT_COLUMNS:
            row[col] = np.nan
        # Per-cycle from cof_evaluate
        for c in per_cycle.columns:
            if c in row:
                row[c] = per_cycle.iloc[i][c]
        # Aggregate (broadcast)
        row["timeRange"] = time_range
        row.update(agg)
        # Minima
        row["neg_time"]  = neg_time[i]
        row["-Min CoF"]  = min_cof_n[i]
        row["pos_time"]  = pos_time[i]
        row["+Min CoF"]  = min_cof_p[i]
        row["zero_time"] = zero_time[i]
        row["Min CoF"]   = 0.0
        # Displacement
        row["disp_neg_time"] = dneg[i]
        row["-Min disp"]     = dmin_n[i]
        row["disp_pos_time"] = dpos[i]
        row["+Min disp"]     = dmin_p[i]
        row["disp_zero_time"]= dzero[i]
        row["Min disp"]      = 0.0
        row["dispMaxTime"]   = dmxt[i]
        row["dispMax"]       = dmx[i]
        rows.append(row)

    return pd.DataFrame(rows, columns=RESULT_COLUMNS)


# ---------------------------------------------------------------------------
# Worker: Load file
# ---------------------------------------------------------------------------

class LoadFileWorker(QRunnable):
    def __init__(self, file_path: str, data_type: str):
        super().__init__()
        self.file_path = file_path
        self.data_type = data_type
        self.signals   = WorkerSignals()

    def run(self):
        try:
            s = app_state.session
            s.reset()
            s.file_path = self.file_path
            s.data_type = self.data_type

            df_raw, step_df, header = load_data(self.file_path, self.data_type)
            s.df_raw  = df_raw
            s.step_df = step_df
            s.header  = header

            s.df_work = _build_df_work(df_raw, self.data_type, header)
            self.signals.finished.emit()
        except Exception:
            self.signals.error.emit(traceback.format_exc())


# ---------------------------------------------------------------------------
# Worker: CoF Offset
# ---------------------------------------------------------------------------

class CoFOffsetWorker(QRunnable):
    def __init__(self):
        super().__init__()
        self.signals = WorkerSignals()

    def run(self):
        try:
            s = app_state.session
            df = s.df_work
            df["cof_shifted"] = cof_offset(df["cof"], df["time"], s.step_df)
            self.signals.finished.emit()
        except Exception:
            self.signals.error.emit(traceback.format_exc())


# ---------------------------------------------------------------------------
# Worker: CoF Filter
# ---------------------------------------------------------------------------

class CoFFilterWorker(QRunnable):
    def __init__(self, window: int):
        super().__init__()
        self.window  = window
        self.signals = WorkerSignals()

    def run(self):
        try:
            s   = app_state.session
            df  = s.df_work
            src = "cof_shifted" if "cof_shifted" in df.columns else "cof"
            if s.data_type == "SRV_FSA" and s.step_df is not None:
                df["cof_filtered"] = cof_step_filter(df[src], df["time"], s.step_df, self.window)
            else:
                df["cof_filtered"] = cof_filter(df[src], self.window)
            self.signals.finished.emit()
        except Exception:
            self.signals.error.emit(traceback.format_exc())


# ---------------------------------------------------------------------------
# Worker: CoF Evaluate (full pipeline)
# ---------------------------------------------------------------------------

class CoFEvaluateWorker(QRunnable):
    def __init__(self, static_range: float, dyn_min: float, dyn_max: float):
        super().__init__()
        self.static_range = static_range
        self.dyn_min      = dyn_min
        self.dyn_max      = dyn_max
        self.signals      = WorkerSignals()

    def run(self):
        try:
            s        = app_state.session
            df       = s.df_work
            cof_col  = _pick_cof_col(df)
            eval_df  = df.rename(columns={cof_col: "cof"}) if cof_col != "cof" else df.copy()

            minima     = cof_find_minima(eval_df, "cof")
            per_cycle  = cof_evaluate(
                eval_df, minima,
                self.static_range, self.dyn_min, self.dyn_max,
            )
            if per_cycle.empty:
                raise ValueError("No cycles detected — try applying Offset and Filter first.")

            agg        = _aggregate_stats(per_cycle)
            time_range = float(df["time"].max() - df["time"].min())
            agg["timeRange"] = time_range

            # Step statistics (SRV_FSA)
            if s.data_type == "SRV_FSA" and s.step_df is not None:
                s.df_step_stats = CoF_Discontstatistics(per_cycle, s.step_df)
            else:
                s.df_step_stats = None

            # Displacement minima + maxima (for RESULT_COLUMNS)
            disp_minima = None
            disp_maxima = None
            if "stroke" in df.columns or "stroke_filtered" in df.columns:
                try:
                    stroke_col  = _pick_stroke_col(df)
                    stroke_df   = df.rename(columns={stroke_col: "stroke"}) if stroke_col != "stroke" else df.copy()
                    disp_minima = stroke_find_minima(stroke_df, "stroke")
                    disp_maxima = stroke_evaluate(stroke_df, disp_minima)
                except Exception:
                    pass  # displacement is optional

            s.df_result = _build_df_result(
                df, per_cycle, minima, disp_minima, disp_maxima,
                time_range, agg, cof_col,
            )
            self.signals.finished.emit()
        except Exception:
            self.signals.error.emit(traceback.format_exc())


# ---------------------------------------------------------------------------
# Worker: Stroke Offset
# ---------------------------------------------------------------------------

class StrokeOffsetWorker(QRunnable):
    def __init__(self):
        super().__init__()
        self.signals = WorkerSignals()

    def run(self):
        try:
            s  = app_state.session
            df = s.df_work
            src = "stroke" if "stroke" in df.columns else "external displacement"
            df["stroke_shifted"] = stroke_offset(df[src], df["time"], s.step_df)
            self.signals.finished.emit()
        except Exception:
            self.signals.error.emit(traceback.format_exc())


# ---------------------------------------------------------------------------
# Worker: Stroke Filter
# ---------------------------------------------------------------------------

class StrokeFilterWorker(QRunnable):
    def __init__(self, window: int):
        super().__init__()
        self.window  = window
        self.signals = WorkerSignals()

    def run(self):
        try:
            s   = app_state.session
            df  = s.df_work
            src = "stroke_shifted" if "stroke_shifted" in df.columns else "stroke"
            df["stroke_filtered"] = stroke_filter(df[src], self.window)
            self.signals.finished.emit()
        except Exception:
            self.signals.error.emit(traceback.format_exc())


# ---------------------------------------------------------------------------
# Worker: Stroke Evaluate
# ---------------------------------------------------------------------------

class StrokeEvaluateWorker(QRunnable):
    def __init__(self):
        super().__init__()
        self.signals = WorkerSignals()

    def run(self):
        try:
            s        = app_state.session
            df       = s.df_work
            col      = _pick_stroke_col(df)
            eval_df  = df.rename(columns={col: "stroke"}) if col != "stroke" else df.copy()
            minima   = stroke_find_minima(eval_df, "stroke")
            stroke_evaluate(eval_df, minima)
            self.signals.finished.emit()
        except Exception:
            self.signals.error.emit(traceback.format_exc())


# ---------------------------------------------------------------------------
# Worker: Save
# ---------------------------------------------------------------------------

class SaveWorker(QRunnable):
    def __init__(self, force: bool = False):
        super().__init__()
        self.force   = force
        self.signals = WorkerSignals()

    def run(self):
        try:
            s = app_state.session
            if s.df_result is None:
                raise ValueError("Nothing to save — run Evaluate first.")

            import os
            file_name = os.path.basename(s.file_path) if s.file_path else "unknown"

            if not self.force:
                db = SessionLocal()
                try:
                    existing = db.query(Test).filter(Test.file_name == file_name).first()
                finally:
                    db.close()
                if existing:
                    date_str = existing.uploaded_at.strftime("%Y-%m-%d %H:%M")
                    self.signals.conflict.emit(file_name, date_str)
                    return

            per_cycle_df = s.df_result[[
                "staticCoFTime", "staticCoF",
                "dynamicCoFTime", "dynamicCoF", "dynamicCoFSD", "dynamicCoFn",
                "dynamicCoFsigma", "dynamicCoFvariance",
            ]].copy()

            first = s.df_result.iloc[0]
            agg = {
                "timeRange":        first.get("timeRange"),
                "staticMeanCoF":    first.get("staticMeanCoF"),
                "staticCoFSD_agg":  first.get("staticCoFSD_agg"),
                "staticCoFN_agg":   first.get("staticCoFN_agg"),
                "staticCoFSum_agg": first.get("staticCoFSum_agg"),
                "staticCoFVar_agg": first.get("staticCoFVar_agg"),
                "dynamicMeanCoF":   first.get("dynamicMeanCoF"),
                "dynamicCoFSD_agg": first.get("dynamicCoFSD_agg"),
                "dynamicCoFN_agg":  first.get("dynamicCoFN_agg"),
                "dynamicCoFSum_agg":first.get("dynamicCoFSum_agg"),
                "dynamicCoFVar_agg":first.get("dynamicCoFVar_agg"),
            }

            save_evaluation(
                file_name     = file_name,
                data_type     = s.data_type,
                filter_window = 100,
                static_range  = 15.0,
                dynamic_min   = 20.0,
                dynamic_max   = 80.0,
                agg           = agg,
                per_cycle_df  = per_cycle_df,
                step_stats_df = s.df_step_stats,
            )
            self.signals.finished.emit()
        except Exception:
            self.signals.error.emit(traceback.format_exc())
