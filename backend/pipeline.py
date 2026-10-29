"""The main data -> CoF -> filter -> evaluate -> stats pipeline.

Each function here is the "recipe" for one step of the pipeline shown in the
CoF Analysis tab, built out of calls to data_loader / physics.CoF /
physics.utility_functions / physics.statistics. Kept separate from app.py so
the pipeline logic can be read and edited in one place, without it being
mixed into marimo cell bodies.
"""

import numpy as np
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
    return utility_functions.filter(df_display.copy(), window)


def is_filter_active(filter_params, df_proc):
    """True once the Filter form has actually been submitted with a window
    > 1 and df_proc holds a real filtered result (not just a copy).
    """
    if filter_params is None:
        return False
    if int(filter_params.get("filter_points", 1)) <= 1:
        return False
    return df_proc is not None


def compute_zero_crossings(df_proc):
    """"Find zeros": the zero crossings of the (filtered) CoF, as
    Find_minima's table. They anchor the speed pulse and decide which steps
    are too noisy for Evaluate with pulse. None if there is no data yet.
    """
    if df_proc is None:
        return None
    return cof_calc.find_minima(df_proc)


def pulse_edges_to_minima(df_display, pulse_edges):
    """Turn the speed pulse's edges into a zero-crossing table shaped like
    Find_minima's result, so Evaluate can use them as cycle boundaries.

    Each edge time is moved to the nearest raw sample (Evaluate looks the
    crossing up by its exact sample time). That sample and the next one
    stand in for the "-Min"/"+Min" pair; "Min Zeit" keeps the exact edge
    time for the chart marker. Edges outside the recording are dropped.

    The extra "direction" column (+1 rising edge, -1 falling edge) tells
    Evaluate which side to look for the static peak on: a rising edge
    starts a positive half-cycle, so only positive peaks count there, and
    the other way round for a falling edge.
    """
    times = df_display["Zeit"].to_numpy()
    values = df_display["CoF"].to_numpy()
    n = len(times)

    ordered = pulse_edges.sort_values("time")
    edge_times = ordered["time"].tolist()
    edge_levels = ordered["level_after"].tolist()

    neg_time = []
    neg_cof = []
    pos_time = []
    pos_cof = []
    cross_time = []
    direction = []
    for j in range(len(edge_times)):
        t = edge_times[j]
        i = int(np.searchsorted(times, t))
        if i >= n:
            i = n - 1
        if i > 0 and abs(times[i - 1] - t) < abs(times[i] - t):
            i = i - 1
        if i >= n - 1:
            continue
        neg_time.append(times[i])
        neg_cof.append(values[i])
        pos_time.append(times[i + 1])
        pos_cof.append(values[i + 1])
        cross_time.append(t)
        if edge_levels[j] >= 0:
            direction.append(1)
        else:
            direction.append(-1)

    return pd.DataFrame({
        "-Min Zeit": neg_time,
        "-Min CoF": neg_cof,
        "+Min Zeit": pos_time,
        "+Min CoF": pos_cof,
        "Min Zeit": cross_time,
        "Min CoF": [0] * len(cross_time),
        "direction": direction,
    })


def compute_pulse_evaluation(df_display, pulse_edges, eval_params):
    """"Evaluate with pulse": the cycle boundaries are the speed pulse's
    edges, the static CoF is the first peak after each edge (searched up to
    Dyn min %), and the dynamic CoF is the mean over Dyn min..Dyn max %.
    Steps marked noisy (too many zero crossings in one stroke, see
    speed_pulse.step_has_extra_crossings) are left out completely - their
    step_df row numbers are returned in "skipped_steps".
    Returns None if the inputs aren't ready yet.
    """
    if df_display is None or pulse_edges is None or eval_params is None:
        return None
    skipped_steps = []
    if "noisy" in pulse_edges.columns:
        noisy_edges = pulse_edges[pulse_edges["noisy"]]
        for step_index in noisy_edges["step"].unique():
            skipped_steps.append(int(step_index))
        pulse_edges = pulse_edges[~pulse_edges["noisy"]]
    minima = pulse_edges_to_minima(df_display, pulse_edges)
    if len(minima) == 0:
        return None
    cof_res = cof_calc.get_static_and_dynamic_cof(
        df_display, minima,
        float(eval_params["static_range"]),
        float(eval_params["dyn_min"]),
        float(eval_params["dyn_max"]),
        static_mode="first_peak",
    )
    return {
        "minima": minima, "cof_res": cof_res, "static_method": "pulse",
        "skipped_steps": skipped_steps,
    }


NOTE_SKIPPED_NOISY = "Skipped: noisy"
NOTE_NO_CYCLES = "Skipped: no cycles"


def _steps_or_whole_file(df_display, step_df):
    """The test steps, or one synthetic step spanning the whole file when
    there's no step data."""
    if step_df is not None:
        return step_df
    return pd.DataFrame({
        "Startzeit [s]": [df_display["Zeit"].min()],
        "Endzeit [s]":   [df_display["Zeit"].max()],
        "inactive":      [False],
    })


def compute_stats(cof_eval, df_display, step_df):
    """Per-step CoF statistics for the current evaluation. Falls back to a
    single synthetic step spanning the whole file when there's no step data.
    Every active step gets a row, in time order: a step that produced no
    cycles keeps its time range with empty numbers, and its "Note" says why
    it was not used. Raises on conversion/computation error.
    """
    steps = _steps_or_whole_file(df_display, step_df)
    stats = stat_funcs.CoF_Stat(cof_eval["cof_res"], steps)

    skipped_steps = cof_eval.get("skipped_steps", [])

    # CoF_Stat's rows, looked up by their "Time Range" text.
    stats_rows_by_range = {}
    for _, stats_row in stats.iterrows():
        stats_rows_by_range[stats_row["Time Range"]] = stats_row.to_dict()

    rows = []
    for position in range(len(steps)):
        step = steps.iloc[position]
        if step["inactive"]:
            continue
        lower = step["Startzeit [s]"]
        upper = step["Endzeit [s]"]
        # Same text CoF_Stat writes, so the two can be matched.
        time_range = f"{round(lower, 1)}-{round(upper, 1)}"
        if time_range in stats_rows_by_range:
            row = stats_rows_by_range[time_range]
            row["Note"] = ""
        else:
            row = {"Time Range": time_range}
            if position in skipped_steps:
                row["Note"] = NOTE_SKIPPED_NOISY
            else:
                row["Note"] = NOTE_NO_CYCLES
        rows.append(row)

    return pd.DataFrame(rows, columns=list(stats.columns) + ["Note"])


# The largest difference between the recombined CoF AVG and the normal
# per-step mean that still counts as "the same number" (floating-point noise).
CHECK_TOLERANCE = 1e-9

GROUP_ORDER = ["CoF AVG", "CoF+", "CoF-"]


def compute_plus_minus_stats(cof_eval, df_display, step_df, stats):
    """Per-step statistics split into CoF+ and CoF- (positive and negative
    strokes), plus "CoF AVG": the two added back together.

    `stats` is compute_stats' result for the same evaluation, or None. Every
    CoF AVG row is compared with the matching row there (see
    add_check_column).

    Returns one DataFrame with a "Group" column, the rows ordered like the
    workbook: all CoF AVG rows, then all CoF+ rows, then all CoF- rows.
    Raises on conversion/computation error.
    """
    steps = _steps_or_whole_file(df_display, step_df)
    groups = stat_funcs.CoF_Stat_PlusMinus(cof_eval["cof_res"], steps)

    rows = []
    for group_name in GROUP_ORDER:
        for _, group_row in groups[group_name].iterrows():
            row = group_row.to_dict()
            row["Group"] = group_name
            rows.append(row)

    columns = ["Group"] + list(groups["CoF AVG"].columns)
    table = pd.DataFrame(rows, columns=columns)
    return add_check_column(table, stats)


def add_check_column(plus_minus_table, stats):
    """Add the "Check" column: for every CoF AVG row, whether it matches the
    normal per-step row in `stats` (compute_stats' result) - if it does, no
    cycle was lost or counted twice when splitting by direction. Empty for
    the CoF+ / CoF- rows, and everywhere when `stats` is None."""
    # The normal per-step rows, looked up by their time window.
    main_rows_by_range = {}
    if stats is not None:
        for _, main_row in stats.iterrows():
            main_rows_by_range[_range_key(main_row["Time Range"])] = main_row

    checks = []
    for _, row in plus_minus_table.iterrows():
        if stats is not None and row["Group"] == "CoF AVG":
            checks.append(_check_against_main(row, main_rows_by_range))
        else:
            checks.append("")
    table = plus_minus_table.copy()
    table["Check"] = checks
    return table


def _range_key(time_range):
    """The (start, end) numbers of a "start-end" time-range text, so that
    "80-90.0" and "80.0-90.0" (the same window, written once from the file
    and once from the database) are recognised as the same step. None if
    the text can't be read."""
    parts = str(time_range).replace("–", "-").split("-")
    if len(parts) != 2:
        return None
    try:
        return (round(float(parts[0]), 1), round(float(parts[1]), 1))
    except ValueError:
        return None


def _check_against_main(avg_row, main_rows_by_range):
    """Compare one recombined CoF AVG row with the normal per-step row.
    Returns "OK" or a short text saying what differs."""
    key = _range_key(avg_row["Time Range"])
    if key is None or key not in main_rows_by_range:
        return "No matching step"
    main_row = main_rows_by_range[key]

    if pd.isna(main_row["Static N"]) or pd.isna(main_row["Dynamic N"]):
        return "No numbers in the step above"

    problems = []
    if int(avg_row["Static N"]) != int(main_row["Static N"]):
        problems.append(
            "static N " + str(int(avg_row["Static N"])) + " vs " + str(int(main_row["Static N"]))
        )
    if int(avg_row["Dynamic N"]) != int(main_row["Dynamic N"]):
        problems.append(
            "dynamic N " + str(int(avg_row["Dynamic N"])) + " vs " + str(int(main_row["Dynamic N"]))
        )
    static_diff = abs(avg_row["Static Avg"] - main_row["Static Avg"])
    if not static_diff <= CHECK_TOLERANCE:
        problems.append("static mean off by " + format(static_diff, ".3g"))
    dynamic_diff = abs(avg_row["Dynamic Avg"] - main_row["Dynamic Avg"])
    if not dynamic_diff <= CHECK_TOLERANCE:
        problems.append("dynamic mean off by " + format(dynamic_diff, ".3g"))

    if len(problems) == 0:
        return "OK"
    return "Differs: " + ", ".join(problems)
