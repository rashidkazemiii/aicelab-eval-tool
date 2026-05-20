"""
General data utilities.
Corresponds to VBA: Trim_Data.bas
"""
import pandas as pd


def trim_data(df: pd.DataFrame, start_time: float, end_time: float) -> pd.DataFrame:
    """Trim dataset to a specific time range."""
    return df[
        (df["time"] >= start_time) & (df["time"] <= end_time)
    ].reset_index(drop=True)


def trim_step_df(step_df: pd.DataFrame, start_time: float, end_time: float) -> pd.DataFrame:
    """Adapt step table after trimming to a new time range."""
    result = step_df[
        (step_df["step_end"] >= start_time) & (step_df["step_start"] <= end_time)
    ].copy()
    result["step_start"] = result["step_start"].clip(lower=start_time)
    result["step_end"] = result["step_end"].clip(upper=end_time)
    return result.reset_index(drop=True)
