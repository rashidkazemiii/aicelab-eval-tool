"""
General data utilities.
Corresponds to VBA: Trim_Data.bas
"""
import pandas as pd


def trim_data(df: pd.DataFrame, start_time: float, end_time: float) -> pd.DataFrame:
    """Trim dataset to a specific time range."""
    return df[
        (df["Zeit [s]"] >= start_time) & (df["Zeit [s]"] <= end_time)
    ].reset_index(drop=True)


def trim_step_df(step_df: pd.DataFrame, start_time: float, end_time: float) -> pd.DataFrame:
    """Adapt step table after trimming to a new time range."""
    result = step_df[
        (step_df["Endzeit [s]"] >= start_time) & (step_df["Startzeit [s]"] <= end_time)
    ].copy()
    result["Startzeit [s]"] = result["Startzeit [s]"].clip(lower=start_time)
    result["Endzeit [s]"] = result["Endzeit [s]"].clip(upper=end_time)
    return result.reset_index(drop=True)
