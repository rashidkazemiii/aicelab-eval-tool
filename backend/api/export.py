import io
import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse
from session import state

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/export")


@router.get("/timeseries")
def export_timeseries():
    if state.df_filter is None:
        return JSONResponse(status_code=400, content={"error": "No data to export"})
    df = state.df_filter.copy()
    for col in ("CoF",):
        if col in df.columns:
            df[col] = df[col].apply(lambda x: f"{x:.5f}")
    for col in ("CoF_shifted", "CoF_Filtered", "stroke_shifted", "stroke_filtered"):
        if col in df.columns:
            df[col] = df[col].apply(lambda x: f"{x:.15f}")
    buf = io.StringIO()
    df.to_csv(buf, index=False, sep=";")
    buf.seek(0)
    return StreamingResponse(
        buf, media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=timeseries.csv"}
    )


@router.get("/result")
def export_result():
    if state.df_result is None:
        return JSONResponse(status_code=400, content={"error": "Run evaluate first"})
    buf = io.StringIO()
    state.df_result.to_csv(buf, index=False, sep=";")
    buf.seek(0)
    return StreamingResponse(
        buf, media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=result.csv"}
    )
