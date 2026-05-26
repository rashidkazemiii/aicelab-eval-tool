import logging
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from database import SessionLocal, Test, Result, PerCycle, save_evaluation
from session import state
from config import DEFAULT_FILTER_WINDOW, DEFAULT_STATIC_RANGE, DEFAULT_DYN_MIN, DEFAULT_DYN_MAX

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/history")


@router.get("")
def get_history():
    """Return all tests with their aggregate results."""
    db = SessionLocal()
    try:
        tests = db.query(Test).order_by(Test.id.desc()).all()
        out = []
        for t in tests:
            results = db.query(Result).filter(Result.test_id == t.id).all()
            out.append({
                "id":           t.id,
                "file_name":    t.file_name,
                "data_type":    t.data_type,
                "uploaded_at":  t.uploaded_at.isoformat() if t.uploaded_at else None,
                "filter_window": t.filter_window,
                "static_range":  t.static_range,
                "dynamic_min":   t.dynamic_min,
                "dynamic_max":   t.dynamic_max,
                "results": [
                    {
                        "time_range":       r.time_range,
                        "static_mean_cof":  r.static_mean_cof,
                        "static_sd":        r.static_sd,
                        "static_n":         r.static_n,
                        "static_sum":       r.static_sum,
                        "static_variance":  r.static_variance,
                        "dynamic_mean_cof": r.dynamic_mean_cof,
                        "dynamic_sd":       r.dynamic_sd,
                        "dynamic_n":        r.dynamic_n,
                        "dynamic_sum":      r.dynamic_sum,
                        "dynamic_variance": r.dynamic_variance,
                    }
                    for r in results
                ],
            })
        return out
    finally:
        db.close()


@router.get("/{test_id}/cycles")
def get_cycles(test_id: int):
    """Return per-cycle data for one test."""
    db = SessionLocal()
    try:
        cycles = (
            db.query(PerCycle)
            .filter(PerCycle.test_id == test_id)
            .order_by(PerCycle.cycle_index)
            .all()
        )
        if not cycles:
            return JSONResponse(status_code=404, content={"error": "No cycles found"})
        return [
            {
                "cycle_index":     c.cycle_index,
                "static_cof_time": c.static_cof_time,
                "static_cof":      c.static_cof,
                "dynamic_cof_time":c.dynamic_cof_time,
                "dynamic_cof":     c.dynamic_cof,
                "dynamic_sd":      c.dynamic_sd,
                "dynamic_n":       c.dynamic_n,
            }
            for c in cycles
        ]
    finally:
        db.close()


@router.delete("/{test_id}")
def delete_test(test_id: int):
    """Delete a test and all its results / cycles."""
    db = SessionLocal()
    try:
        test = db.query(Test).filter(Test.id == test_id).first()
        if not test:
            return JSONResponse(status_code=404, content={"error": "Test not found"})
        db.delete(test)
        db.commit()
        return {"status": "deleted", "id": test_id}
    except Exception as e:
        db.rollback()
        logger.error(f"Delete failed: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        db.close()


@router.post("/save")
def save(force: bool = False):
    """
    Save the current session's evaluation result to the database.

    - Requires evaluate to have been run first (state.df_result must exist).
    - If a test with the same filename already exists and force=False,
      returns {"status": "conflict"} with details so the frontend can ask
      the user before overwriting.
    - force=True deletes the existing record and saves fresh.
    """
    if state.df_result is None:
        return JSONResponse(status_code=400,
                            content={"error": "No evaluation result. Run Evaluate first."})

    file_name  = state.file_path or "unknown"
    base_name  = Path(file_name).name   # just the filename, no temp_uploads/ prefix

    db = SessionLocal()
    try:
        # ---- conflict check ------------------------------------------------
        existing = (
            db.query(Test)
            .filter(Test.file_name.like(f"%{base_name}"))
            .order_by(Test.id.desc())
            .first()
        )
        if existing and not force:
            return {
                "status":        "conflict",
                "existing_id":   existing.id,
                "existing_date": existing.uploaded_at.isoformat()
                                 if existing.uploaded_at else None,
                "file_name":     base_name,
            }

        # ---- overwrite: delete the old record ------------------------------
        if existing and force:
            db.delete(existing)
            db.commit()

    finally:
        db.close()

    # ---- build agg dict from df_result row 0 -------------------------------
    r = state.df_result.iloc[0] if len(state.df_result) > 0 else {}
    agg = {
        "timeRange":         r.get("timeRange")         if hasattr(r, "get") else None,
        "staticMeanCoF":     r.get("staticMeanCoF")     if hasattr(r, "get") else None,
        "staticCoFSD_agg":   r.get("staticCoFSD_agg")   if hasattr(r, "get") else None,
        "staticCoFN_agg":    r.get("staticCoFN_agg")    if hasattr(r, "get") else None,
        "staticCoFSum_agg":  r.get("staticCoFSum_agg")  if hasattr(r, "get") else None,
        "staticCoFVar_agg":  r.get("staticCoFVar_agg")  if hasattr(r, "get") else None,
        "dynamicMeanCoF":    r.get("dynamicMeanCoF")    if hasattr(r, "get") else None,
        "dynamicCoFSD_agg":  r.get("dynamicCoFSD_agg")  if hasattr(r, "get") else None,
        "dynamicCoFN_agg":   r.get("dynamicCoFN_agg")   if hasattr(r, "get") else None,
        "dynamicCoFSum_agg": r.get("dynamicCoFSum_agg") if hasattr(r, "get") else None,
        "dynamicCoFVar_agg": r.get("dynamicCoFVar_agg") if hasattr(r, "get") else None,
    }

    # ---- per_cycle df -------------------------------------------------------
    from physics.cof import cof_evaluate   # already computed, grab from df_result
    per_cycle_cols = [
        "staticCoFTime", "staticCoF", "dynamicCoFTime", "dynamicCoF",
        "dynamicCoFSD", "dynamicCoFn", "dynamicCoFsigma", "dynamicCoFvariance",
    ]
    present = [c for c in per_cycle_cols if c in state.df_result.columns]
    per_cycle_df = state.df_result[present].dropna(subset=["staticCoF"]).reset_index(drop=True)

    try:
        test_id = save_evaluation(
            file_name     = file_name,
            data_type     = state.data_type,
            filter_window = DEFAULT_FILTER_WINDOW,
            static_range  = DEFAULT_STATIC_RANGE,
            dynamic_min   = DEFAULT_DYN_MIN,
            dynamic_max   = DEFAULT_DYN_MAX,
            agg           = agg,
            per_cycle_df  = per_cycle_df,
            step_stats_df = state.df_step_stats,
        )
        return {"status": "saved", "test_id": test_id}
    except Exception as e:
        logger.error(f"Save failed: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
