import numpy as np


def calculate(df, stroke, threshold=1):
    """
    Compute displacement (stroke) from rotational speed.

    Unwraps the phase accumulated from RPM data, then projects it onto
    a cosine wave scaled by the stroke amplitude from the file header.
    """
    df["phase"] = 2 * np.pi * df["rotation speed"] / 60 * df["Zeit [s]"]
    diff = df["phase"].diff()
    mask = (diff < -threshold) | (diff > threshold)
    corrections = diff.where(mask, 0).cumsum()
    df["phase"] -= corrections
    df["stroke"] = 0.5 * stroke * np.cos(df["phase"])
    return df
