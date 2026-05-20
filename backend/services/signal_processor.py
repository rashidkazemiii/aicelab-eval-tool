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
from physics.cof    import cof_offset, cof_filter, cof_find_minima, cof_evaluate
from physics.stroke import stroke_offset, stroke_filter
from config import DEFAULT_FILTER_WINDOW

logger = logging.getLogger(__name__)


class SignalProcessor:

    def apply_cof_offset(self, df: pd.DataFrame, step_df: pd.DataFrame) -> pd.DataFrame:
        """Mean-center CoF per active test step."""
        return cof_offset(df, step_df)

    def apply_stroke_offset(self, df: pd.DataFrame, step_df: pd.DataFrame) -> pd.DataFrame:
        """Mean-center stroke per active test step."""
        return stroke_offset(df, step_df)

    def apply_filter(self, series: pd.Series, window: int = DEFAULT_FILTER_WINDOW) -> pd.Series:
        """Rolling median filter for noise reduction."""
        return cof_filter(series, window)

    def find_minima(self, df: pd.DataFrame, column: str) -> pd.DataFrame:
        """Zero-crossing detection: finds half-cycle boundaries in a waveform."""
        return cof_find_minima(df, column)

    def evaluate_cof_cycles(
        self,
        df: pd.DataFrame,
        minima: pd.DataFrame,
        static_range: float,
        dyn_min: float,
        dyn_max: float,
    ) -> pd.DataFrame:
        """Extract per-cycle static and dynamic CoF statistics."""
        return cof_evaluate(df, minima, static_range, dyn_min, dyn_max)


# Module-level singleton — import this in all API modules
processor = SignalProcessor()
