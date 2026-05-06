import pandas as pd
import numpy as np
from physics import stroke


# Header
def read_header(fread):
    header_data = {}
    for line in fread:
        line = line.strip()

        # Stop if either Startzeit or Nummer is found

        if "Startzeit" in line or "Nummer" in line:
            break
        if not line:
            continue
        parts = [
            p.strip() 
            for p in line.split("\t") 
            if p.strip()
        ]
        if len(parts) >= 2:
            key = parts[0]
            value = " ".join(parts[1:])
            header_data[key] = value
    print(f"Extracted header data: {header_data}")
    return clean_header_data(header_data)


def clean_header_data(header_data):
    if "Hub Exzenter" in header_data.keys():
        try:
            value=header_data["Hub Exzenter"].split()[0].replace(",", ".")
            header_data["stroke"] = float(value)
            print(f"Parsed 'Hub Exzenter' value: {header_data['stroke']}")
        except(ValueError, IndexError) as e:
            print(f"Error parsing 'Hub Exzenter': {e}")
            header_data["stroke"] = None

    if "Anzahl Stufen" in header_data.keys():
        header_data["Stufe_ja_nein"] = header_data["Anzahl Stufen"] == "Ja"
    return header_data


# Step data


def read_step_df(fread):
    found_start = False
    found_end = False
    start, end = 0, 0
    for i, line in enumerate(fread):
        if "Startzeit" in line and not found_start:
            found_start = True
            start = i
        elif found_start and "Stufe" not in line:
            end = i
            found_end = True
            break
    if not found_start:
        return None
    rows = fread[start:end]
    data = [row.strip().split("\t") for row in rows]
    data[0] = ["Step"] + data[0]
    df = pd.DataFrame(data[1:], columns=data[0])
    return clean_step_df(df)


def clean_step_df(step_df):
    if step_df is None or step_df.empty:
        return None

    # Replace German decimals and convert to float
    step_df = step_df.replace({",": "."}, regex=True)

    # Handle the potential encoding mess for the Temperature column
    temp_col = "Temperatur [°C]"
    if "Temperatur [Â°C]" in step_df.columns:
        temp_col = "Temperatur [Â°C]"

    target_cols = ["Startzeit [s]", "Drehzahl [U/min]", "Belastung [N]", temp_col]

    try:
        step_df[target_cols] = step_df[target_cols].astype(float)
        # Standardize the column name after conversion
        step_df = step_df.rename(columns={temp_col: "Temperatur [°C]"})
    except KeyError as e:
        raise Exception(
            f"Missing expected columns in step data. Available: {list(step_df.columns)}"
        )

    # Logic: Endtime is the Startzeit of the next step
    step_df["Endtime [s]"] = step_df["Startzeit [s]"].shift(-1)

    # Remove rows where start and end time are identical (artifacts)
    step_df = step_df[step_df["Endtime [s]"] != step_df["Startzeit [s]"]]

    # Calculate inactivity (where RPM is 0)
    step_df["inactive"] = step_df["Drehzahl [U/min]"] == 0

    return step_df


# main df


def read_main_df(filename, fread):
    """
    Locates the data table start and reads it into a DataFrame.
    """
    found = False
    skip_rows = 0
    for i, line in enumerate(fread):
        if "Nummer" in line:
            skip_rows = i
            found = True
            break

    if not found:
        raise Exception(f"The main dataframe was not found in the file {filename}")
    df = pd.read_csv(
        filename, sep="\t", skiprows=skip_rows, low_memory=False, decimal=","
    )
    df = df.drop(index=0).reset_index(drop=True)

    return clean_main_df(df)


def clean_main_df(df):
    """
    Cleans column names, handles translations, and converts data types.
    """
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_", regex=True)

    rename_map = {
        "zeit": "time",
        "drehzahl": "rotation speed",
        "belastung": "normal load",
        "rk_oft_links": "friction force left",
        "rk_oft_rechts": "friction force right",
        "reibungskraft": "friction force",
        "verschleiss": "Wear",
        "reibungszahl": "CoF",
        "temperatur": "Temperature",
        "externer_eingang_1": "external temperature",
        "externer_eingang_2": "external displacement",
        "externer_eingang_3": "external pressure",
    }

    to_drop = [
        "nummer",
        "reibungsmoment",
        "rk_sop_links",
        "rk_sop_rechts",
        "belastung_links",
        "belastung_rechts",
    ]
    existing_drops = [c for c in to_drop if c in df.columns]

    df = df.drop(columns=existing_drops)
    df = df.rename(columns=rename_map)

    df = df.replace({",": "."}, regex=True).astype(float)

    return df


# main function


def remove_inactive_data(df, step_df):
    if step_df is None:
        return df
    inactive_periods = step_df[step_df["inactive"] == True][
        ["Startzeit [s]", "Endtime [s]"]
    ]

    for _, row in inactive_periods.iterrows():
        df = df[
            (df["time"] < row["Startzeit [s]"]) | (df["time"] >= row["Endtime [s]"])
        ]

    return df.reset_index(drop=True)


def readRawFile(filename: str):
    with open(filename, mode="r", encoding="latin-1") as f:
        fread = f.readlines()
    header = read_header(fread)
    step_df = read_step_df(fread)
    df = read_main_df(filename, fread)
    df = stroke.calculate(df, header["stroke"])
    df = remove_inactive_data(df, step_df)
    if not step_df is None:
        step_df.loc[step_df.index[-1], "Endtime [s]"] = df["time"].max()
    return df, step_df, header
