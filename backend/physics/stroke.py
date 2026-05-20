"""
All stroke (displacement) domain algorithms.
Corresponds to VBA: Stroke_Phase, Stroke_Shift, Stroke_StepShift,
                    Stroke_Filter, Stroke_StepFilter, Stroke_Minima, Stroke_Evaluate.
"""
import logging
import numpy as np
import pandas as pd
from config import ZERO_CROSSING_DT_THRESHOLD, CYCLE_NOISE_RATIO

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Stroke_Phase
# ---------------------------------------------------------------------------

def stroke_calculate(df, stroke, threshold=1):
    """
    Compute displacement (stroke) from rotational speed.

    Unwraps the phase accumulated from RPM data, then projects it onto
    a cosine wave scaled by the stroke amplitude from the file header.
    """
    df["phase"] = 2 * np.pi * df["rotation speed"] / 60 * df["time"]
    diff = df["phase"].diff()
    mask = (diff < -threshold) | (diff > threshold)
    corrections = diff.where(mask, 0).cumsum()
    df["phase"] -= corrections
    df["stroke"] = 0.5 * stroke * np.cos(df["phase"])
    return df


# ---------------------------------------------------------------------------
# Stroke_Shift / Stroke_StepShift
# ---------------------------------------------------------------------------

def stroke_offset(series: pd.Series, time: pd.Series, step_df=None) -> pd.Series:
    """Mean-center stroke per active step."""
    result = series.copy()
    if step_df is None:
        result -= result.mean()
    else:
        for _, row in step_df.iterrows():
            if not row["inactive"]:
                mask = (time >= row["step_start"]) & (time <= row["step_end"])
                col = result[mask]
                result[mask] = col - col.mean()
    return result


# ---------------------------------------------------------------------------
# Stroke_Filter / Stroke_StepFilter
# ---------------------------------------------------------------------------

def stroke_filter(series: pd.Series, n: int) -> pd.Series:
    """Rolling median filter for stroke signal."""
    return series.rolling(n, center=True, min_periods=1).median()


# ---------------------------------------------------------------------------
# Stroke_Minima
# ---------------------------------------------------------------------------

def stroke_find_minima(df: pd.DataFrame, column: str = "stroke") -> pd.DataFrame:
    """
    Zero-crossing boundary detection for stroke waveform.

    Column parameter allows use with stroke_shifted / stroke_filtered variants.
    Returns a DataFrame with one row per detected cycle containing times and
    values of negative peak, positive peak, and interpolated zero-crossing.
    """
    times  = df["time"].values
    values = df[column].values

    dt         = np.diff(times)
    prev_vals  = values[:-1]
    curr_vals  = values[1:]
    prev_times = times[:-1]
    curr_times = times[1:]

    sign_change = ((prev_vals < 0) & (curr_vals >= 0)) | ((prev_vals >= 0) & (curr_vals < 0))
    mask    = sign_change & (dt < ZERO_CROSSING_DT_THRESHOLD)
    indices = np.where(mask)[0]

    negativeTime  = []
    negativeArray = []
    positiveTime  = []
    positiveArray = []

    for idx in indices:
        pv, cv = prev_vals[idx], curr_vals[idx]
        pt, ct = prev_times[idx], curr_times[idx]
        if pv < 0:
            negativeArray.append(pv); negativeTime.append(pt)
        else:
            positiveArray.append(pv); positiveTime.append(pt)
        if cv < 0:
            negativeArray.append(cv); negativeTime.append(ct)
        else:
            positiveArray.append(cv); positiveTime.append(ct)

    if len(negativeTime) > len(positiveTime):
        negativeTime.pop(); negativeArray.pop()
    elif len(negativeTime) < len(positiveTime):
        positiveTime.pop(); positiveArray.pop()

    theoreticalTime = [
        (positiveTime[i] * negativeArray[i] - negativeTime[i] * positiveArray[i])
        / (negativeArray[i] - positiveArray[i])
        for i in range(len(negativeTime))
    ]

    timeSpan = np.diff(negativeTime)
    if len(timeSpan) == 0:
        logger.warning("No time spans found in zero-crossing detection — check data continuity")
    else:
        avg = timeSpan.mean()
        if np.any((timeSpan < CYCLE_NOISE_RATIO * avg) & (timeSpan != 0)):
            logger.warning("Noisy data detected: cycle spacing < 50%% of average. Apply filter before evaluating.")

    return pd.DataFrame({
        "neg_time":       negativeTime,
        "-Min " + column: negativeArray,
        "pos_time":       positiveTime,
        "+Min " + column: positiveArray,
        "zero_time":      theoreticalTime,
        "Min " + column:  [0] * len(positiveArray),
    })


# ---------------------------------------------------------------------------
# Stroke_Evaluate
# ---------------------------------------------------------------------------

def stroke_evaluate(df, minima, column: str = "stroke"):
    """
    Per-cycle stroke amplitude.

    Returns max (absolute peak) stroke value per half-cycle.
    """
    a = 1.0  # use full cycle for stroke peak

    Time       = df["time"].tolist()
    Stroke     = df[column].tolist()
    negMinTime = minima["neg_time"].tolist()

    startIndex    = []
    maxStroke     = []
    maxStrokeTime = []

    time_to_idx = {t: i for i, t in enumerate(Time)}
    for t in negMinTime:
        startIndex.append(time_to_idx[t] + 1)

    for i in range(1, len(negMinTime)):
        try:
            endIndex        = startIndex[i]
            movingTimeRange = Time[startIndex[i - 1] : endIndex]
            movingRange     = Stroke[startIndex[i - 1] : endIndex]
            if not movingRange:
                continue
            if Stroke[endIndex - 1] > 0:
                maxStroke.append(max(movingRange))
                idx, _ = max(enumerate(movingRange), key=lambda x: x[1])
            else:
                maxStroke.append(min(movingRange))
                idx, _ = min(enumerate(movingRange), key=lambda x: x[1])
            maxStrokeTime.append(movingTimeRange[idx])
        except Exception as e:
            logger.warning("Skipping stroke cycle %d: %s", i, e)
            continue

    return pd.DataFrame({"maxstroke": maxStroke, "maxstrokeTime": maxStrokeTime})
