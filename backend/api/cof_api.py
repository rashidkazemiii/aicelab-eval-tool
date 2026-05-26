import logging
import traceback
import pandas as pd
from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response, HTMLResponse
from session import state
from physics.cof import cof_calculate, cof_offset, cof_filter, cof_find_minima, cof_evaluate, CoF_Discontstatistics
from config import (
    DEFAULT_FILTER_WINDOW, DEFAULT_STATIC_RANGE, DEFAULT_DYN_MIN, DEFAULT_DYN_MAX,
    RESULT_COLUMNS, RESULT_COL_MAP,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cof")


# ---------------------------------------------------------------------------
# Pipeline: calculate → offset → filter
# ---------------------------------------------------------------------------

@router.post("/calculate")
def calculate():
    if state.df_raw is None:
        return JSONResponse(status_code=400, content={"error": "No file uploaded yet"})
    try:
        df = state.df_raw.copy()
        # OFT files need CoF computed from friction-force columns.
        # SRV / SRV_FSA already export a 'cof' column — skip the calculation.
        if "cof" not in df.columns:
            df = cof_calculate(df, None)
        keep = ["time", "cof", "stroke", "external displacement"]
        state.df_work = df[[c for c in keep if c in df.columns]].copy()
        state.df_work["cof"] = state.df_work["cof"].round(5)
        state.df_result     = None
        state.df_step_stats = None
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Calculate failed: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/calculated")
def get_calculated():
    if state.df_work is None:
        return JSONResponse(status_code=400, content={"error": "Run calculate first"})
    data = state.df_work[["time", "cof"]]
    return Response(
        content=data.to_json(orient="records", double_precision=5),
        media_type="application/json"
    )


@router.post("/offset")
def offset():
    if state.df_work is None:
        return JSONResponse(status_code=400, content={"error": "Run calculate first"})
    try:
        state.df_work["cof_shifted"] = cof_offset(state.df_work["cof"], state.df_work["time"], state.step_df).values
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Offset failed: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/offset")
def get_offset():
    if state.df_work is None or "cof_shifted" not in state.df_work.columns:
        return JSONResponse(status_code=400, content={"error": "Run offset first"})
    return Response(
        content=state.df_work[["time", "cof_shifted"]].to_json(orient="records", double_precision=8),
        media_type="application/json"
    )


@router.post("/filter")
def filter(window: int = DEFAULT_FILTER_WINDOW):
    if state.df_work is None:
        return JSONResponse(status_code=400, content={"error": "Run calculate first"})
    try:
        source = "cof_shifted" if "cof_shifted" in state.df_work.columns else "cof"
        state.df_work["cof_filtered"] = cof_filter(state.df_work[source], window).values
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Filter failed: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/filter")
def get_filter():
    if state.df_work is None or "cof_filtered" not in state.df_work.columns:
        return JSONResponse(status_code=400, content={"error": "Run filter first"})
    cols = ["time", "cof_shifted", "cof_filtered"]
    present = [c for c in cols if c in state.df_work.columns]
    return Response(
        content=state.df_work[present].rename(columns={"cof_filtered": "filtered"}).to_json(orient="records", double_precision=8),
        media_type="application/json"
    )


# ---------------------------------------------------------------------------
# Evaluate: cycle analysis → results
# ---------------------------------------------------------------------------

def _cof_minima(df, column):
    """Find zero-crossing minima and rename columns to the standard CoF schema."""
    m = cof_find_minima(df, column)
    return m.rename(columns={
        f"-Min {column}": "-Min CoF",
        f"+Min {column}": "+Min CoF",
        f"Min {column}":  "Min CoF",
    })


def _per_cycle_stats(df_eval, minima, static_range, dyn_min, dyn_max):
    """Compute per-cycle static and dynamic CoF statistics."""
    return cof_evaluate(df_eval, minima, static_range, dyn_min, dyn_max)


def _aggregate_stats(per_cycle, time_range):
    """Compute aggregate statistics across all cycles."""
    return {
        "timeRange":         time_range,
        "staticMeanCoF":     per_cycle["staticCoF"].abs().mean(),
        "staticCoFSD_agg":   per_cycle["staticCoF"].abs().std(),
        "staticCoFN_agg":    int(per_cycle["staticCoF"].count()),
        "staticCoFSum_agg":  per_cycle["staticCoF"].abs().sum(),
        "staticCoFVar_agg":  (per_cycle["staticCoF"] ** 2).sum(),
        "dynamicMeanCoF":    per_cycle["dynamicCoFsigma"].sum() / per_cycle["dynamicCoFn"].sum(),
        "dynamicCoFSD_agg":  (
            (per_cycle["dynamicCoFvariance"].sum() - per_cycle["dynamicCoFsigma"].sum() ** 2 / per_cycle["dynamicCoFn"].sum())
            / (per_cycle["dynamicCoFn"].sum() - 1)
        ) ** 0.5,
        "dynamicCoFN_agg":   int(per_cycle["dynamicCoFn"].sum()),
        "dynamicCoFSum_agg": per_cycle["dynamicCoFsigma"].sum(),
        "dynamicCoFVar_agg": per_cycle["dynamicCoFvariance"].sum(),
        "integralTimeRange": time_range,
    }


def _displacement_data(df_work, neg_times):
    """Find displacement minima and per-cycle maxima aligned to CoF cycle boundaries."""
    disp_col = next(
        (c for c in ("external displacement", "stroke_filtered", "stroke_shifted", "stroke")
         if c in df_work.columns),
        None
    )
    if disp_col is None:
        return pd.DataFrame()

    dm = cof_find_minima(df_work, disp_col)
    dm = dm.rename(columns={
        "neg_time":         "disp_neg_time",
        f"-Min {disp_col}": "-Min disp",
        "pos_time":         "disp_pos_time",
        f"+Min {disp_col}": "+Min disp",
        "zero_time":        "disp_zero_time",
        f"Min {disp_col}":  "Min disp",
    }).reset_index(drop=True)

    disp_df = df_work[["time", disp_col]]
    max_times, max_vals = [], []
    for i in range(len(neg_times) - 1):
        seg = disp_df[
            (disp_df["time"] >= neg_times[i]) &
            (disp_df["time"] <= neg_times[i + 1])
        ]
        if len(seg):
            idx = seg[disp_col].abs().idxmax()
            max_times.append(seg.loc[idx, "time"])
            max_vals.append(seg.loc[idx, disp_col])

    n = len(max_vals)
    dm["dispMaxTime"] = float("nan")
    dm["dispMax"]     = float("nan")
    if n:
        k = min(n, len(dm))
        dm.loc[:k - 1, "dispMaxTime"] = max_times[:k]
        dm.loc[:k - 1, "dispMax"]     = max_vals[:k]

    return dm


@router.post("/evaluate")
def evaluate(
    static_cof_range:        float = DEFAULT_STATIC_RANGE,
    beginning_dynamic_range: float = DEFAULT_DYN_MIN,
    ending_dynamic_range:    float = DEFAULT_DYN_MAX,
):
    if state.df_work is None:
        return JSONResponse(status_code=400, content={"error": "Run calculate first"})
    try:
        column = (
            "cof_filtered" if "cof_filtered" in state.df_work.columns else
            "cof_shifted"  if "cof_shifted"  in state.df_work.columns else
            "cof"
        )

        minima  = _cof_minima(state.df_work, column)
        df_eval = state.df_work.copy()
        if "cof_shifted" in df_eval.columns:
            df_eval["cof"] = df_eval["cof_shifted"]

        per_cycle = _per_cycle_stats(
            df_eval, minima, static_cof_range,
            beginning_dynamic_range, ending_dynamic_range
        )
        agg  = _aggregate_stats(
            per_cycle,
            state.df_work["time"].max() - state.df_work["time"].min()
        )
        disp = _displacement_data(state.df_work, minima["neg_time"].tolist())

        n = len(per_cycle)
        n_rows = max(n, len(minima))
        state.df_result = pd.DataFrame(float("nan"), index=range(n_rows), columns=RESULT_COLUMNS)

        for col in per_cycle.columns:
            if col in state.df_result.columns:
                state.df_result.loc[:n - 1, col] = per_cycle[col].values

        for col in minima.columns:
            if col in state.df_result.columns:
                state.df_result.loc[:len(minima) - 1, col] = minima[col].values

        if state.data_type == "SRV_FSA" and state.step_df is not None and n > 0:
            # SRV_FSA: fill one aggregate row per active step (N rows instead of 1).
            # "Time Range" from CoF_Discontstatistics is a string ("0.0–2.5"),
            # so convert that column to object dtype before writing.
            step_stats = CoF_Discontstatistics(per_cycle, state.step_df)
            state.df_step_stats = step_stats
            state.df_result["timeRange"] = state.df_result["timeRange"].astype(object)
            _STEP_COL_MAP = {
                "Time Range":      "timeRange",
                "Static Avg":      "staticMeanCoF",
                "Static Std Dev":  "staticCoFSD_agg",
                "Static N":        "staticCoFN_agg",
                "Static Avg x N":  "staticCoFSum_agg",
                "Static Var":      "staticCoFVar_agg",
                "Dynamic Avg":     "dynamicMeanCoF",
                "Dynamic Std Dev": "dynamicCoFSD_agg",
                "Dynamic N":       "dynamicCoFN_agg",
                "Dynamic Avg x N": "dynamicCoFSum_agg",
                "Dynamic Var":     "dynamicCoFVar_agg",
            }
            for step_i, step_row in step_stats.reset_index(drop=True).iterrows():
                for src, dst in _STEP_COL_MAP.items():
                    if src in step_row.index and dst in state.df_result.columns:
                        state.df_result.loc[step_i, dst] = step_row[src]
        elif n > 0:
            # OFT / SRV: single aggregate row (unchanged)
            for col, val in agg.items():
                state.df_result.loc[0, col] = val
            state.df_step_stats = None

        d = min(len(disp), n_rows)
        for col in disp.columns:
            if col in state.df_result.columns:
                state.df_result.loc[:d - 1, col] = disp[col].values[:d]

        agg_serializable = {k: (None if pd.isna(v) else v) for k, v in agg.items()
                            if not isinstance(v, pd.Series)}
        return {"status": "success", "cycles": n, "aggregate": agg_serializable}

    except Exception as e:
        logger.error(f"Evaluate failed: {e}\n{traceback.format_exc()}")
        state.last_error = str(e)
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/result/json")
def get_result_json():
    if state.df_result is None:
        return JSONResponse(status_code=400, content={"error": "Run evaluate first"})
    return Response(
        content=state.df_result.to_json(orient="records", double_precision=8),
        media_type="application/json"
    )


@router.get("/result/html")
def get_result_html():
    if state.df_result is None:
        last_err = state.last_error
        msg = f"<p style='color:#c0392b'><b>Last error:</b> {last_err}</p>" if last_err else ""
        return HTMLResponse(content=f"""<!DOCTYPE html><html><head><title>Result</title>
<style>body{{font-family:monospace;padding:40px;background:#f4f6f8;color:#1f2a40}}</style></head>
<body><h2>No results yet</h2>
<p>Run <b>Evaluate</b> on the Analysis page first.</p>{msg}</body></html>""")

    df_view = state.df_result[[k for k, _ in RESULT_COL_MAP]].rename(columns=dict(RESULT_COL_MAP))
    table = df_view.to_html(index=False, border=0, classes="data-table", na_rep="")
    html = f"""<!DOCTYPE html><html><head><title>Result</title>
<style>
  body {{ font-family: monospace; font-size: 12px; padding: 20px; background: #f4f6f8; overflow-x: auto; }}
  h2 {{ color: #1f2a40; }}
  .data-table {{ border-collapse: collapse; background: #fff; white-space: nowrap; }}
  .data-table th {{ background: #1f2a40; color: #fff; padding: 6px 12px; text-align: right; position: sticky; top: 0; }}
  .data-table td {{ padding: 4px 12px; text-align: right; border-bottom: 1px solid #e0e0e0; }}
  .data-table tr:hover td {{ background: #eef2ff; }}
</style></head>
<body><h2>Evaluation Result</h2>{table}</body></html>"""
    return HTMLResponse(content=html)


# ---------------------------------------------------------------------------
# SRV_FSA per-step statistics  (new — OFT result above is untouched)
# ---------------------------------------------------------------------------

@router.get("/step-stats/json")
def get_step_stats_json():
    if state.df_step_stats is None:
        return JSONResponse(status_code=400, content={"error": "No step stats available. Run evaluate on an SRV_FSA file first."})
    return Response(
        content=state.df_step_stats.to_json(orient="records", double_precision=8),
        media_type="application/json",
    )


@router.get("/step-stats/html")
def get_step_stats_html():
    if state.df_step_stats is None:
        last_err = state.last_error
        msg = f"<p style='color:#c0392b'><b>Last error:</b> {last_err}</p>" if last_err else ""
        return HTMLResponse(content=f"""<!DOCTYPE html><html><head><title>Step Stats</title>
<style>body{{font-family:monospace;padding:40px;background:#f4f6f8;color:#1f2a40}}</style></head>
<body><h2>No step stats yet</h2>
<p>Run <b>Evaluate</b> on an <b>SRV_FSA</b> file first.</p>{msg}</body></html>""")

    table = state.df_step_stats.to_html(index=False, border=0, classes="data-table", na_rep="")
    html = f"""<!DOCTYPE html><html><head><title>Step Statistics</title>
<style>
  body {{ font-family: monospace; font-size: 12px; padding: 20px; background: #f4f6f8; overflow-x: auto; }}
  h2 {{ color: #1f2a40; }}
  .data-table {{ border-collapse: collapse; background: #fff; white-space: nowrap; }}
  .data-table th {{ background: #1f2a40; color: #fff; padding: 6px 12px; text-align: right; position: sticky; top: 0; }}
  .data-table td {{ padding: 4px 12px; text-align: right; border-bottom: 1px solid #e0e0e0; }}
  .data-table tr:hover td {{ background: #eef2ff; }}
</style></head>
<body><h2>Per-Step Statistics (SRV_FSA)</h2>{table}</body></html>"""
    return HTMLResponse(content=html)
