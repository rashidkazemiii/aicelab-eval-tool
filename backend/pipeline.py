"""The main data -> CoF -> filter -> evaluate -> stats pipeline.

Each function here is the "recipe" for one step of the pipeline shown in the
CoF Analysis tab, built out of calls to data_loader / physics.CoF /
physics.utility_functions / physics.statistics. Kept separate from app.py so
the pipeline logic can be read and edited in one place, without it being
mixed into marimo cell bodies.
"""

import pandas as pd

from physics import CoF as cof_calc
from physics import utility_functions
from physics import statistics as stat_funcs


def rename_columns_by_position(df_raw, params):
    """Rename df_raw's columns to the fixed names CoF.calculate expects, using
    the 1-indexed column numbers in `params` (col_time, col_left, col_right,
    col_load). A column number of 0 means "not present" - that column is left
    unrenamed.
    """
    cols = df_raw.columns
    rename = {}
    col_time = int(params["col_time"])
    col_left = int(params["col_left"])
    col_right = int(params["col_right"])
    col_load = int(params["col_load"])
    if col_time > 0:
        rename[cols[col_time - 1]] = "Zeit"
    if col_left > 0:
        rename[cols[col_left - 1]] = "RK OFT Links"
    if col_right > 0:
        rename[cols[col_right - 1]] = "RK OFT Rechts"
    if col_load > 0:
        rename[cols[col_load - 1]] = "Belastung"
    return df_raw.rename(columns=rename)


def compute_display_df(df_raw, step_df, params, offset_on):
    """Build the display dataframe: rename columns, compute CoF, round it,
    trim to the step range (if any), and apply the offset toggle. Raises on
    any conversion/computation error - the caller is expected to wrap this in
    its own try/except.
    """
    df_display = rename_columns_by_position(df_raw, params).copy()
    if params["nlc"]:
        nlc = float(params["nlc"])
    else:
        nlc = None
    df_display = cof_calc.calculate(df_display, nlc)
    df_display["CoF"] = df_display["CoF"].round(5)
    if step_df is not None:
        trim_start = float(step_df["Startzeit [s]"].min())
        trim_end = round(float(step_df["Endzeit [s]"].max()))
        df_display = utility_functions.trim(df_display, trim_start, trim_end)
        if "Drehzahl" in step_df.columns:
            df_display = utility_functions.assign_step_speed(df_display, step_df)
    if offset_on:
        df_display = utility_functions.offset(df_display)
    return df_display


def compute_filtered_df(df_display, filter_params):
    """Apply the Filter form to df_display. Returns a plain copy of
    df_display if there are no filter params yet, or the window is <= 1
    (filter disabled). Raises on conversion/computation error.
    """
    if filter_params is None:
        return df_display.copy()
    window = int(filter_params["filter_points"])
    if window <= 1:
        return df_display.copy()
    method = filter_params.get("method", "vba")
    return utility_functions.filter(df_display.copy(), window, method=method)


def is_filter_active(filter_params, df_proc):
    """True once the Filter form has actually been submitted with a window
    > 1 and df_proc holds a real filtered result (not just a copy).
    """
    if filter_params is None:
        return False
    if int(filter_params.get("filter_points", 1)) <= 1:
        return False
    return df_proc is not None


def compute_evaluation(df_display, df_proc, eval_params):
    """Run Find_minima + Evaluate for the Evaluate form. Returns a dict with
    "minima" and "cof_res", or None if the inputs aren't ready yet. Raises on
    conversion/computation error.
    """
    if df_proc is None or df_display is None or eval_params is None:
        return None
    minima = cof_calc.find_minima(df_proc)
    cof_res = cof_calc.get_static_and_dynamic_cof(
        df_display, minima,
        float(eval_params["static_range"]),
        float(eval_params["dyn_min"]),
        float(eval_params["dyn_max"]),
    )
    return {"minima": minima, "cof_res": cof_res}


def compute_stats(cof_eval, df_display, step_df):
    """Per-step CoF statistics for the current evaluation. Falls back to a
    single synthetic step spanning the whole file when there's no step data.
    Raises on conversion/computation error.
    """
    if step_df is not None:
        steps = step_df
    else:
        steps = pd.DataFrame({
            "Startzeit [s]": [df_display["Zeit"].min()],
            "Endzeit [s]":   [df_display["Zeit"].max()],
            "inactive":      [False],
        })
    return stat_funcs.CoF_Stat(cof_eval["cof_res"], steps)
