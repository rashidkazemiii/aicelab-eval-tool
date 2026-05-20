import logging
import pandas as pd
from read_files import SRV, SRV_FSA, OFT

logger = logging.getLogger(__name__)


def load_data(filename: str, data_origin: str) -> tuple[pd.DataFrame, pd.DataFrame | None, dict | None]:
    """
    Load test data from a supported source format.

    Returns:
        df:      Main measurement data table.
        step_df: Step metadata table (or None).
        header:  File header metadata (OFT only, else None).
    """
    df:      pd.DataFrame | None = None
    step_df: pd.DataFrame | None = None
    header:  dict | None         = None

    if data_origin == "SRV":
        df, step_df = SRV.readRawFile(filename)
    elif data_origin == "SRV_FSA":
        df, step_df = SRV_FSA.readRawFile(filename)
    elif data_origin == "OFT":
        df, step_df, header = OFT.readRawFile(filename)
    else:
        raise ValueError(f"File format '{data_origin}' is not supported. Filename: {filename}")

    if step_df is None:
        if df is not None and not df.empty:
            step_df = pd.DataFrame({
                'Step':           [0],
                'Startzeit [s]':  [0],
                'Endzeit [s]':    [df["Zeit [s]"].max()],
                'inactive':       [False],
            })
        else:
            logger.warning("Loaded DataFrame is empty — step_df could not be generated.")

    if df is None:
        raise ValueError(f"No data could be loaded from '{filename}' (format: {data_origin}).")

    if "stroke" in df.columns:
        df["stroke"] = df["stroke"].astype(float)

    return df, step_df, header
