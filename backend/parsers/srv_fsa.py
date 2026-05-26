import pandas as pd
from typing import Tuple, Optional


def readRawFile(filename: str) -> Tuple[pd.DataFrame, Optional[pd.DataFrame]]:
    data = pd.read_csv(
        filename,
        header=None,
        sep="\t",
        skiprows=1,
        decimal=",",
        names=["time", "stroke", "cof"],
    )
    data["diff"] = data["time"].diff().fillna(0)
    time_greater_than_1 = data[data["diff"] > 1]
    start_time = []
    end_time = []
    inactive = []
    previous_end = 0
    for index, row in time_greater_than_1.iterrows():
        start = data.iloc[index - 1]["time"]
        end = data.iloc[index]["time"]
        if not start - previous_end <= 0:
            end_time.append(start)
            start_time.append(previous_end)
            inactive.append(False)
        end_time.append(end)
        previous_end = end
        start_time.append(start)
        inactive.append(True)
    if len(start_time) == 0:
        step_df = None
    else:
        # The loop only adds an active segment when a gap follows it.
        # The final active segment has no trailing gap, so add it explicitly.
        # Then add a closing marker so step_df["step_start"] is even-length:
        #   [start₁, end₁, start₂, end₂, …, startN, endN]
        # This matches the VBA referenceTime structure expected by
        # CoF_Discontstatistics / CoF_Discontsepstatistics.
        final_end = data["time"].iloc[-1]
        if final_end > previous_end:
            start_time.append(previous_end)
            end_time.append(final_end)
            inactive.append(False)
            # closing marker — zero-duration inactive row that carries endN
            start_time.append(final_end)
            end_time.append(final_end)
            inactive.append(True)
        step_df = pd.DataFrame(
            {"step_start": start_time, "step_end": end_time, "inactive": inactive}
        )
    return data, step_df
