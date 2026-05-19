from dataclasses import dataclass
from typing import Optional
import pandas as pd


@dataclass
class SessionState:
    file_path: Optional[str] = None
    data_type: str = "OFT"

    df_raw:    Optional[pd.DataFrame] = None
    df_filter: Optional[pd.DataFrame] = None   # Zeit, CoF, CoF_shifted, CoF_Filtered, stroke, stroke_shifted, stroke_filtered
    df_result: Optional[pd.DataFrame] = None   # per-cycle stats, schema = RESULT_COLUMNS
    step_df:   Optional[pd.DataFrame] = None
    header:    Optional[dict] = None

    def reset(self):
        self.df_raw    = None
        self.df_filter = None
        self.df_result = None
        self.step_df   = None
        self.header    = None


state = SessionState()
