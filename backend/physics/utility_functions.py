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


def filter_fast(series, n):
    """Centered rolling median over `n` samples (pandas C implementation).
    At the two ends of the series the window simply has fewer samples."""
    return series.rolling(window=n, center=True, min_periods=1).median()


def filter(df, window):
    # df is already trimmed to [first step start, last step end] upstream when steps
    # exist, so filtering the whole received range covers both cases.
    has_stroke = "stroke" in df.columns
    df["CoF"] = filter_fast(df["CoF"], window).round(15).values
    if has_stroke:
        df["stroke"] = filter_fast(df["stroke"], window).round(15).values
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
    negativeTime = []
    negativeArray = []
    positiveTime = []
    positiveArray = []

    # Vectorized over consecutive-sample pairs (was a df.iterrows() loop over
    # every single row - fine for a few thousand rows, but a real friction
    # trace can have hundreds of thousands, where the per-row Python overhead
    # of iterrows() made Evaluate take long enough to feel like the app had
    # frozen). Only the pairs that are actually a zero crossing still need a
    # plain Python loop below (there are far fewer of those than rows).
    values = df[column].to_numpy()
    times = df["Zeit"].to_numpy()
    if len(values) >= 2:
        prevValue = values[:-1]
        currentValue = values[1:]
        prevTime = times[:-1]
        currentTime = times[1:]
        within_gap = (currentTime - prevTime) < ZERO_CROSSING_TIME_GAP_THRESHOLD
        went_negative_to_positive = (prevValue < 0) & (currentValue >= 0)
        went_positive_to_negative = (prevValue >= 0) & (currentValue < 0)
        crossing_idx = np.nonzero(
            within_gap & (went_negative_to_positive | went_positive_to_negative)
        )[0]

        for idx in crossing_idx:
            pv, pt = prevValue[idx], prevTime[idx]
            cv, ct = currentValue[idx], currentTime[idx]
            if pv < 0:
                negativeArray.append(pv)
                negativeTime.append(pt)
            else:
                positiveArray.append(pv)
                positiveTime.append(pt)
            if cv < 0:
                negativeArray.append(cv)
                negativeTime.append(ct)
            else:
                positiveArray.append(cv)
                positiveTime.append(ct)
    if len(negativeTime) > len(positiveTime):
        negativeTime.pop()
        negativeArray.pop()
    elif len(negativeTime) < len(positiveTime):
        positiveTime.pop()
        positiveArray.pop()

    # j = crossing index: one per detected zero-crossing (0, 1, 2, ...).
    theoreticalTime = []
    for j in range(len(negativeTime)):
        theoreticalTime.append(
            (positiveTime[j] * negativeArray[j] - negativeTime[j] * positiveArray[j])
            / (negativeArray[j] - positiveArray[j])
        )

    # check if filtering is necessary

    # pauseTime = pauseTime

    timetocheck = negativeTime
    timeSpan = []
    for j in range(len(timetocheck) - 1):
        timeSpan.append(timetocheck[j + 1] - timetocheck[j])
    if not len(timeSpan) == 0:
        averagetimeSpan = sum(timeSpan) / len(timeSpan)
    else:
        averagetimeSpan = 1
        logger.warning("No time spans found in zero-crossing detection — check data continuity")
    for j in range(len(timeSpan)):
        if timeSpan[j] < 0.5 * averagetimeSpan and timeSpan[j] != 0:
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


# --- first-peak static CoF (used by "Evaluate with pulse") -----------------
# Light smoothing used only to locate the peak (the value is read from raw).
# 3 samples: enough to ignore a single-sample spike, small enough not to
# flatten a real breakaway peak, which at high speed is only a few samples
# wide.
FIRST_PEAK_SMOOTH_SAMPLES = 3
# After locating the peak on the smoothed signal, the exact raw maximum is
# taken within this many samples of it.
FIRST_PEAK_REFINE_SAMPLES = 3
# The search starts this many samples before the crossing, as a safety margin.
FIRST_PEAK_START_MARGIN_SAMPLES = 2


def find_first_peak(Stroke, start_i, dyn_start_i, sign):
    """Index of the FIRST peak of sign * Stroke after a zero crossing.

    All indices are 0-based positions in `Stroke`. `start_i` is the zero
    crossing that starts the cycle, `dyn_start_i` is where the dynamic
    plateau begins (the search stops there), and `sign` is +1 when this
    half-cycle is positive and -1 when it is negative.

    Walking forward on a lightly smoothed copy, the peak is simply the first
    positive sample after which the signal turns down (not lower than the
    sample before it, higher than the one after it). Nothing else - no
    minimum width or height - so it is the first breakaway bump, however
    small, and not a later, bigger one.

    Returns the raw index of the peak, or None when the signal never turns
    down before the dynamic plateau.
    """
    n = len(Stroke)
    lo = start_i - FIRST_PEAK_START_MARGIN_SAMPLES
    if lo < 0:
        lo = 0
    hi = dyn_start_i
    if hi > n:
        hi = n
    if hi - lo < FIRST_PEAK_SMOOTH_SAMPLES:
        return None

    region = np.asarray(Stroke[lo:hi], dtype=float) * sign
    smoothed = (
        pd.Series(region)
        .rolling(window=FIRST_PEAK_SMOOTH_SAMPLES, center=True, min_periods=1)
        .median()
        .to_numpy()
    )

    # The median can give a peak a flat top of equal values; ">=" on the
    # left and ">" on the right lands on the last sample of such a top.
    candidate = -1
    for m in range(1, len(smoothed) - 1):
        if smoothed[m] <= 0:
            continue
        if smoothed[m] >= smoothed[m - 1] and smoothed[m] > smoothed[m + 1]:
            candidate = m
            break

    if candidate < 0:
        return None

    # Read the exact peak from the raw values around the smoothed location.
    r_lo = candidate - FIRST_PEAK_REFINE_SAMPLES
    r_hi = candidate + FIRST_PEAK_REFINE_SAMPLES
    if r_lo < 0:
        r_lo = 0
    if r_hi > len(region) - 1:
        r_hi = len(region) - 1
    best_m = r_lo
    best_v = region[r_lo]
    for m in range(r_lo + 1, r_hi + 1):
        if region[m] > best_v:
            best_v = region[m]
            best_m = m
    return lo + best_m


def Evaluate(
    df, minima, column, static_cof_range, beginning_dynamic_range, ending_dynamic_range,
    static_mode="fixed_window",
):
    """Compute per-cycle static/dynamic CoF statistics between zero crossings.

    For each pair of consecutive negative-going zero crossings in `minima`
    (one full stroke cycle), finds the static CoF and the dynamic CoF (the
    mean of `column` over the [beginning_dynamic_range%,
    ending_dynamic_range%] window of the cycle).

    static_mode decides how the static CoF is found:
      "fixed_window" - the peak/trough of `column` within the first
                       `static_cof_range`% of the cycle (the original rule);
      "first_peak"   - the first peak after the zero crossing, searched up
                       to the start of the dynamic window (find_first_peak);
                       cycles with no such peak fall back to the fixed
                       window.

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
    # Optional: which way each crossing goes (+1 = the CoF goes positive after
    # it, -1 = negative). Present when the crossings are the speed pulse's
    # edges ("Evaluate with pulse"); then the peak is looked for on that
    # side, instead of reading the sign off the signal itself.
    if "direction" in minima.columns:
        crossingDirection = minima["direction"].tolist()
    else:
        crossingDirection = None

    def cycle_sign(crossing_j, endIndex):
        """+1 / -1 for the cycle that starts at crossing crossing_j: the
        crossing's own direction when known, else the sign of the raw CoF at
        the end of the static window. 0 when that value is exactly zero."""
        if crossingDirection is not None:
            if crossingDirection[crossing_j] >= 0:
                return 1
            return -1
        if Stroke[endIndex - 1] > 0:
            return 1
        if Stroke[endIndex - 1] < 0:
            return -1
        return 0

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

    # j = crossing index: startIndex[j] is crossing j's row number in the raw table.
    for j in range(len(negMinTime)):
        startIndex.append(Time.index(negMinTime[j]) + 1)

    def replace_with_first_peak(prevIndex, nextIndex, sign):
        """In "first_peak" mode, swap the static value just appended (found
        with the fixed window) for the first peak after the crossing, if
        there is one. prevIndex/nextIndex are 1-based rows like startIndex;
        find_first_peak wants 0-based ones, hence the -1s. `sign` is the
        cycle's +1 / -1 from cycle_sign()."""
        if static_mode != "first_peak":
            return
        dynStart = prevIndex + _vba_round(b * (nextIndex - prevIndex))
        peak_i = find_first_peak(Stroke, prevIndex - 1, dynStart - 1, sign)
        if peak_i is not None:
            maxStroke[-1] = Stroke[peak_i]
            maxStrokeTime[-1] = Time[peak_i]

    # k = cycle index: cycle k is the stroke between crossing k-1 and crossing k -
    # it reuses j's own numbering rather than counting separately.
    for k in range(1, len(negMinTime)):
        gap_threshold = SRV_TIME_GAP_THRESHOLD
        if Speed is not None:
            drehzahl = Speed[startIndex[k - 1] - 1]
            if drehzahl and drehzahl > 0:
                half_period = 30.0 / drehzahl  # (60 / Drehzahl) / 2
                gap_threshold = max(SRV_TIME_GAP_THRESHOLD, PAUSE_SAFETY_FACTOR * half_period)
        if negMinTime[k] - negMinTime[k - 1] > gap_threshold:
            # gap spans a pause between test steps — disregard this cycle
            continue
        try:
            endIndex = startIndex[k - 1] + _vba_round(
                a * (startIndex[k] - startIndex[k - 1])
            )
            if startIndex[k - 1] == endIndex:
                raise Exception(
                    f"The starting and ending index are the same : {endIndex}. Check that {startIndex[k]} and {startIndex[k - 1]} are not too close. This happend for time = {Time[startIndex[k - 1]]}"
                )
            # Windows are shifted by -3/-2: the VBA macro builds these ranges via
            # Range("AD"&pos&":AD"&pos), i.e. it uses the array position as a literal
            # sheet row number. Since the sheet's data starts at row 3 (rows 1-2 are
            # headers), that address is 2 rows earlier than the position it's meant
            # to reference. Replicated here for parity with the VBA tool.
            movingTimeRange = Time[startIndex[k - 1] - 3 : endIndex - 2]
            movingRange = Stroke[startIndex[k - 1] - 3 : endIndex - 2]
            sign = cycle_sign(k - 1, endIndex)
            if sign > 0:
                maxStroke.append(max(movingRange))
                # Find the position of the biggest value in movingRange. If
                # more than one sample ties for biggest, keep the first one
                # (same rule Python's own max() uses).
                index = 0
                biggest_value = movingRange[0]
                for m in range(1, len(movingRange)):
                    if movingRange[m] > biggest_value:
                        biggest_value = movingRange[m]
                        index = m
            elif sign < 0:
                maxStroke.append(min(movingRange))
                # Same idea, but looking for the smallest value instead.
                index = 0
                smallest_value = movingRange[0]
                for m in range(1, len(movingRange)):
                    if movingRange[m] < smallest_value:
                        smallest_value = movingRange[m]
                        index = m
            else:
                continue
            maxStrokeTime.append(movingTimeRange[index])
            replace_with_first_peak(startIndex[k - 1], startIndex[k], sign)
            startdynamicIndex.append(
                startIndex[k - 1] + _vba_round(b * (startIndex[k] - startIndex[k - 1]))
            )
            enddynamicIndex.append(
                startIndex[k - 1] + _vba_round(c * (startIndex[k] - startIndex[k - 1]))
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
            logger.warning("Skipping cycle %d: %s", k, e)
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
            sign = cycle_sign(len(negMinTime) - 1, endIndex)
            if sign > 0:
                maxStroke.append(max(movingRange))
                index = 0
                biggest_value = movingRange[0]
                for m in range(1, len(movingRange)):
                    if movingRange[m] > biggest_value:
                        biggest_value = movingRange[m]
                        index = m
            elif sign < 0:
                maxStroke.append(min(movingRange))
                index = 0
                smallest_value = movingRange[0]
                for m in range(1, len(movingRange)):
                    if movingRange[m] < smallest_value:
                        smallest_value = movingRange[m]
                        index = m
            else:
                raise Exception("Endpoint value is exactly zero.")
            maxStrokeTime.append(movingTimeRange[index])
            replace_with_first_peak(prevIndex, nextIndex, sign)
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

