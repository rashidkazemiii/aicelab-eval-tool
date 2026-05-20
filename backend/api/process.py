import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response
from session import state
from physics import CoF as CoF_module
from services.signal_processor import processor
from config import DEFAULT_FILTER_WINDOW

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/calculate")
def calculate():
    if state.df_raw is None:
        return JSONResponse(status_code=400, content={"error": "No file uploaded yet"})
    try:
        state.df_filter = CoF_module.calculate(state.df_raw.copy(), None)
        state.df_filter["CoF"] = state.df_filter["CoF"].round(5)
        state.df_result = None
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Calculate failed: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/data")
def get_data():
    if state.df_filter is None:
        return JSONResponse(status_code=400, content={"error": "Run calculate first"})
    data = state.df_filter[["Zeit [s]", "CoF"]].rename(
        columns={"Zeit [s]": "zeit", "CoF": "cof"}
    )
    return Response(
        content=data.to_json(orient="records", double_precision=5),
        media_type="application/json"
    )


@router.post("/offset")
def apply_offset():
    if state.df_filter is None:
        return JSONResponse(status_code=400, content={"error": "Run calculate first"})
    try:
        df_offset = processor.apply_offset(state.df_filter.copy(), state.step_df)
        state.df_filter["CoF_shifted"] = df_offset["CoF"].values
        cols = ["Zeit [s]", "CoF", "CoF_shifted"]
        data = state.df_filter[cols].rename(
            columns={"Zeit [s]": "zeit", "CoF": "cof", "CoF_shifted": "cof_shifted"}
        )
        return Response(
            content=data.to_json(orient="records", double_precision=8),
            media_type="application/json"
        )
    except Exception as e:
        logger.error(f"Offset failed: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/filter")
def apply_filter(window: int = DEFAULT_FILTER_WINDOW):
    if state.df_filter is None:
        return JSONResponse(status_code=400, content={"error": "Run calculate first"})
    try:
        source = "CoF_shifted" if "CoF_shifted" in state.df_filter.columns else "CoF"
        state.df_filter["CoF_Filtered"] = processor.apply_filter(
            state.df_filter[source], window
        ).values

        cols = ["Zeit [s]", "CoF", "CoF_shifted", "CoF_Filtered"]
        present = [c for c in cols if c in state.df_filter.columns]
        rename = {"Zeit [s]": "zeit", "CoF": "cof", "CoF_shifted": "cof_shifted", "CoF_Filtered": "filtered"}
        data = state.df_filter[present].rename(columns=rename)
        return Response(
            content=data.to_json(orient="records", double_precision=8),
            media_type="application/json"
        )
    except Exception as e:
        logger.error(f"Filter failed: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
