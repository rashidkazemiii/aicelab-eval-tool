import warnings

import numpy as np
import pandas as pd

from .utility_functions import Find_minima, Evaluate


def calculate(df: pd.DataFrame, normal_load_correction_factor: float | None) -> pd.DataFrame:
    """Add a "CoF" column to `df` from its "RK OFT Links"/"RK OFT Rechts"/"Belastung" columns.

    With no correction factor, CoF = (Links + Rechts) / Belastung. With
    factor == 0, CoF is left as the uncorrected friction force sum (not a
    true, unitless CoF). Otherwise, CoF = (Links + Rechts) / (Belastung - factor),
    unclamped — a row where Belastung < factor yields a sign-flipped CoF (the
    correction overshot the actual load for that sample), and a row where
    Belastung == factor yields NaN rather than a silent division by zero.
    """
    if normal_load_correction_factor is None:
        df["CoF"] = (df["RK OFT Links"] + df["RK OFT Rechts"]) / df[
            "Belastung"
        ]
    elif normal_load_correction_factor == 0:
        warnings.warn("CoF is not the real CoF. Careful with units.")
        df["CoF"] = df["RK OFT Links"] + df["RK OFT Rechts"]
    else:

        def calculate_cof_ith_corrected_nl(row):
            NL = row["Belastung"] - normal_load_correction_factor
            if NL == 0:
                return np.nan
            return (row["RK OFT Links"] + row["RK OFT Rechts"]) / NL

        df["CoF"] = df.apply(calculate_cof_ith_corrected_nl, axis=1)
    return df


def find_minima(df: pd.DataFrame) -> pd.DataFrame:
    """Find zero crossings of `df["CoF"]`. See utility_functions.Find_minima."""
    return Find_minima(df, "CoF")


def get_static_and_dynamic_cof(
    df: pd.DataFrame,
    CoF_minima: pd.DataFrame,
    static_cof_range: float,
    beginning_dynamic_range: float,
    ending_dynamic_range: float,
) -> pd.DataFrame:
    """Per-cycle static/dynamic CoF statistics. See utility_functions.Evaluate."""
    return Evaluate(
        df,
        CoF_minima,
        "CoF",
        static_cof_range,
        beginning_dynamic_range,
        ending_dynamic_range,
    )
