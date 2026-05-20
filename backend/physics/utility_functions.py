import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def offset(df, step_df=None):
    if step_df is None:
        df["CoF"] = df["CoF"] - df["CoF"].mean()
        df["stroke"] = df["stroke"] - df["stroke"].mean()
    else:
        for index, row in step_df.iterrows():
            if not row["inactive"]:
                # Filter rows based on conditions
                filtered_rows = df[
                    (df["Zeit [s]"] < row["Endzeit [s]"])
                    & (df["Zeit [s]"] > row["Startzeit [s]"])
                ]
                # Select "CoF" column from filtered rows
                cof_column = filtered_rows["CoF"]
                # Subtract the mean of "CoF" column from values in "CoF" column
                cof_column_adjusted = cof_column - cof_column.mean()
                # Assign adjusted values back to the original DataFrame
                df.loc[filtered_rows.index, "CoF"] = cof_column_adjusted
                # do the same with stroke
                stroke_column = filtered_rows["stroke"]
                stroke_column_adjusted = stroke_column - stroke_column.mean()
                df.loc[filtered_rows.index, "stroke"] = stroke_column_adjusted
    return df


def filter(df, step_df, window):
    if step_df is None:
        df["CoF"] = df["CoF"].rolling(window).median()
        df["stroke"] = df["stroke"].rolling(window).median()
    else:
        for index, row in step_df.iterrows():
            if not row["inactive"]:
                # Filter rows based on conditions
                filtered_rows = df[
                    (df["Zeit [s]"] < row["Endzeit [s]"])
                    & (df["Zeit [s]"] > row["Startzeit [s]"])
                ]
                # Select "CoF" column from filtered rows
                cof_column = filtered_rows["CoF"]
                # Assign adjusted values back to the original DataFrame
                df.loc[filtered_rows.index, "CoF"] = cof_column.rolling(
                    window, center=True, min_periods=1
                ).median()
                stroke_column = filtered_rows["stroke"]
                df.loc[filtered_rows.index, "stroke"] = stroke_column.rolling(
                    window, min_periods=1
                ).median()
    return df


def filter_vb_style(series, n):
    return series.rolling(n, center=True, min_periods=1).median()


def trim(df, trim_start, trim_end):
    return df[(df["Zeit [s]"] < trim_end) & (df["Zeit [s]"] > trim_start)]


def Find_minima(df, column):
    times  = df["Zeit [s]"].values
    values = df[column].values

    dt         = np.diff(times)
    prev_vals  = values[:-1]
    curr_vals  = values[1:]
    prev_times = times[:-1]
    curr_times = times[1:]

    sign_change = ((prev_vals < 0) & (curr_vals >= 0)) | ((prev_vals >= 0) & (curr_vals < 0))
    mask = sign_change & (dt < 0.002)
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
        if np.any((timeSpan < 0.5 * avg) & (timeSpan != 0)):
            logger.warning("Noisy data detected: cycle spacing < 50%% of average. Apply filter before evaluating.")

    return pd.DataFrame({
        "-Min Zeit":       negativeTime,
        "-Min " + column:  negativeArray,
        "+Min Zeit":       positiveTime,
        "+Min " + column:  positiveArray,
        "Min Zeit":        theoreticalTime,
        "Min " + column:   [0] * len(positiveArray),
    })


def Evaluate(
    df, minima, column, static_cof_range, beginning_dynamic_range, ending_dynamic_range
):
    a = 0.01 * static_cof_range
    b = 0.01 * beginning_dynamic_range
    c = 0.01 * ending_dynamic_range

    Time = df["Zeit [s]"].tolist()
    Stroke = df[column].tolist()
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

    time_to_idx = {t: i for i, t in enumerate(Time)}
    for t in negMinTime:
        startIndex.append(time_to_idx[t] + 1)

    for i in range(1, len(negMinTime)):
        try:
            endIndex = startIndex[i - 1] + round(
                a * (startIndex[i] - startIndex[i - 1])
            )
            if startIndex[i - 1] == endIndex:
                raise Exception(
                    f"The starting and ending index are the same : {endIndex}. Check that {startIndex[i]} and {startIndex[i - 1]} are not too close. This happend for time = {Time[startIndex[i - 1]]}"
                )
            movingTimeRange = Time[startIndex[i - 1] : endIndex]
            movingRange = Stroke[startIndex[i - 1] : endIndex]
            if Stroke[endIndex - 1] > 0:
                maxStroke.append(max(movingRange))
                index, element = max(enumerate(movingRange), key=lambda x: x[1])
            elif Stroke[endIndex - 1] < 0:
                maxStroke.append(min(movingRange))
                index, element = min(enumerate(movingRange), key=lambda x: x[1])
            else:
                continue
            maxStrokeTime.append(movingTimeRange[index])
            startdynamicIndex.append(
                startIndex[i - 1] + round(b * (startIndex[i] - startIndex[i - 1]))
            )
            enddynamicIndex.append(
                startIndex[i - 1] + round(c * (startIndex[i] - startIndex[i - 1]))
            )
            startdynamicTime.append(Time[startdynamicIndex[-1]])
            enddynamicTime.append(Time[enddynamicIndex[-1]])
            startdynamicCoF.append(Stroke[startdynamicIndex[-1]])
            enddynamicCoF.append(Stroke[enddynamicIndex[-1]])

            movingdynamicRange = Stroke[startdynamicIndex[-1] : enddynamicIndex[-1]]
            dynamicCoFTime.append((startdynamicTime[-1] + enddynamicTime[-1]) / 2)
            dynamicCoF.append(sum(movingdynamicRange) / len(movingdynamicRange))
            dynamicCoFSD.append(np.std((movingdynamicRange)))
            dynamicCoFn.append(len((movingdynamicRange)))
            dynamicCoFsigma.append(abs(dynamicCoF[-1]) * dynamicCoFn[-1])
            dynamicCoFvariance.append(
                dynamicCoFSD[-1] ** 2 * (dynamicCoFn[-1] - 1)
                + dynamicCoFsigma[-1] ** 2 / dynamicCoFn[-1]
            )
        except Exception as e:
            logger.warning("Skipping cycle %d: %s", i, e)
            continue

    ###
    if column == "CoF":
        lists_to_check = [
            startdynamicTime,
            startdynamicCoF,
            enddynamicTime,
            dynamicCoF,
            maxStroke,
        ]
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

