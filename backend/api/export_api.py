import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse
from session import state
import io

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/export/timeseries")
def export_timeseries():
    if state.df_filter is None:
        return JSONResponse(status_code=400, content={"error": "Run calculate first"})
    try:
        buf = io.StringIO()
        state.df_filter.to_csv(buf, sep=";", index=False, float_format="%.15f")
        buf.seek(0)
        return StreamingResponse(
            iter([buf.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=timeseries.csv"}
        )
    except Exception as e:
        logger.error(f"Export timeseries failed: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/export/result")
def export_result():
    if state.df_result is None:
        return JSONResponse(status_code=400, content={"error": "Run evaluate first"})
    try:
        buf = io.StringIO()
        state.df_result.to_csv(buf, sep=";", index=False)
        buf.seek(0)
        return StreamingResponse(
            iter([buf.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=result.csv"}
        )
    except Exception as e:
        logger.error(f"Export result failed: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
