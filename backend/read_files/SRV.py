import pandas as pd
from typing import Tuple, Optional


def readRawFile(filename: str) -> Tuple[pd.DataFrame, Optional[pd.DataFrame]]:
    data = pd.read_csv(filename, delimiter="\t", decimal=",", encoding="ISO-8859-1")
    data = data.rename(columns={"Friction coeff": "CoF", "Stroke [µm]": "stroke"})
    data["diff"] = data["Zeit [s]"].diff().fillna(0)
    time_greater_than_1 = data[data["diff"] > 1]
    start_time = []
    end_time = []
    inactive = []
    previous_end = 0
    for index, row in time_greater_than_1.iterrows():
        start = data.iloc[index - 1]["Zeit [s]"]
        end = data.iloc[index]["Zeit [s]"]
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
        step_df = pd.DataFrame(
            {"Startzeit [s]": start_time, "Endzeit [s]": end_time, "inactive": inactive}
        )
    return data, step_df

