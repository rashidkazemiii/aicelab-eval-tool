import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response
from session import state
from services.signal_processor import processor
from config import DEFAULT_FILTER_WINDOW

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/displacement")


@router.get("/data")
def get_displacement_data():
    if state.df_filter is None:
        return JSONResponse(status_code=400, content={"error": "Run calculate first"})
    if "stroke" not in state.df_filter.columns:
        return JSONResponse(status_code=400, content={"error": "No stroke data available"})

    data = state.df_filter[["Zeit [s]", "stroke"]].rename(
        columns={"Zeit [s]": "zeit"}
    )
    return Response(
        content=data.to_json(orient="records", double_precision=8),
        media_type="application/json"
    )


@router.post("/offset")
def apply_displacement_offset():
    if state.df_filter is None:
        return JSONResponse(status_code=400, content={"error": "Run calculate first"})
    if "stroke" not in state.df_filter.columns:
        return JSONResponse(status_code=400, content={"error": "No stroke data available"})
    try:
        df_offset = processor.apply_stroke_offset(state.df_filter.copy(), state.step_df)
        state.df_filter["stroke_shifted"] = df_offset["stroke"].values

        cols = ["Zeit [s]", "stroke", "stroke_shifted"]
        data = state.df_filter[cols].rename(columns={"Zeit [s]": "zeit"})
        return Response(
            content=data.to_json(orient="records", double_precision=8),
            media_type="application/json"
        )
    except Exception as e:
        logger.error(f"Displacement offset failed: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/filter")
def apply_displacement_filter(window: int = DEFAULT_FILTER_WINDOW):
    if state.df_filter is None:
        return JSONResponse(status_code=400, content={"error": "Run calculate first"})
    if "stroke" not in state.df_filter.columns:
        return JSONResponse(status_code=400, content={"error": "No stroke data available"})
    try:
        source = "stroke_shifted" if "stroke_shifted" in state.df_filter.columns else "stroke"
        state.df_filter["stroke_filtered"] = processor.apply_filter(
            state.df_filter[source], window
        ).values

        cols = ["Zeit [s]", "stroke", "stroke_shifted", "stroke_filtered"]
        present = [c for c in cols if c in state.df_filter.columns]
        data = state.df_filter[present].rename(columns={"Zeit [s]": "zeit"})
        return Response(
            content=data.to_json(orient="records", double_precision=8),
            media_type="application/json"
        )
    except Exception as e:
        logger.error(f"Displacement filter failed: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/evaluate")
def evaluate_displacement():
    if state.df_filter is None:
        return JSONResponse(status_code=400, content={"error": "Run calculate first"})
    if "stroke" not in state.df_filter.columns:
        return JSONResponse(status_code=400, content={"error": "No stroke data available"})
    try:
        col = next(
            (c for c in ("stroke_filtered", "stroke_shifted", "stroke")
             if c in state.df_filter.columns),
            None
        )
        if col is None:
            return JSONResponse(status_code=400, content={"error": "No stroke column available"})
        minima = processor.find_minima(state.df_filter, col)
        return {"status": "success", "cycles": len(minima)}
    except Exception as e:
        logger.error(f"Displacement evaluate failed: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
