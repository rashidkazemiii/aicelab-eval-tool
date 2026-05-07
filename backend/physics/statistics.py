import numpy as np
import pandas as pd


def CoF_Stat(CoF, step_df):
    staticTime = CoF["staticCoFTime"]
    staticCoF = CoF["staticCoF"]

    dynamicStdDev = CoF["dynamicCoFSD"]
    dynamiccount = CoF["dynamicCoFn"]
    dynamicAvgxN = CoF["dynamicCoFsigma"]
    dynamicVar = CoF["dynamicCoFvariance"]

    # referenceTime = step_df["Startzeit [s]"].to_numpy()

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

            lowerLimit = row["Startzeit [s]"]  # referenceTime[i]
            upperLimit = row["Endzeit [s]"]  # referenceTime[i + 1]
            mask = (staticTime >= lowerLimit) & (staticTime <= upperLimit)
            absoluteCoF = np.abs(staticCoF[mask])
            stepdynamicStdDev = dynamicStdDev[mask]
            stepdynamiccount = dynamiccount[mask]
            stepdynamicAvgxN = dynamicAvgxN[mask]
            stepdynamicVar = dynamicVar[mask]

            count = len(absoluteCoF)
            if not count == 0:

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
                    (
                        (
                            tempdynamicVar[-1]
                            - (tempdynamicAvgxN[-1]) ** 2 / tempdynamiccount[-1]
                        )
                        / (tempdynamiccount[-1] - 1)
                    )
                    ** 0.5
                )

    statistics = pd.DataFrame(
        data={
            "Time Range": temptimeRange,
            "Static Avg": tempstaticAvg,
            "Static Std Dev": tempstaticStdDev,
            "Static N": tempcount,
            "Static Avg x N": tempstaticAvgxN,
            "Static Var": tempstaticVar,
            "Dynamic Avg": tempdynamicAvg,
            "Dynamic Std Dev": tempdynamicStdDev,
            "Dynamic N": tempdynamiccount,
            "Dynamic Avg x N": tempdynamicAvgxN,
            "Dynamic Var": tempdynamicVar,
        }
    )
    return statistics


def CoF_Statisticspersecond(CoF, step_df):
    static_time = CoF["staticCoFTime"]
    static_CoF = CoF["staticCoF"]

    dynamic_StdDev = CoF["dynamicCoFSD"]
    dynamic_Count = CoF["dynamicCoFn"]
    dynamic_AvgxN = CoF["dynamicCoFsigma"]
    dynamic_Var = CoF["dynamicCoFvariance"]

    # raw_data = step_df["Startzeit [s]"].to_numpy()
    reference_time = [
        i
        for i in range(
            int(step_df["Startzeit [s]"].to_numpy()[0]),
            int(step_df["Endzeit [s]"].to_numpy()[-1]) + 1,
        )
    ]
    # initial_time = static_time.iloc[0]
    # final_time = static_time.iloc[-1]

    # time_array = np.arange(initial_time, final_time + 1)

    nonempty_row = len(static_time)

    if nonempty_row == 2:
        paste_row = 3
    else:
        paste_row = nonempty_row + 2

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

        absolute_CoF = []
        step_dynamic_std_dev = []
        step_dynamic_count = []
        step_dynamic_avg_x_n = []
        step_dynamic_var = []

        # count = 0
        mask = (static_time >= lower_limit) & (static_time <= upper_limit)

        absolute_CoF = abs(static_CoF[mask])
        step_dynamic_std_dev = dynamic_StdDev[mask]
        step_dynamic_count = dynamic_Count[mask]
        step_dynamic_avg_x_n = dynamic_AvgxN[mask]
        step_dynamic_var = dynamic_Var[mask]
        count = len(step_dynamic_std_dev)
        # print(count,end=" ")
        # count = 0
        # absolute_CoF = []
        # step_dynamic_std_dev = []
        # step_dynamic_count = []
        # step_dynamic_avg_x_n = []
        # step_dynamic_var = []
        # for j in range(len(static_time)):
        #    if lower_limit <= static_time.iloc[j] < upper_limit:
        #        absolute_CoF.append(abs(static_CoF.iloc[j]))
        #        step_dynamic_std_dev.append(dynamic_StdDev.iloc[j])
        #        step_dynamic_count.append(dynamic_Count.iloc[j])
        #        step_dynamic_avg_x_n.append(dynamic_AvgxN.iloc[j])
        #        step_dynamic_var.append(dynamic_Var.iloc[j])
        #        count += 1
        # print(count)
        if not count == 0:
            temp_count.append(count)
            temp_time_range.append(
                str(round(lower_limit, 1)) + "–" + str(round(upper_limit, 1))
            )
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
                (
                    (
                        temp_dynamic_var[-1]
                        - (temp_dynamic_avg_x_n[-1]) ** 2 / temp_dynamic_count[-1]
                    )
                    / (temp_dynamic_count[-1] - 1)
                )
                ** 0.5
            )

    statistics_per_second = pd.DataFrame(
        {
            "Time Range": temp_time_range,
            "Static Avg": temp_static_avg,
            "Static Std Dev": temp_static_std_dev,
            "Count": temp_count,
            "Static Avg * n": temp_static_avg_x_n,
            "Static Var": temp_static_var,
            "Dynamic Avg": temp_dynamic_avg,
            "Dynamic Std Dev": temp_dynamic_std_dev,
            "Dynamic Count": temp_dynamic_count,
            "Dynamic Avg * n": temp_dynamic_avg_x_n,
            "Dynamic Var": temp_dynamic_var,
        }
    )
    return statistics_per_second


def CoF_StatsepContCheck(CoF, step_df, data_origin):
    if data_origin == "SRV_FSA":
        return CoF_Discontsepstatistics(CoF, step_df)
    return CoF_Contsepstatistics(CoF, step_df)


def CoF_Contsepstatistics(CoF, step_df):
    staticTime = CoF["staticCoFTime"].to_numpy()
    staticCoF = CoF["staticCoF"].to_numpy()

    dynamicStdDev = CoF["dynamicCoFSD"].to_numpy()
    dynamiccount = CoF["dynamicCoFn"].to_numpy()
    dynamicAvgxN = CoF["dynamicCoFsigma"].to_numpy()
    dynamicVar = CoF["dynamicCoFvariance"].to_numpy()

    referenceTime = step_df["Startzeit [s]"].to_numpy()
    # Initialize lists to store intermediate results
    temptimeRange = []
    tempstaticAvgL = []
    tempstaticAvgR = []
    tempstaticStdDevL = []
    tempstaticStdDevR = []
    tempcountL = []
    tempcountR = []
    tempstaticAvgxNL = []
    tempstaticAvgxNR = []
    tempstaticVarL = []
    tempstaticVarR = []

    tempdynamicAvgL = []
    tempdynamicAvgR = []
    tempdynamiccountL = []
    tempdynamiccountR = []
    tempdynamicStdDevL = []
    tempdynamicStdDevR = []
    tempdynamicAvgxNL = []
    tempdynamicAvgxNR = []
    tempdynamicVarL = []
    tempdynamicVarR = []

    # Main loop
    n_skipped_rows = 0
    for i in range(len(referenceTime) - 1):
        lowerLimit = referenceTime[i]
        upperLimit = referenceTime[i + 1]

        # Filter staticCoF based on time range
        mask = (staticTime >= lowerLimit) & (staticTime <= upperLimit)
        staticCoF_filtered = staticCoF[mask]
        staticTime_filtered = staticTime[mask]

        # Initialize lists to store filtered values
        absoluteCoFL = []
        absoluteCoFR = []
        stepdynamicStdDevL = []
        stepdynamicStdDevR = []
        stepdynamiccountL = []
        stepdynamiccountR = []
        stepdynamicAvgxNL = []
        stepdynamicAvgxNR = []
        stepdynamicVarL = []
        stepdynamicVarR = []

        countL = 0
        countR = 0

        if not len(staticCoF_filtered) == 0:

            # Iterate over filtered staticCoF
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

            # Calculating intermediate results
            tempcountL.append(countL)
            tempcountR.append(countR)
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
            tempdynamicAvgL.append(
                tempdynamicAvgxNL[i - n_skipped_rows]
                / tempdynamiccountL[i - n_skipped_rows]
            )
            tempdynamicAvgR.append(
                tempdynamicAvgxNR[i - n_skipped_rows]
                / tempdynamiccountR[i - n_skipped_rows]
            )
            tempdynamicStdDevL.append(
                (
                    (
                        tempdynamicVarL[i - n_skipped_rows]
                        - (tempdynamicAvgxNL[i - n_skipped_rows]) ** 2
                        / tempdynamiccountL[i - n_skipped_rows]
                    )
                    / (tempdynamiccountL[i - n_skipped_rows] - 1)
                )
                ** 0.5
            )
            tempdynamicStdDevR.append(
                (
                    (
                        tempdynamicVarR[i - n_skipped_rows]
                        - (tempdynamicAvgxNR[i - n_skipped_rows]) ** 2
                        / tempdynamiccountR[i - n_skipped_rows]
                    )
                    / (tempdynamiccountR[i - n_skipped_rows] - 1)
                )
                ** 0.5
            )
        else:
            n_skipped_rows += 1

    # Convert lists to DataFrame
    statisticssep = pd.DataFrame(
        {
            "Time Range": temptimeRange,
            "Static Avg L": tempstaticAvgL,
            "Static StdDev L": tempstaticStdDevL,
            "Count L": tempcountL,
            "Static AvgxN L": tempstaticAvgxNL,
            "Static Var L": tempstaticVarL,
            "Dynamic Avg L": tempdynamicAvgL,
            "Dynamic StdDev L": tempdynamicStdDevL,
            "Dynamic Count L": tempdynamiccountL,
            "Dynamic AvgxN L": tempdynamicAvgxNL,
            "Dynamic Var L": tempdynamicVarL,
            "Static Avg R": tempstaticAvgR,
            "Static StdDev R": tempstaticStdDevR,
            "Count R": tempcountR,
            "Static AvgxN R": tempstaticAvgxNR,
            "Static Var R": tempstaticVarR,
            "Dynamic Avg R": tempdynamicAvgR,
            "Dynamic StdDev R": tempdynamicStdDevR,
            "Dynamic Count R": tempdynamiccountR,
            "Dynamic AvgxN R": tempdynamicAvgxNR,
            "Dynamic Var R": tempdynamicVarR,
        }
    )
    return statisticssep


def CoF_Discontsepstatistics(CoF, step_df):
    # Extracting data from statistics_CoF DataFrame
    staticTime = CoF["staticCoFTime"].to_numpy()
    staticCoF = CoF["staticCoF"].to_numpy()
    dynamicStdDev = CoF["dynamicCoFSD"].to_numpy()
    dynamiccount = CoF["dynamicCoFn"].to_numpy()
    dynamicAvgxN = CoF["dynamicCoFsigma"].to_numpy()
    dynamicVar = CoF["dynamicCoFvariance"].to_numpy()

    # Extracting reference time from data DataFrame
    referenceTime = step_df["Startzeit [s]"].to_numpy()

    # Find non-empty rows and last row
    # nonemptyrow = len(evalsh["Startzeit [s]"])  # Assuming "Startzeit [s]" is the column containing reference time
    lastrow = len(staticTime)  # Assuming it has the same length as staticCoF

    # Initialize temporary variables
    temptimeRange = []
    tempstaticAvgL = []
    tempstaticAvgR = []
    tempstaticStdDevL = []
    tempstaticStdDevR = []
    tempcountL = []
    tempcountR = []

    tempstaticAvgxNL = []
    tempstaticAvgxNR = []
    tempstaticVarL = []
    tempstaticVarR = []
    tempdynamicAvgL = []
    tempdynamicAvgR = []
    tempdynamiccountL = []
    tempdynamiccountR = []
    tempdynamicStdDevL = []
    tempdynamicStdDevR = []
    tempdynamicAvgxNL = []
    tempdynamicAvgxNR = []
    tempdynamicVarL = []
    tempdynamicVarR = []

    # Loop through reference time
    for i in range(0, len(referenceTime) - 1, 2):
        lowerLimit = referenceTime[i]
        upperLimit = referenceTime[i + 1]

        absoluteCoFL = []
        absoluteCoFR = []
        stepdynamicStdDevL = []
        stepdynamicStdDevR = []
        stepdynamiccountL = []
        stepdynamiccountR = []
        stepdynamicAvgxNL = []
        stepdynamicAvgxNR = []
        stepdynamicVarL = []
        stepdynamicVarR = []

        countL = 0
        countR = 0

        # Loop through static time
        for j in range(len(staticTime)):
            if pd.notnull(staticTime[j]):
                if staticTime[j] >= lowerLimit and staticTime[j] <= upperLimit:
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
        if not (countL + countR == 0):

            tempcountL.append(countL)
            tempcountR.append(countR)
            temptimeRange.append(
                str(round(lowerLimit, 1)) + "–" + str(round(upperLimit, 1))
            )
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
                tempdynamicAvgxNL[-1] / tempdynamiccountL[-1]
                if not tempdynamiccountL[-1] == 0
                else 0
            )
            tempdynamicAvgR.append(
                tempdynamicAvgxNR[-1] / tempdynamiccountR[-1]
                if not tempdynamiccountR[-1] == 0
                else 0
            )
            tempdynamicStdDevL.append(
                (
                    (
                        tempdynamicVarL[-1]
                        - (tempdynamicAvgxNL[-1]) ** 2 / tempdynamiccountL[-1]
                    )
                    / (tempdynamiccountL[-1] - 1)
                )
                ** 0.5
                if not tempdynamiccountL[-1] == 0
                else 0
            )
            tempdynamicStdDevR.append(
                (
                    (
                        tempdynamicVarR[-1]
                        - (tempdynamicAvgxNR[-1]) ** 2 / tempdynamiccountR[-1]
                    )
                    / (tempdynamiccountR[-1] - 1)
                )
                ** 0.5
                if not tempdynamiccountR[-1] == 0
                else 0
            )

    # Create dataframes with the results
    statisticssep = pd.DataFrame(
        {
            "Time Range": temptimeRange,
            "Static Avg (Left)": tempstaticAvgL,
            "Static Std Dev (Left)": tempstaticStdDevL,
            "Static Count (Left)": tempcountL,
            "Static AvgxN (Left)": tempstaticAvgxNL,
            "Static Variance (Left)": tempstaticVarL,
            "Static Avg (Right)": tempstaticAvgR,
            "Static Std Dev (Right)": tempstaticStdDevR,
            "Static Count (Right)": tempcountR,
            "Static AvgxN (Right)": tempstaticAvgxNR,
            "Static Variance (Right)": tempstaticVarR,
            "Dynamic Avg (Left)": tempdynamicAvgL,
            "Dynamic Std Dev (Left)": tempdynamicStdDevL,
            "Dynamic Count (Left)": tempdynamiccountL,
            "Dynamic AvgxN (Left)": tempdynamicAvgxNL,
            "Dynamic Variance (Left)": tempdynamicVarL,
            "Dynamic Avg (Right)": tempdynamicAvgR,
            "Dynamic Std Dev (Right)": tempdynamicStdDevR,
            "Dynamic Count (Right)": tempdynamiccountR,
            "Dynamic AvgxN (Right)": tempdynamicAvgxNR,
            "Dynamic Variance (Right)": tempdynamicVarR,
        }
    )
    return statisticssep

