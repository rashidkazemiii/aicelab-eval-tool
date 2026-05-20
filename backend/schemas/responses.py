"""
API response schemas.

Documents the data contract for each endpoint so frontend developers
(and future mobile/AI integrations) know exactly what to expect.
These are not enforced by FastAPI at runtime — they serve as the
authoritative specification for the API surface.
"""
from typing import Optional


# GET /data  →  list of TimeseriesPoint
class TimeseriesPoint:
    zeit: float          # time in seconds
    cof: float           # raw coefficient of friction


# POST /offset  →  list of OffsetPoint
class OffsetPoint:
    zeit: float
    cof: float
    cof_shifted: float   # mean-centered CoF


# POST /filter  →  list of FilterPoint
class FilterPoint:
    zeit: float
    cof: Optional[float]
    cof_shifted: Optional[float]
    filtered: Optional[float]    # median-filtered CoF


# GET /displacement/data  →  list of DisplacementPoint
class DisplacementPoint:
    zeit: float
    stroke: float        # displacement in mm


# POST /displacement/offset  →  list of DisplacementOffsetPoint
class DisplacementOffsetPoint:
    zeit: float
    stroke: float
    stroke_shifted: float


# POST /displacement/filter  →  list of DisplacementFilterPoint
class DisplacementFilterPoint:
    zeit: float
    stroke: Optional[float]
    stroke_shifted: Optional[float]
    stroke_filtered: Optional[float]


# POST /evaluate  →  EvaluateResponse
class EvaluateResponse:
    status: str          # "success"
    cycles: int          # number of detected cycles
    aggregate: dict      # aggregate stats across all cycles (keys match RESULT_COLUMNS)


# GET /result/json  →  list of ResultRow  (48 columns — see config.RESULT_COLUMNS)
# GET /export/timeseries  →  CSV stream (semicolon-separated)
# GET /export/result      →  CSV stream (semicolon-separated)
