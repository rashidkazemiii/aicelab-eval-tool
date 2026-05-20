"""
Service layer: sits between API endpoints and physics algorithms.

All API modules import from here instead of calling physics functions directly.
Benefits:
  - Swap algorithms without touching the API
  - Add AI data logging here in the future
  - Add caching or timing to specific operations
  - Single place to add cross-cutting concerns (logging, metrics)
"""
import logging
import pandas as pd
from physics import utility_functions
from config import DEFAULT_FILTER_WINDOW

logger = logging.getLogger(__name__)


class SignalProcessor:

    def apply_offset(self, df: pd.DataFrame, step_df: pd.DataFrame) -> pd.DataFrame:
        """Mean-center CoF and stroke per active test step."""
        return utility_functions.offset(df, step_df)

    def apply_filter(self, series: pd.Series, window: int = DEFAULT_FILTER_WINDOW) -> pd.Series:
        """Rolling median filter for noise reduction."""
        return utility_functions.filter_vb_style(series, window)

    def find_minima(self, df: pd.DataFrame, column: str) -> pd.DataFrame:
        """Zero-crossing detection: finds half-cycle boundaries in a waveform."""
        return utility_functions.Find_minima(df, column)

    def evaluate_cycles(
        self,
        df: pd.DataFrame,
        minima: pd.DataFrame,
        column: str,
        static_range: float,
        dyn_min: float,
        dyn_max: float,
    ) -> pd.DataFrame:
        """Extract per-cycle static and dynamic CoF statistics."""
        return utility_functions.Evaluate(df, minima, column, static_range, dyn_min, dyn_max)


# Module-level singleton — import this in all API modules
processor = SignalProcessor()
