import logging
import math
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

SRV_TIME_GAP_THRESHOLD = 1.0  # seconds; gap larger than this marks a new test step/pause
ZERO_CROSSING_TIME_GAP_THRESHOLD = 0.002  # seconds; samples farther apart than this aren't treated as a zero crossing
# Safety margin over a step's own expected half-stroke period (60 / Drehzahl / 2)
# before treating a gap between crossings as a pause, for a step slow enough that
# SRV_TIME_GAP_THRESHOLD alone would mistake every real stroke for one.
PAUSE_SAFETY_FACTOR = 1.5


def _vba_round(x):
    """Round half up, matching VBA's WorksheetFunction.Round (Python's round() is banker's rounding)."""
    return math.floor(x + 0.5)


def assign_step_speed(df, step_df):
    """Map each step's Drehzahl (rotational speed, U/min) onto the raw
    samples that fall inside that step's time window. Lets Find_minima/
    Evaluate look up the expected stroke period for whichever step a
    zero-crossing falls in, instead of assuming one speed for the whole
    file. `step_df` must have "Drehzahl" - the caller checks for that.
    """
    df = df.copy()
    df["Drehzahl"] = np.nan
    for _, row in step_df.iterrows():
        mask = (df["Zeit"] >= row["Startzeit [s]"]) & (df["Zeit"] <= row["Endzeit [s]"])
        df.loc[mask, "Drehzahl"] = row["Drehzahl"]
    return df


def offset(df):
    # df is already trimmed to [first step start, last step end] upstream when steps
    # exist, so a single global mean over the received range covers both cases.
    has_stroke = "stroke" in df.columns
    df["CoF"] = (df["CoF"] - df["CoF"].mean()).round(15)
    if has_stroke:
        df["stroke"] = (df["stroke"] - df["stroke"].mean()).round(15)
    return df


def filter_vb_style(series, n):
    """Centered rolling median matching the VB CoFFilter macro exactly.
    Edge handling: window grows 1,3,5,...,n-2 at start and shrinks symmetrically at end."""
    N = len(series)
    half_n = n / 2.0
    result = series.copy().astype(float)

    for i in range(1, N + 1):  # 1-indexed like VB
        if i <= half_n:
            start = 0
            end = 2 * i - 2
        elif i > N - half_n:
            start = 2 * i - N - 1
            end = N - 1
        else:
            start = round(i - half_n) - 1
            end = round(i + half_n) - 1

        start = max(0, start)
        end = min(N - 1, end)
        result.iloc[i - 1] = series.iloc[start:end + 1].median()

    return result


def filter_fast(series, n):
    """Vectorized centered rolling median (pandas C implementation).
    Not bit-exact with the VBA macro's edge-window growth/shrink, but same
    result in the interior and orders of magnitude faster on large series."""
    return series.rolling(window=n, center=True, min_periods=1).median()


def filter(df, window, method="vba"):
    # df is already trimmed to [first step start, last step end] upstream when steps
    # exist, so filtering the whole received range covers both cases.
    if method == "vba":
        filter_fn = filter_vb_style
    elif method == "fast":
        filter_fn = filter_fast
    else:
        raise ValueError(f"Unknown filter method: {method!r}. Expected one of ['vba', 'fast']")
    has_stroke = "stroke" in df.columns
    df["CoF"] = filter_fn(df["CoF"], window).round(15).values
    if has_stroke:
        df["stroke"] = filter_fn(df["stroke"], window).round(15).values
    return df


def trim(df, trim_start, trim_end):
    return df[(df["Zeit"] <= trim_end) & (df["Zeit"] >= trim_start)]


def Find_minima(df, column):
    """Find zero crossings of `column` over `df["Zeit"]`.

    Walks consecutive samples and records every sign change (negative-to-positive
    or positive-to-negative) that occurs within ZERO_CROSSING_TIME_GAP_THRESHOLD
    seconds of each other, then linearly interpolates the crossing time between
    each pair. Returns a DataFrame with the raw pre/post-crossing samples
    ("-Min"/"+Min" columns) and the interpolated crossing ("Min") columns.
    """
    firstIteration = True
    negativeTime = []
    negativeArray = []
    positiveTime = []
    positiveArray = []

    for index, row in df.iterrows():
        if firstIteration:
            prevValue = row[column]
            prevTime = row["Zeit"]
            firstIteration = False
        else:
            currentValue = row[column]
            currentTime = row["Zeit"]
            if currentTime - prevTime < ZERO_CROSSING_TIME_GAP_THRESHOLD:
                went_negative_to_positive = prevValue < 0 and currentValue >= 0
                went_positive_to_negative = prevValue >= 0 and currentValue < 0
                if went_negative_to_positive or went_positive_to_negative:
                    if prevValue < 0:
                        negativeArray.append(prevValue)
                        negativeTime.append(prevTime)
                    else:
                        positiveArray.append(prevValue)
                        positiveTime.append(prevTime)
                    if currentValue < 0:
                        negativeArray.append(currentValue)
                        negativeTime.append(currentTime)
                    else:
                        positiveArray.append(currentValue)
                        positiveTime.append(currentTime)
            prevValue = currentValue
            prevTime = currentTime
    if len(negativeTime) > len(positiveTime):
        negativeTime.pop()
        negativeArray.pop()
    elif len(negativeTime) < len(positiveTime):
        positiveTime.pop()
        positiveArray.pop()

    theoreticalTime = []
    for i in range(len(negativeTime)):
        theoreticalTime.append(
            (positiveTime[i] * negativeArray[i] - negativeTime[i] * positiveArray[i])
            / (negativeArray[i] - positiveArray[i])
        )

    # check if filtering is necessary

    # pauseTime = pauseTime

    timetocheck = negativeTime
    timeSpan = []
    for i in range(len(timetocheck) - 1):
        timeSpan.append(timetocheck[i + 1] - timetocheck[i])
    if not len(timeSpan) == 0:
        averagetimeSpan = sum(timeSpan) / len(timeSpan)
    else:
        averagetimeSpan = 1
        logger.warning("No time spans found in zero-crossing detection — check data continuity")
    for i in range(len(timeSpan)):
        if timeSpan[i] < 0.5 * averagetimeSpan and timeSpan[i] != 0:
            logger.warning("Noisy data detected: cycle spacing < 50%% of average. Apply filter before evaluating.")

    res = pd.DataFrame(
        {
            "-Min Zeit": negativeTime,
            "-Min " + column: negativeArray,
            "+Min Zeit": positiveTime,
            "+Min " + column: positiveArray,
            "Min Zeit": theoreticalTime,
            "Min " + column: [0] * len(positiveArray),
        }
    )
    return res


def Evaluate(
    df, minima, column, static_cof_range, beginning_dynamic_range, ending_dynamic_range
):
    """Compute per-cycle static/dynamic CoF statistics between zero crossings.

    For each pair of consecutive negative-going zero crossings in `minima`
    (one full stroke cycle), finds the static CoF (the peak/trough of
    `column` within the first `static_cof_range`% of the cycle) and the
    dynamic CoF (the mean of `column` over the
    [beginning_dynamic_range%, ending_dynamic_range%] window of the cycle).
    Cycles whose start index equals its rounded end index, or that fail for
    any other reason, are skipped (logged as a warning, not raised) — this
    mirrors the reference VBA tool's behavior of silently disregarding
    single-sample or otherwise degenerate cycles.
    """
    a = 0.01 * static_cof_range
    b = 0.01 * beginning_dynamic_range
    c = 0.01 * ending_dynamic_range

    Time = df["Zeit"].tolist()
    Stroke = df[column].tolist()
    Speed = df["Drehzahl"].tolist() if "Drehzahl" in df.columns else None
    negMinTime = minima["-Min Zeit"].tolist()

    startIndex = []
    maxStrokeIndex = []
    maxStroke = []
    maxStrokeTime = []
    startdynamicIndex = []
    enddynamicIndex = []
    startdynamicTime = []
    enddynamicTime = []
    startdynamicCoF = []
    enddynamicCoF = []

    dynamicCoFTime = []
    dynamicCoF = []
    dynamicCoFSD = []
    dynamicCoFn = []
    dynamicCoFsigma = []
    dynamicCoFvariance = []

    for i in range(len(negMinTime)):
        startIndex.append(Time.index(negMinTime[i]) + 1)

    for i in range(1, len(negMinTime)):
        gap_threshold = SRV_TIME_GAP_THRESHOLD
        if Speed is not None:
            drehzahl = Speed[startIndex[i - 1] - 1]
            if drehzahl and drehzahl > 0:
                half_period = 30.0 / drehzahl  # (60 / Drehzahl) / 2
                gap_threshold = max(SRV_TIME_GAP_THRESHOLD, PAUSE_SAFETY_FACTOR * half_period)
        if negMinTime[i] - negMinTime[i - 1] > gap_threshold:
            # gap spans a pause between test steps — disregard this cycle
            continue
        try:
            endIndex = startIndex[i - 1] + _vba_round(
                a * (startIndex[i] - startIndex[i - 1])
            )
            if startIndex[i - 1] == endIndex:
                raise Exception(
                    f"The starting and ending index are the same : {endIndex}. Check that {startIndex[i]} and {startIndex[i - 1]} are not too close. This happend for time = {Time[startIndex[i - 1]]}"
                )
            # Windows are shifted by -3/-2: the VBA macro builds these ranges via
            # Range("AD"&pos&":AD"&pos), i.e. it uses the array position as a literal
            # sheet row number. Since the sheet's data starts at row 3 (rows 1-2 are
            # headers), that address is 2 rows earlier than the position it's meant
            # to reference. Replicated here for parity with the VBA tool.
            movingTimeRange = Time[startIndex[i - 1] - 3 : endIndex - 2]
            movingRange = Stroke[startIndex[i - 1] - 3 : endIndex - 2]
            if Stroke[endIndex - 1] > 0:
                maxStroke.append(max(movingRange))
                # Find the position of the biggest value in movingRange. If
                # more than one sample ties for biggest, keep the first one
                # (same rule Python's own max() uses).
                index = 0
                biggest_value = movingRange[0]
                for j in range(1, len(movingRange)):
                    if movingRange[j] > biggest_value:
                        biggest_value = movingRange[j]
                        index = j
            elif Stroke[endIndex - 1] < 0:
                maxStroke.append(min(movingRange))
                # Same idea, but looking for the smallest value instead.
                index = 0
                smallest_value = movingRange[0]
                for j in range(1, len(movingRange)):
                    if movingRange[j] < smallest_value:
                        smallest_value = movingRange[j]
                        index = j
            else:
                continue
            maxStrokeTime.append(movingTimeRange[index])
            startdynamicIndex.append(
                startIndex[i - 1] + _vba_round(b * (startIndex[i] - startIndex[i - 1]))
            )
            enddynamicIndex.append(
                startIndex[i - 1] + _vba_round(c * (startIndex[i] - startIndex[i - 1]))
            )
            startdynamicTime.append(Time[startdynamicIndex[-1] - 1])
            enddynamicTime.append(Time[enddynamicIndex[-1] - 1])
            startdynamicCoF.append(Stroke[startdynamicIndex[-1] - 1])
            enddynamicCoF.append(Stroke[enddynamicIndex[-1] - 1])

            movingdynamicRange = Stroke[startdynamicIndex[-1] - 3 : enddynamicIndex[-1] - 2]
            dynamicCoFTime.append((startdynamicTime[-1] + enddynamicTime[-1]) / 2)
            dynamicCoF.append(sum(movingdynamicRange) / len(movingdynamicRange))
            dynamicCoFSD.append(np.std(movingdynamicRange, ddof=1))
            dynamicCoFn.append(len((movingdynamicRange)))
            dynamicCoFsigma.append(abs(dynamicCoF[-1]) * dynamicCoFn[-1])
            dynamicCoFvariance.append(
                dynamicCoFSD[-1] ** 2 * (dynamicCoFn[-1] - 1)
                + dynamicCoFsigma[-1] ** 2 / dynamicCoFn[-1]
            )
        except Exception as e:
            logger.warning("Skipping cycle %d: %s", i, e)
            continue

    # The recording almost always stops mid-stroke, so the last detected
    # crossing has no following crossing to pair with - the loop above can
    # only evaluate a cycle once it has both endpoints, so that trailing
    # stroke (and whatever step it falls in, if it has no other complete
    # strokes) would otherwise be silently dropped. Close it against the
    # last recorded sample instead, using the same math as one loop
    # iteration above but with the end of the data standing in for the
    # missing closing crossing.
    if len(negMinTime) >= 1:
        try:
            prevIndex = startIndex[-1]
            nextIndex = len(Time)
            endIndex = prevIndex + _vba_round(a * (nextIndex - prevIndex))
            if prevIndex == endIndex:
                raise Exception(
                    f"The starting and ending index are the same : {endIndex}."
                )
            movingTimeRange = Time[prevIndex - 3 : endIndex - 2]
            movingRange = Stroke[prevIndex - 3 : endIndex - 2]
            if Stroke[endIndex - 1] > 0:
                maxStroke.append(max(movingRange))
                index = 0
                biggest_value = movingRange[0]
                for j in range(1, len(movingRange)):
                    if movingRange[j] > biggest_value:
                        biggest_value = movingRange[j]
                        index = j
            elif Stroke[endIndex - 1] < 0:
                maxStroke.append(min(movingRange))
                index = 0
                smallest_value = movingRange[0]
                for j in range(1, len(movingRange)):
                    if movingRange[j] < smallest_value:
                        smallest_value = movingRange[j]
                        index = j
            else:
                raise Exception("Endpoint value is exactly zero.")
            maxStrokeTime.append(movingTimeRange[index])
            startdynamicIndex.append(prevIndex + _vba_round(b * (nextIndex - prevIndex)))
            enddynamicIndex.append(prevIndex + _vba_round(c * (nextIndex - prevIndex)))
            startdynamicTime.append(Time[startdynamicIndex[-1] - 1])
            enddynamicTime.append(Time[enddynamicIndex[-1] - 1])
            startdynamicCoF.append(Stroke[startdynamicIndex[-1] - 1])
            enddynamicCoF.append(Stroke[enddynamicIndex[-1] - 1])

            movingdynamicRange = Stroke[startdynamicIndex[-1] - 3 : enddynamicIndex[-1] - 2]
            dynamicCoFTime.append((startdynamicTime[-1] + enddynamicTime[-1]) / 2)
            dynamicCoF.append(sum(movingdynamicRange) / len(movingdynamicRange))
            dynamicCoFSD.append(np.std(movingdynamicRange, ddof=1))
            dynamicCoFn.append(len((movingdynamicRange)))
            dynamicCoFsigma.append(abs(dynamicCoF[-1]) * dynamicCoFn[-1])
            dynamicCoFvariance.append(
                dynamicCoFSD[-1] ** 2 * (dynamicCoFn[-1] - 1)
                + dynamicCoFsigma[-1] ** 2 / dynamicCoFn[-1]
            )
        except Exception as e:
            logger.warning("Skipping trailing stroke: %s", e)

    if column == "CoF":
        res_df = pd.DataFrame(
            data={
                "startdynamicTime": startdynamicTime,
                "startdynamicCoF": startdynamicCoF,
                "enddynamicTime": enddynamicTime,
                "enddynamicCoF": enddynamicCoF,
                "dynamicCoFTime": dynamicCoFTime,
                "dynamicCoF": dynamicCoF,
                "dynamicCoFSD": dynamicCoFSD,
                "dynamicCoFn": dynamicCoFn,
                "dynamicCoFsigma": dynamicCoFsigma,
                "dynamicCoFvariance": dynamicCoFvariance,
                "staticCoF": maxStroke,
                "staticCoFTime": maxStrokeTime,
            }
        )
    elif column == "stroke":
        res_df = pd.DataFrame(
            data={"maxstroke": maxStroke, "maxstrokeTime": maxStrokeTime}
        )
    else:
        raise Exception(column + " not implemented")

    return res_df

