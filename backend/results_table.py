"""Builds the two tables shown under the chart on the Results page.

Kept as two separate tables, not one: the raw table has one row per raw
sample (100,000+ on a real test file), while the evaluation columns have one
row per cycle/step/zero-crossing (usually a few hundred at most). An earlier
version padded the evaluation columns out to the raw table's row count so
everything could share one DataFrame - which meant a table that was over 99%
empty padding, large enough on a real file to trip marimo's output-size
limit. Padding the evaluation columns only up to each other's row count
keeps the same columns without that bloat.
"""

import pandas as pd

import table_helpers

# Column-specific rounding precision below has no known rationale beyond
# matching the reference VBA tool's output column-by-column; preserved
# as-is rather than unified to a single value.
DEFAULT_COF_DECIMALS = 15
MINUS_MIN_COF_DECIMALS = 16
PLUS_MIN_COF_DECIMALS = 18


def build_raw_table(df_display, df_proc, filter_active):
    """Per-sample table: Time, CoF, and (once Filter has run) Filtered CoF.
    `df_display` must not be None - the caller shows its own placeholder for
    that case.
    """
    cols = {
        "Time [s]": list(df_display["Zeit"]),
        "CoF":      list(df_display["CoF"].round(DEFAULT_COF_DECIMALS)),
    }
    if filter_active:
        cols["Filtered CoF"] = list(df_proc["CoF"].round(DEFAULT_COF_DECIMALS))
    return pd.DataFrame(cols)


def build_eval_table(cof_eval, stats_result, stats_error):
    """Per-cycle/per-step evaluation table, or None before Evaluate has run."""
    if cof_eval is None:
        return None

    if stats_error is not None:
        return pd.DataFrame({"Eval error": [stats_error]})

    try:
        stats = stats_result
        cr = cof_eval["cof_res"]
        mn = cof_eval["minima"]
        n = max(len(cr), len(mn), len(stats))

        def pad_column(arr):
            return table_helpers.pad(arr, n)

        def round_and_pad_column(arr, decimals=DEFAULT_COF_DECIMALS):
            return table_helpers.round_and_pad(arr, n, decimals)

        cols = {
            "Static CoF time [s]": pad_column(cr["staticCoFTime"]),
            "Static CoF": round_and_pad_column(cr["staticCoF"]),
            "Dynamic CoF time [s]": pad_column(cr["dynamicCoFTime"]),
            "Dynamic CoF": round_and_pad_column(cr["dynamicCoF"]),
            "Dynamic std dev": round_and_pad_column(cr["dynamicCoFSD"]),
            "Dynamic N": pad_column(cr["dynamicCoFn"]),
            "Dynamic CoF sum": round_and_pad_column(cr["dynamicCoFsigma"]),
            "Dynamic CoF variance": round_and_pad_column(cr["dynamicCoFvariance"]),
            "Time range [s]": pad_column(stats["Time Range"]),
            "Static mean CoF": round_and_pad_column(stats["Static Avg"]),
            "Static std dev": round_and_pad_column(stats["Static Std Dev"]),
            "Static N": pad_column(stats["Static N"]),
            "Static CoF sum": round_and_pad_column(stats["Static Avg x N"]),
            "Static CoF variance": round_and_pad_column(stats["Static Var"]),
            "Dynamic mean CoF": round_and_pad_column(stats["Dynamic Avg"]),
            "Dynamic mean std dev": round_and_pad_column(stats["Dynamic Std Dev"]),
            "Dynamic mean N": pad_column(stats["Dynamic N"]),
            "Dynamic CoF avg×N": round_and_pad_column(stats["Dynamic Avg x N"]),
            "Dynamic CoF var (step)": round_and_pad_column(stats["Dynamic Var"]),
            "-Min time [s]": pad_column(mn["-Min Zeit"]),
            "-Min CoF": round_and_pad_column(mn["-Min CoF"], MINUS_MIN_COF_DECIMALS),
            "+Min time [s]": pad_column(mn["+Min Zeit"]),
            "+Min CoF": round_and_pad_column(mn["+Min CoF"], PLUS_MIN_COF_DECIMALS),
            "Min time [s]": pad_column(mn["Min Zeit"]),
            "CoF minima": round_and_pad_column(mn["Min CoF"]),
            "Dynamic start time [s]": pad_column(cr["startdynamicTime"]),
            "Dynamic start CoF": round_and_pad_column(cr["startdynamicCoF"]),
            "Dynamic end time [s]": pad_column(cr["enddynamicTime"]),
            "Dynamic end CoF": round_and_pad_column(cr["enddynamicCoF"]),
        }
        return pd.DataFrame(cols)
    except Exception as e:
        return pd.DataFrame({"Eval error": [str(e)]})
