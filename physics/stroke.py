import numpy as np
from .utility_functions import Find_minima, Evaluate


def calculate(df, stroke, threshold=1):
    df["phase"] = 2 * np.pi * df["rotation speed"] / 60 * df["time"]
    diff = df["phase"].diff()
    mask = (diff < -threshold) | (diff > threshold)
    corrections = diff.where(mask, 0).cumsum()
    df["phase"] -= corrections
    df["stroke"] = 0.5 * stroke * np.cos(df["phase"])
    return df


def find_minima(df):
    return Find_minima(df, "stroke")


def find_maxima(
    df, stroke_minima, static_cof_range, beginning_dynamic_range, ending_dynamic_range
):
    return Evaluate(
        df,
        stroke_minima,
        "stroke",
        static_cof_range,
        beginning_dynamic_range,
        ending_dynamic_range,
    )
