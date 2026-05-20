import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response
from session import state
from physics.stroke import stroke_offset, stroke_filter, stroke_find_minima
from config import DEFAULT_FILTER_WINDOW

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/displacement")


@router.get("/data")
def get_displacement_data():
    if state.df_work is None:
        return JSONResponse(status_code=400, content={"error": "Run calculate first"})
    if "stroke" not in state.df_work.columns:
        return JSONResponse(status_code=400, content={"error": "No stroke data available"})

    data = state.df_work[["time", "stroke"]]
    return Response(
        content=data.to_json(orient="records", double_precision=8),
        media_type="application/json"
    )


@router.post("/offset")
def apply_displacement_offset():
    if state.df_work is None:
        return JSONResponse(status_code=400, content={"error": "Run calculate first"})
    if "stroke" not in state.df_work.columns:
        return JSONResponse(status_code=400, content={"error": "No stroke data available"})
    try:
        df_offset = stroke_offset(state.df_work.copy(), state.step_df)
        state.df_work["stroke_shifted"] = df_offset["stroke"].values

        cols = ["time", "stroke", "stroke_shifted"]
        data = state.df_work[cols]
        return Response(
            content=data.to_json(orient="records", double_precision=8),
            media_type="application/json"
        )
    except Exception as e:
        logger.error(f"Displacement offset failed: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/filter")
def apply_displacement_filter(window: int = DEFAULT_FILTER_WINDOW):
    if state.df_work is None:
        return JSONResponse(status_code=400, content={"error": "Run calculate first"})
    if "stroke" not in state.df_work.columns:
        return JSONResponse(status_code=400, content={"error": "No stroke data available"})
    try:
        source = "stroke_shifted" if "stroke_shifted" in state.df_work.columns else "stroke"
        state.df_work["stroke_filtered"] = stroke_filter(state.df_work[source], window).values

        cols = ["time", "stroke", "stroke_shifted", "stroke_filtered"]
        present = [c for c in cols if c in state.df_work.columns]
        data = state.df_work[present]
        return Response(
            content=data.to_json(orient="records", double_precision=8),
            media_type="application/json"
        )
    except Exception as e:
        logger.error(f"Displacement filter failed: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/evaluate")
def evaluate_displacement():
    if state.df_work is None:
        return JSONResponse(status_code=400, content={"error": "Run calculate first"})
    if "stroke" not in state.df_work.columns:
        return JSONResponse(status_code=400, content={"error": "No stroke data available"})
    try:
        col = next(
            (c for c in ("stroke_filtered", "stroke_shifted", "stroke")
             if c in state.df_work.columns),
            None
        )
        if col is None:
            return JSONResponse(status_code=400, content={"error": "No stroke column available"})
        minima = stroke_find_minima(state.df_work, col)
        return {"status": "success", "cycles": len(minima)}
    except Exception as e:
        logger.error(f"Displacement evaluate failed: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
