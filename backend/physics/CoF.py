"""
All CoF domain algorithms.
Corresponds to VBA: CoF_Calculate, CoF_Shift, CoF_StepShift, CoF_Filter,
                    CoF_StepFilter, CoF_Minima, CoF_Evaluate,
                    and all CoF statistics modules.
"""
import warnings
import logging
import numpy as np
import pandas as pd
from config import ZERO_CROSSING_DT_THRESHOLD, CYCLE_NOISE_RATIO

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# CoF_Calculate
# ---------------------------------------------------------------------------

def cof_calculate(df, normal_load_correction_factor):
    """Compute CoF from friction force and normal load."""
    if normal_load_correction_factor is None:
        df["CoF"] = (df["friction force left"] + df["friction force right"]) / df["normal load"]
    elif normal_load_correction_factor == 0:
        warnings.warn("CoF is not the real CoF. Careful with units.")
        df["CoF"] = df["friction force left"] + df["friction force right"]
    else:
        def _corrected(row):
            NL = max(0, row["normal load"] - normal_load_correction_factor)
            return (row["friction force left"] + row["friction force right"]) / NL
        df["CoF"] = df.apply(_corrected, axis=1)
    return df


# ---------------------------------------------------------------------------
# CoF_Shift / CoF_StepShift
# ---------------------------------------------------------------------------

def cof_offset(df, step_df=None):
    """Mean-center CoF per active step (CoF column only)."""
    if step_df is None:
        df["CoF"] = df["CoF"] - df["CoF"].mean()
    else:
        for _, row in step_df.iterrows():
            if not row["inactive"]:
                mask = (df["Zeit [s]"] > row["Startzeit [s]"]) & (df["Zeit [s]"] < row["Endzeit [s]"])
                col = df.loc[mask, "CoF"]
                df.loc[mask, "CoF"] = col - col.mean()
    return df


# ---------------------------------------------------------------------------
# CoF_Filter / CoF_StepFilter
# ---------------------------------------------------------------------------

def cof_filter(series: pd.Series, n: int) -> pd.Series:
    """Rolling median filter for CoF signal."""
    return series.rolling(n, center=True, min_periods=1).median()


# ---------------------------------------------------------------------------
# CoF_Minima
# ---------------------------------------------------------------------------

def cof_find_minima(df: pd.DataFrame, column: str = "CoF") -> pd.DataFrame:
    """
    Zero-crossing boundary detection for CoF waveform.

    Column parameter allows use with CoF_shifted / CoF_Filtered variants.
    Returns a DataFrame with one row per detected cycle containing times and
    values of negative peak, positive peak, and interpolated zero-crossing.
    """
    times  = df["Zeit [s]"].values
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
        "-Min Zeit":      negativeTime,
        "-Min " + column: negativeArray,
        "+Min Zeit":      positiveTime,
        "+Min " + column: positiveArray,
        "Min Zeit":       theoreticalTime,
        "Min " + column:  [0] * len(positiveArray),
    })


# ---------------------------------------------------------------------------
# CoF_Evaluate
# ---------------------------------------------------------------------------

def cof_evaluate(df, minima, static_cof_range, beginning_dynamic_range, ending_dynamic_range):
    """
    Per-cycle static and dynamic CoF statistics.

    For each cycle (between consecutive zero-crossings):
    - Static CoF: peak value in the first static_cof_range% of the cycle
    - Dynamic CoF: mean/SD/count in the middle band (beginning% to ending%)
    """
    a = 0.01 * static_cof_range
    b = 0.01 * beginning_dynamic_range
    c = 0.01 * ending_dynamic_range

    Time       = df["Zeit [s]"].tolist()
    Stroke     = df["CoF"].tolist()
    negMinTime = minima["-Min Zeit"].tolist()

    startIndex         = []
    maxStrokeIndex     = []
    maxStroke          = []
    maxStrokeTime      = []
    startdynamicIndex  = []
    enddynamicIndex    = []
    startdynamicTime   = []
    enddynamicTime     = []
    startdynamicCoF    = []
    enddynamicCoF      = []
    dynamicCoFTime     = []
    dynamicCoF         = []
    dynamicCoFSD       = []
    dynamicCoFn        = []
    dynamicCoFsigma    = []
    dynamicCoFvariance = []

    time_to_idx = {t: i for i, t in enumerate(Time)}
    for t in negMinTime:
        startIndex.append(time_to_idx[t] + 1)

    for i in range(1, len(negMinTime)):
        try:
            endIndex = startIndex[i - 1] + round(a * (startIndex[i] - startIndex[i - 1]))
            if startIndex[i - 1] == endIndex:
                raise Exception(
                    f"Start and end index are equal ({endIndex}). "
                    f"Indices {startIndex[i]} and {startIndex[i-1]} may be too close "
                    f"(t = {Time[startIndex[i-1]]})."
                )
            movingTimeRange = Time[startIndex[i - 1] : endIndex]
            movingRange     = Stroke[startIndex[i - 1] : endIndex]
            if Stroke[endIndex - 1] > 0:
                maxStroke.append(max(movingRange))
                index, element = max(enumerate(movingRange), key=lambda x: x[1])
            elif Stroke[endIndex - 1] < 0:
                maxStroke.append(min(movingRange))
                index, element = min(enumerate(movingRange), key=lambda x: x[1])
            else:
                continue
            maxStrokeTime.append(movingTimeRange[index])
            startdynamicIndex.append(startIndex[i - 1] + round(b * (startIndex[i] - startIndex[i - 1])))
            enddynamicIndex.append(  startIndex[i - 1] + round(c * (startIndex[i] - startIndex[i - 1])))
            startdynamicTime.append(Time[startdynamicIndex[-1]])
            enddynamicTime.append(  Time[enddynamicIndex[-1]])
            startdynamicCoF.append( Stroke[startdynamicIndex[-1]])
            enddynamicCoF.append(   Stroke[enddynamicIndex[-1]])

            movingdynamicRange = Stroke[startdynamicIndex[-1] : enddynamicIndex[-1]]
            dynamicCoFTime.append((startdynamicTime[-1] + enddynamicTime[-1]) / 2)
            dynamicCoF.append(sum(movingdynamicRange) / len(movingdynamicRange))
            dynamicCoFSD.append(np.std(movingdynamicRange))
            dynamicCoFn.append(len(movingdynamicRange))
            dynamicCoFsigma.append(abs(dynamicCoF[-1]) * dynamicCoFn[-1])
            dynamicCoFvariance.append(
                dynamicCoFSD[-1] ** 2 * (dynamicCoFn[-1] - 1)
                + dynamicCoFsigma[-1] ** 2 / dynamicCoFn[-1]
            )
        except Exception as e:
            logger.warning("Skipping cycle %d: %s", i, e)
            continue

    return pd.DataFrame({
        "startdynamicTime":   startdynamicTime,
        "startdynamicCoF":    startdynamicCoF,
        "enddynamicTime":     enddynamicTime,
        "enddynamicCoF":      enddynamicCoF,
        "dynamicCoFTime":     dynamicCoFTime,
        "dynamicCoF":         dynamicCoF,
        "dynamicCoFSD":       dynamicCoFSD,
        "dynamicCoFn":        dynamicCoFn,
        "dynamicCoFsigma":    dynamicCoFsigma,
        "dynamicCoFvariance": dynamicCoFvariance,
        "staticCoF":          maxStroke,
        "staticCoFTime":      maxStrokeTime,
    })


# ---------------------------------------------------------------------------
# CoF statistics modules (merged from statistics.py)
# ---------------------------------------------------------------------------

def CoF_Stat(CoF, step_df):
    staticTime    = CoF["staticCoFTime"]
    staticCoF     = CoF["staticCoF"]
    dynamicStdDev = CoF["dynamicCoFSD"]
    dynamiccount  = CoF["dynamicCoFn"]
    dynamicAvgxN  = CoF["dynamicCoFsigma"]
    dynamicVar    = CoF["dynamicCoFvariance"]

    temptimeRange = []
    tempstaticAvg = []
    tempstaticStdDev = []
    tempcount = []
    tempstaticAvgxN = []
    tempstaticVar = []
    tempdynamicAvg = []
    tempdynamiccount = []
    tempdynamicStdDev = []
    tempdynamicAvgxN = []
    tempdynamicVar = []

    for i, row in step_df.iterrows():
        if not row["inactive"]:
            lowerLimit = row["Startzeit [s]"]
            upperLimit = row["Endzeit [s]"]
            mask = (staticTime >= lowerLimit) & (staticTime <= upperLimit)
            absoluteCoF       = np.abs(staticCoF[mask])
            stepdynamicStdDev = dynamicStdDev[mask]
            stepdynamiccount  = dynamiccount[mask]
            stepdynamicAvgxN  = dynamicAvgxN[mask]
            stepdynamicVar    = dynamicVar[mask]

            count = len(absoluteCoF)
            if count != 0:
                tempcount.append(count)
                temptimeRange.append(f"{round(lowerLimit, 1)}–{round(upperLimit, 1)}")
                tempstaticAvg.append(np.mean(absoluteCoF))
                tempstaticStdDev.append(np.std(absoluteCoF))
                tempstaticAvgxN.append(tempstaticAvg[-1] * count)
                tempstaticVar.append(
                    (tempstaticStdDev[-1]) ** 2 * (count - 1)
                    + (tempstaticAvgxN[-1]) ** 2 / count
                )
                tempdynamiccount.append(np.sum(stepdynamiccount))
                tempdynamicAvgxN.append(np.sum(stepdynamicAvgxN))
                tempdynamicVar.append(np.sum(stepdynamicVar))
                tempdynamicAvg.append(tempdynamicAvgxN[-1] / tempdynamiccount[-1])
                tempdynamicStdDev.append(
                    ((tempdynamicVar[-1] - (tempdynamicAvgxN[-1]) ** 2 / tempdynamiccount[-1])
                     / (tempdynamiccount[-1] - 1)) ** 0.5
                )

    return pd.DataFrame({
        "Time Range":      temptimeRange,
        "Static Avg":      tempstaticAvg,
        "Static Std Dev":  tempstaticStdDev,
        "Static N":        tempcount,
        "Static Avg x N":  tempstaticAvgxN,
        "Static Var":      tempstaticVar,
        "Dynamic Avg":     tempdynamicAvg,
        "Dynamic Std Dev": tempdynamicStdDev,
        "Dynamic N":       tempdynamiccount,
        "Dynamic Avg x N": tempdynamicAvgxN,
        "Dynamic Var":     tempdynamicVar,
    })


def CoF_Statisticspersecond(CoF, step_df):
    static_time    = CoF["staticCoFTime"]
    static_CoF     = CoF["staticCoF"]
    dynamic_StdDev = CoF["dynamicCoFSD"]
    dynamic_Count  = CoF["dynamicCoFn"]
    dynamic_AvgxN  = CoF["dynamicCoFsigma"]
    dynamic_Var    = CoF["dynamicCoFvariance"]

    reference_time = [
        i for i in range(
            int(step_df["Startzeit [s]"].to_numpy()[0]),
            int(step_df["Endzeit [s]"].to_numpy()[-1]) + 1,
        )
    ]

    temp_time_range = []
    temp_static_avg = []
    temp_static_std_dev = []
    temp_count = []
    temp_static_avg_x_n = []
    temp_static_var = []
    temp_dynamic_avg = []
    temp_dynamic_count = []
    temp_dynamic_std_dev = []
    temp_dynamic_avg_x_n = []
    temp_dynamic_var = []

    for i in range(len(reference_time) - 1):
        lower_limit = reference_time[i]
        upper_limit = reference_time[i + 1]
        mask = (static_time >= lower_limit) & (static_time <= upper_limit)

        absolute_CoF         = abs(static_CoF[mask])
        step_dynamic_std_dev = dynamic_StdDev[mask]
        step_dynamic_count   = dynamic_Count[mask]
        step_dynamic_avg_x_n = dynamic_AvgxN[mask]
        step_dynamic_var     = dynamic_Var[mask]
        count = len(step_dynamic_std_dev)

        if count != 0:
            temp_count.append(count)
            temp_time_range.append(str(round(lower_limit, 1)) + "–" + str(round(upper_limit, 1)))
            temp_static_avg.append(np.mean(absolute_CoF))
            temp_static_std_dev.append(np.std(absolute_CoF))
            temp_static_avg_x_n.append(temp_static_avg[-1] * count)
            temp_static_var.append(
                (temp_static_std_dev[-1]) ** 2 * (count - 1)
                + (temp_static_avg_x_n[-1]) ** 2 / count
            )
            temp_dynamic_count.append(np.sum(step_dynamic_count))
            temp_dynamic_avg_x_n.append(np.sum(step_dynamic_avg_x_n))
            temp_dynamic_var.append(np.sum(step_dynamic_var))
            temp_dynamic_avg.append(temp_dynamic_avg_x_n[-1] / temp_dynamic_count[-1])
            temp_dynamic_std_dev.append(
                ((temp_dynamic_var[-1] - (temp_dynamic_avg_x_n[-1]) ** 2 / temp_dynamic_count[-1])
                 / (temp_dynamic_count[-1] - 1)) ** 0.5
            )

    return pd.DataFrame({
        "Time Range":      temp_time_range,
        "Static Avg":      temp_static_avg,
        "Static Std Dev":  temp_static_std_dev,
        "Count":           temp_count,
        "Static Avg * n":  temp_static_avg_x_n,
        "Static Var":      temp_static_var,
        "Dynamic Avg":     temp_dynamic_avg,
        "Dynamic Std Dev": temp_dynamic_std_dev,
        "Dynamic Count":   temp_dynamic_count,
        "Dynamic Avg * n": temp_dynamic_avg_x_n,
        "Dynamic Var":     temp_dynamic_var,
    })


def CoF_StatsepContCheck(CoF, step_df, data_origin):
    if data_origin == "SRV_FSA":
        return CoF_Discontsepstatistics(CoF, step_df)
    return CoF_Contsepstatistics(CoF, step_df)


def CoF_Contsepstatistics(CoF, step_df):
    staticTime    = CoF["staticCoFTime"].to_numpy()
    staticCoF     = CoF["staticCoF"].to_numpy()
    dynamicStdDev = CoF["dynamicCoFSD"].to_numpy()
    dynamiccount  = CoF["dynamicCoFn"].to_numpy()
    dynamicAvgxN  = CoF["dynamicCoFsigma"].to_numpy()
    dynamicVar    = CoF["dynamicCoFvariance"].to_numpy()
    referenceTime = step_df["Startzeit [s]"].to_numpy()

    temptimeRange = []
    tempstaticAvgL = []; tempstaticAvgR = []
    tempstaticStdDevL = []; tempstaticStdDevR = []
    tempcountL = []; tempcountR = []
    tempstaticAvgxNL = []; tempstaticAvgxNR = []
    tempstaticVarL = []; tempstaticVarR = []
    tempdynamicAvgL = []; tempdynamicAvgR = []
    tempdynamiccountL = []; tempdynamiccountR = []
    tempdynamicStdDevL = []; tempdynamicStdDevR = []
    tempdynamicAvgxNL = []; tempdynamicAvgxNR = []
    tempdynamicVarL = []; tempdynamicVarR = []

    n_skipped_rows = 0
    for i in range(len(referenceTime) - 1):
        lowerLimit = referenceTime[i]
        upperLimit = referenceTime[i + 1]
        mask = (staticTime >= lowerLimit) & (staticTime <= upperLimit)
        staticCoF_filtered = staticCoF[mask]

        absoluteCoFL = []; absoluteCoFR = []
        stepdynamicStdDevL = []; stepdynamicStdDevR = []
        stepdynamiccountL = []; stepdynamiccountR = []
        stepdynamicAvgxNL = []; stepdynamicAvgxNR = []
        stepdynamicVarL = []; stepdynamicVarR = []
        countL = 0; countR = 0

        if len(staticCoF_filtered) != 0:
            for j in range(len(staticCoF_filtered)):
                if staticCoF_filtered[j] < 0:
                    absoluteCoFL.append(abs(staticCoF_filtered[j]))
                    stepdynamicStdDevL.append(dynamicStdDev[j])
                    stepdynamiccountL.append(dynamiccount[j])
                    stepdynamicAvgxNL.append(dynamicAvgxN[j])
                    stepdynamicVarL.append(dynamicVar[j])
                    countL += 1
                else:
                    absoluteCoFR.append(staticCoF_filtered[j])
                    stepdynamicStdDevR.append(dynamicStdDev[j])
                    stepdynamiccountR.append(dynamiccount[j])
                    stepdynamicAvgxNR.append(dynamicAvgxN[j])
                    stepdynamicVarR.append(dynamicVar[j])
                    countR += 1

            tempcountL.append(countL); tempcountR.append(countR)
            temptimeRange.append(f"{round(lowerLimit, 1)}–{round(upperLimit, 1)}")
            tempstaticAvgL.append(np.mean(absoluteCoFL))
            tempstaticAvgR.append(np.mean(absoluteCoFR))
            tempstaticStdDevL.append(np.std(absoluteCoFL))
            tempstaticStdDevR.append(np.std(absoluteCoFR))
            tempstaticAvgxNL.append(np.mean(absoluteCoFL) * countL)
            tempstaticAvgxNR.append(np.mean(absoluteCoFR) * countR)
            tempstaticVarL.append(
                (np.std(absoluteCoFL) ** 2) * (countL - 1)
                + (np.mean(absoluteCoFL) * countL) ** 2 / countL
            )
            tempstaticVarR.append(
                (np.std(absoluteCoFR) ** 2) * (countR - 1)
                + (np.mean(absoluteCoFR) * countR) ** 2 / countR
            )
            tempdynamiccountL.append(np.sum(stepdynamiccountL))
            tempdynamiccountR.append(np.sum(stepdynamiccountR))
            tempdynamicAvgxNL.append(np.sum(stepdynamicAvgxNL))
            tempdynamicAvgxNR.append(np.sum(stepdynamicAvgxNR))
            tempdynamicVarL.append(np.sum(stepdynamicVarL))
            tempdynamicVarR.append(np.sum(stepdynamicVarR))
            k = i - n_skipped_rows
            tempdynamicAvgL.append(tempdynamicAvgxNL[k] / tempdynamiccountL[k])
            tempdynamicAvgR.append(tempdynamicAvgxNR[k] / tempdynamiccountR[k])
            tempdynamicStdDevL.append(
                ((tempdynamicVarL[k] - (tempdynamicAvgxNL[k]) ** 2 / tempdynamiccountL[k])
                 / (tempdynamiccountL[k] - 1)) ** 0.5
            )
            tempdynamicStdDevR.append(
                ((tempdynamicVarR[k] - (tempdynamicAvgxNR[k]) ** 2 / tempdynamiccountR[k])
                 / (tempdynamiccountR[k] - 1)) ** 0.5
            )
        else:
            n_skipped_rows += 1

    return pd.DataFrame({
        "Time Range":       temptimeRange,
        "Static Avg L":     tempstaticAvgL,
        "Static StdDev L":  tempstaticStdDevL,
        "Count L":          tempcountL,
        "Static AvgxN L":   tempstaticAvgxNL,
        "Static Var L":     tempstaticVarL,
        "Dynamic Avg L":    tempdynamicAvgL,
        "Dynamic StdDev L": tempdynamicStdDevL,
        "Dynamic Count L":  tempdynamiccountL,
        "Dynamic AvgxN L":  tempdynamicAvgxNL,
        "Dynamic Var L":    tempdynamicVarL,
        "Static Avg R":     tempstaticAvgR,
        "Static StdDev R":  tempstaticStdDevR,
        "Count R":          tempcountR,
        "Static AvgxN R":   tempstaticAvgxNR,
        "Static Var R":     tempstaticVarR,
        "Dynamic Avg R":    tempdynamicAvgR,
        "Dynamic StdDev R": tempdynamicStdDevR,
        "Dynamic Count R":  tempdynamiccountR,
        "Dynamic AvgxN R":  tempdynamicAvgxNR,
        "Dynamic Var R":    tempdynamicVarR,
    })


def CoF_Discontsepstatistics(CoF, step_df):
    staticTime    = CoF["staticCoFTime"].to_numpy()
    staticCoF     = CoF["staticCoF"].to_numpy()
    dynamicStdDev = CoF["dynamicCoFSD"].to_numpy()
    dynamiccount  = CoF["dynamicCoFn"].to_numpy()
    dynamicAvgxN  = CoF["dynamicCoFsigma"].to_numpy()
    dynamicVar    = CoF["dynamicCoFvariance"].to_numpy()
    referenceTime = step_df["Startzeit [s]"].to_numpy()

    temptimeRange = []
    tempstaticAvgL = []; tempstaticAvgR = []
    tempstaticStdDevL = []; tempstaticStdDevR = []
    tempcountL = []; tempcountR = []
    tempstaticAvgxNL = []; tempstaticAvgxNR = []
    tempstaticVarL = []; tempstaticVarR = []
    tempdynamicAvgL = []; tempdynamicAvgR = []
    tempdynamiccountL = []; tempdynamiccountR = []
    tempdynamicStdDevL = []; tempdynamicStdDevR = []
    tempdynamicAvgxNL = []; tempdynamicAvgxNR = []
    tempdynamicVarL = []; tempdynamicVarR = []

    for i in range(0, len(referenceTime) - 1, 2):
        lowerLimit = referenceTime[i]
        upperLimit = referenceTime[i + 1]

        absoluteCoFL = []; absoluteCoFR = []
        stepdynamicStdDevL = []; stepdynamicStdDevR = []
        stepdynamiccountL = []; stepdynamiccountR = []
        stepdynamicAvgxNL = []; stepdynamicAvgxNR = []
        stepdynamicVarL = []; stepdynamicVarR = []
        countL = 0; countR = 0

        for j in range(len(staticTime)):
            if pd.notnull(staticTime[j]) and lowerLimit <= staticTime[j] <= upperLimit:
                if staticCoF[j] < 0:
                    absoluteCoFL.append(abs(staticCoF[j]))
                    stepdynamicStdDevL.append(dynamicStdDev[j])
                    stepdynamiccountL.append(dynamiccount[j])
                    stepdynamicAvgxNL.append(dynamicAvgxN[j])
                    stepdynamicVarL.append(dynamicVar[j])
                    countL += 1
                else:
                    absoluteCoFR.append(staticCoF[j])
                    stepdynamicStdDevR.append(dynamicStdDev[j])
                    stepdynamiccountR.append(dynamiccount[j])
                    stepdynamicAvgxNR.append(dynamicAvgxN[j])
                    stepdynamicVarR.append(dynamicVar[j])
                    countR += 1

        if countL + countR != 0:
            tempcountL.append(countL); tempcountR.append(countR)
            temptimeRange.append(str(round(lowerLimit, 1)) + "–" + str(round(upperLimit, 1)))
            tempstaticAvgL.append(np.mean(absoluteCoFL))
            tempstaticAvgR.append(np.mean(absoluteCoFR))
            tempstaticStdDevL.append(np.std(absoluteCoFL))
            tempstaticStdDevR.append(np.std(absoluteCoFR))
            tempstaticAvgxNL.append(tempstaticAvgL[-1] * countL)
            tempstaticAvgxNR.append(tempstaticAvgR[-1] * countR)
            tempstaticVarL.append(
                (tempstaticStdDevL[-1]) ** 2 * (countL - 1)
                + (tempstaticAvgxNL[-1]) ** 2 / countL
            )
            tempstaticVarR.append(
                (tempstaticStdDevR[-1]) ** 2 * (countR - 1)
                + (tempstaticAvgxNR[-1]) ** 2 / countR
            )
            tempdynamiccountL.append(sum(stepdynamiccountL))
            tempdynamiccountR.append(sum(stepdynamiccountR))
            tempdynamicAvgxNL.append(sum(stepdynamicAvgxNL))
            tempdynamicAvgxNR.append(sum(stepdynamicAvgxNR))
            tempdynamicVarL.append(sum(stepdynamicVarL))
            tempdynamicVarR.append(sum(stepdynamicVarR))
            tempdynamicAvgL.append(
                tempdynamicAvgxNL[-1] / tempdynamiccountL[-1] if tempdynamiccountL[-1] != 0 else 0
            )
            tempdynamicAvgR.append(
                tempdynamicAvgxNR[-1] / tempdynamiccountR[-1] if tempdynamiccountR[-1] != 0 else 0
            )
            tempdynamicStdDevL.append(
                ((tempdynamicVarL[-1] - (tempdynamicAvgxNL[-1]) ** 2 / tempdynamiccountL[-1])
                 / (tempdynamiccountL[-1] - 1)) ** 0.5
                if tempdynamiccountL[-1] != 0 else 0
            )
            tempdynamicStdDevR.append(
                ((tempdynamicVarR[-1] - (tempdynamicAvgxNR[-1]) ** 2 / tempdynamiccountR[-1])
                 / (tempdynamiccountR[-1] - 1)) ** 0.5
                if tempdynamiccountR[-1] != 0 else 0
            )

    return pd.DataFrame({
        "Time Range":              temptimeRange,
        "Static Avg (Left)":       tempstaticAvgL,
        "Static Std Dev (Left)":   tempstaticStdDevL,
        "Static Count (Left)":     tempcountL,
        "Static AvgxN (Left)":     tempstaticAvgxNL,
        "Static Variance (Left)":  tempstaticVarL,
        "Static Avg (Right)":      tempstaticAvgR,
        "Static Std Dev (Right)":  tempstaticStdDevR,
        "Static Count (Right)":    tempcountR,
        "Static AvgxN (Right)":    tempstaticAvgxNR,
        "Static Variance (Right)": tempstaticVarR,
        "Dynamic Avg (Left)":      tempdynamicAvgL,
        "Dynamic Std Dev (Left)":  tempdynamicStdDevL,
        "Dynamic Count (Left)":    tempdynamiccountL,
        "Dynamic AvgxN (Left)":    tempdynamicAvgxNL,
        "Dynamic Variance (Left)": tempdynamicVarL,
        "Dynamic Avg (Right)":     tempdynamicAvgR,
        "Dynamic Std Dev (Right)": tempdynamicStdDevR,
        "Dynamic Count (Right)":   tempdynamiccountR,
        "Dynamic AvgxN (Right)":   tempdynamicAvgxNR,
        "Dynamic Variance (Right)":tempdynamicVarR,
    })
