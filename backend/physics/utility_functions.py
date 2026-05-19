import pandas as pd
import numpy as np


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


def filter(df, step_df, window):
    if step_df is None:
        df["CoF"] = df["CoF"].rolling(window).median()
        df["stroke"] = df["stroke"].rolling(window).median()
    else:
        for index, row in step_df.iterrows():
            if not row["inactive"]:
                filtered_rows = df[
                    (df["Zeit [s]"] < row["Endzeit [s]"])
                    & (df["Zeit [s]"] > row["Startzeit [s]"])
                ]
                cof_column = filtered_rows["CoF"]
                df.loc[filtered_rows.index, "CoF"] = cof_column.rolling(
                    window, center=True, min_periods=1
                ).median()
                stroke_column = filtered_rows["stroke"]
                df.loc[filtered_rows.index, "stroke"] = stroke_column.rolling(
                    window, min_periods=1
                ).median()
    return df


def trim(df, trim_start, trim_end):
    return df[(df["Zeit [s]"] < trim_end) & (df["Zeit [s]"] > trim_start)]


def Find_minima(df, column):
    firstIteration = True
    negativeTime = []
    negativeArray = []
    positiveTime = []
    positiveArray = []

    for index, row in df.iterrows():
        if firstIteration:
            prevValue = row[column]
            prevTime = row["Zeit [s]"]
            firstIteration = False
        else:
            currentValue = row[column]
            currentTime = row["Zeit [s]"]
            if currentTime - prevTime < 0.002:
                if (prevValue < 0 and currentValue >= 0) or (
                    prevValue >= 0 and currentValue < 0
                ):
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
        # if timeSpan[i] > pauseTime:
        #    timeSpan[i] = 0
    if not len(timeSpan) == 0:
        averagetimeSpan = sum(timeSpan) / len(timeSpan)
    else:
        averagetimeSpan = 1
        print("timeSpan has a len of 0 - ask Fevsi what to do with it")
    for i in range(len(timeSpan)):
        if timeSpan[i] < 0.5 * averagetimeSpan and timeSpan[i] != 0:
            print("The data is too noisy! Please apply the filter and try again.")

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

    for i in range(len(negMinTime)):
        startIndex.append(Time.index(negMinTime[i]) + 1)

    for i in range(1, len(negMinTime)):
        # if negMinTime[i] - negMinTime[i - 1] > self.pauseTime:
        #    continue
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
            dynamicCoFTime.append(
                startdynamicTime[-1] + (enddynamicTime[-1] + startdynamicTime[-1]) / 2
            )
            dynamicCoF.append(sum(movingdynamicRange) / len(movingdynamicRange))
            dynamicCoFSD.append(np.std((movingdynamicRange)))
            dynamicCoFn.append(len((movingdynamicRange)))
            dynamicCoFsigma.append(abs(dynamicCoF[-1]) * dynamicCoFn[-1])
            dynamicCoFvariance.append(
                (dynamicCoFSD[-1] ** 2)
                * ((dynamicCoFn[-1] - 1 + dynamicCoFsigma[-1] ** 2) / dynamicCoFn[-1])
            )
        except Exception as e:
            print(e)
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

