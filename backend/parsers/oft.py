import pandas as pd
import numpy as np
import logging
from physics import stroke

logger = logging.getLogger(__name__)


# Header
def read_header(fread: list[str]) -> dict:
    """
    Read key/value metadata from the OFT file header.

    The parser stops once table-like content begins (e.g. lines containing
    "Startzeit" or "Nummer").
    """
    header_data: dict[str, str] = {}
    stop_markers = ("Startzeit", "Nummer")

    for raw_line in fread:
        line = raw_line.strip()

    for raw_line in fread:
        line = raw_line.strip()

        if any(marker in line for marker in stop_markers):
            break

        if not line:
            continue

        parts = [part.strip() for part in line.split("\t") if part.strip()]
        if len(parts) < 2:
            continue

        key = parts[0]
        value = " ".join(parts[1:])
        header_data[key] = value

    logger.info("Extracted header data: %s", header_data)
    return clean_header_data(header_data)


def clean_header_data(header_data):
    if "Hub Exzenter" in header_data.keys():
        try:
            value = header_data["Hub Exzenter"].split()[0].replace(",", ".")
            header_data["stroke"] = float(value)
            logger.info("Parsed 'Hub Exzenter' value: %s", header_data["stroke"])
        except (ValueError, IndexError) as e:
            logger.warning("Error parsing 'Hub Exzenter': %s", e)
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

    step_df = step_df.replace({",": "."}, regex=True)

    temp_col = "Temperatur [°C]"
    if "Temperatur [Â°C]" in step_df.columns:
        temp_col = "Temperatur [Â°C]"

    target_cols = ["Startzeit [s]", "Drehzahl [U/min]", "Belastung [N]", temp_col]

    try:
        step_df[target_cols] = step_df[target_cols].astype(float)
        step_df = step_df.rename(columns={temp_col: "Temperatur [°C]"})
    except KeyError:
        raise Exception(
            f"Missing expected columns in step data. Available: {list(step_df.columns)}"
        )

    step_df["Endzeit [s]"] = step_df["Startzeit [s]"].shift(-1)
    step_df = step_df[step_df["Endzeit [s]"] != step_df["Startzeit [s]"]]
    step_df["inactive"] = step_df["Drehzahl [U/min]"] == 0

    return step_df


# Main df

def read_main_df(filename, fread):
    """Locates the data table start and reads it into a DataFrame."""
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
    """Cleans column names, handles translations, and converts data types."""
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_", regex=True)

    rename_map = {
        "zeit": "Zeit [s]",
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


def remove_inactive_data(df, step_df):
    if step_df is None:
        return df
    inactive_periods = step_df[step_df["inactive"] == True][["Startzeit [s]", "Endzeit [s]"]]
    for _, row in inactive_periods.iterrows():
        df = df[
            (df["Zeit [s]"] < row["Startzeit [s]"]) | (df["Zeit [s]"] >= row["Endzeit [s]"])
        ]
    return df.reset_index(drop=True)


def readRawFile(filename: str):
    with open(filename, mode="r", encoding="latin-1") as f:
        fread = f.readlines()
    header = read_header(fread)
    step_df = read_step_df(fread)
    df = read_main_df(filename, fread)
    df = stroke.stroke_calculate(df, header["stroke"])
    df = remove_inactive_data(df, step_df)
    if step_df is not None:
        step_df.loc[step_df.index[-1], "Endzeit [s]"] = df["Zeit [s]"].max()
    return df, step_df, header
