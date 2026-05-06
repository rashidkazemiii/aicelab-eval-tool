from read_files import SRV, SRV_FSA, OFT
import pandas as pd


def load_data(filename: str, data_origin: str) -> tuple[pd.DataFrame, pd.DataFrame | None, dict | None]:
    """
    Load test data from a supported source format.

    Returns:
        df: main measurement data table.
        step_df: step metadata table (or None).
        header: file header metadata (OFT only, else None).
    """
    # df (DataFrame | None): main measurement dataset.
    df: pd.DataFrame | None = None

    # step_df (DataFrame | None): step interval metadata.
    step_df: pd.DataFrame | None = None

    # header (dict | None): optional metadata from OFT file headers.
    header: dict | None = None

    if data_origin == "SRV":
        df, step_df = SRV.readRawFile(filename)
    elif data_origin == "SRV_FSA":
        df, step_df = SRV_FSA.readRawFile(filename)
    elif data_origin == "OFT":
        df, step_df, header = OFT.readRawFile(filename)
    else:
        raise Exception(
            f"File format {data_origin} is not implemented. Filename provided is {filename}"    #The f before the string stands for "formatted string literal" (also called f-string), which is a feature introduced in Python 3.6.
        )                                                                                       #The f tells Python to evaluate expressions inside curly braces {} and insert their values into the string.
    if step_df is None:
        if df is not None and not df.empty:
            step_df = pd.DataFrame(
                {
                    'Step': [0],
                    'Startzeit [s]': [0],
                    'Endtime [s]': [df["time"].max()],
                    'inactive': [False],
                }
            )
        else:
            print("Warning: df is empty, cannot generate step_df.")
    if df is None:
        raise ValueError(f"No data could be loaded from {filename} (origin={data_origin}).")
    if "stroke" in df.columns:
        # stroke (Series[float]): numeric stroke signal for downstream calculations.
        df['stroke'] = df['stroke'].astype(float)
    return df, step_df, header
