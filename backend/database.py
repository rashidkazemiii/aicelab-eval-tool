"""
Persistent storage for evaluated friction tests.

One SQLite file (tribology.db, next to this module) holds:

  tests        — one row per saved test (identity + the params it was evaluated with)
  results      — one row per row of CoF_Stat's output (one step, or one synthetic
                 whole-file "step" when the test has no real step data)
  per_cycle    — one row per friction cycle (for future ML / AI training)
  minima       — one row per detected zero-crossing pair
  raw_samples  — one row per raw data sample (the full-resolution signal)
"""

from __future__ import annotations

import math
import os
from datetime import datetime
from typing import Optional

import pandas as pd
from sqlalchemy import (
    Column, DateTime, Float, ForeignKey, Integer, String, Text,
    create_engine, func, inspect, text,
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

_DB_PATH = os.path.join(os.path.dirname(__file__), "tribology.db")
DATABASE_URL = f"sqlite:///{_DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class Test(Base):
    """One row per saved test."""
    __tablename__ = "tests"

    id            = Column(Integer, primary_key=True, index=True)
    file_name     = Column(Text,    nullable=False)
    data_type     = Column(String,  nullable=False)          # OFT / SRV / SRV_FSA
    uploaded_at   = Column(DateTime, default=datetime.utcnow)

    filter_window = Column(Integer)
    static_range  = Column(Float)
    dynamic_min   = Column(Float)
    dynamic_max   = Column(Float)
    # How the static CoF was found: "fixed_window" (Evaluate - biggest value
    # in the first static_range % of the cycle) or "pulse" (Evaluate with
    # pulse - first peak after the speed pulse's edge). NULL on tests saved
    # before this column existed = fixed_window.
    static_method = Column(String)

    results     = relationship("Result",     back_populates="test",
                                cascade="all, delete-orphan")
    per_cycle   = relationship("PerCycle",   back_populates="test",
                                cascade="all, delete-orphan")
    raw_samples = relationship("RawSample",  back_populates="test",
                                cascade="all, delete-orphan")
    minima      = relationship("Minima",     back_populates="test",
                                cascade="all, delete-orphan")
    steps       = relationship("Step",       back_populates="test",
                                cascade="all, delete-orphan")


class Result(Base):
    """One row per row of CoF_Stat's output (one per active step)."""
    __tablename__ = "results"

    id               = Column(Integer, primary_key=True)
    test_id          = Column(Integer, ForeignKey("tests.id"), nullable=False)
    time_range       = Column(String)
    static_mean_cof  = Column(Float)
    static_sd        = Column(Float)
    static_n         = Column(Integer)
    static_sum       = Column(Float)
    static_variance  = Column(Float)
    dynamic_mean_cof = Column(Float)
    dynamic_sd       = Column(Float)
    dynamic_n        = Column(Integer)
    dynamic_sum      = Column(Float)
    dynamic_variance = Column(Float)

    test = relationship("Test", back_populates="results")


class PerCycle(Base):
    """One row per friction cycle. Training data for future ML / AI models."""
    __tablename__ = "per_cycle"

    id               = Column(Integer, primary_key=True)
    test_id          = Column(Integer, ForeignKey("tests.id"), nullable=False)
    cycle_index      = Column(Integer)
    static_cof_time  = Column(Float)
    static_cof       = Column(Float)
    dynamic_cof_time = Column(Float)
    dynamic_cof      = Column(Float)
    dynamic_sd       = Column(Float)
    dynamic_n        = Column(Integer)
    dynamic_sigma    = Column(Float)
    dynamic_variance = Column(Float)
    start_dynamic_time = Column(Float)
    start_dynamic_cof  = Column(Float)
    end_dynamic_time   = Column(Float)
    end_dynamic_cof    = Column(Float)
    # Ground truth entered by hand on the chart: was the static point the
    # tool picked right? "correct" / "wrong" / NULL (not labelled). When it
    # was wrong, corrected_static_time is where the user said the peak
    # really is (NULL if they only said "wrong").
    label                 = Column(String)
    corrected_static_time = Column(Float)

    test = relationship("Test", back_populates="per_cycle")


class Step(Base):
    """One row per test step (the file's step table: time window and speed).
    Needed to bring a saved test back into the Analysis tab - the speed
    pulse and the per-step statistics both need the step windows, and the
    pulse needs the speed. Tests saved before this table existed have no
    rows here; get_step_df falls back to the Result rows' time ranges."""
    __tablename__ = "steps"

    id          = Column(Integer, primary_key=True)
    test_id     = Column(Integer, ForeignKey("tests.id"), nullable=False, index=True)
    step_index  = Column(Integer)
    start_time  = Column(Float)
    end_time    = Column(Float)
    speed       = Column(Float)      # Drehzahl [U/min], NULL if the file had none
    inactive    = Column(Integer)    # 0 / 1

    test = relationship("Test", back_populates="steps")


class Minima(Base):
    """One row per detected zero-crossing pair (cof_eval['minima'] in app.py)."""
    __tablename__ = "minima"

    id              = Column(Integer, primary_key=True)
    test_id         = Column(Integer, ForeignKey("tests.id"), nullable=False, index=True)
    crossing_index  = Column(Integer)
    minus_min_time  = Column(Float)
    minus_min_cof   = Column(Float)
    plus_min_time   = Column(Float)
    plus_min_cof    = Column(Float)
    min_time        = Column(Float)
    min_cof         = Column(Float)

    test = relationship("Test", back_populates="minima")


class RawSample(Base):
    """One row per raw data sample (the full-resolution signal shown in the
    CoF Analysis results table: Time / CoF / Filtered CoF)."""
    __tablename__ = "raw_samples"

    id           = Column(Integer, primary_key=True)
    test_id      = Column(Integer, ForeignKey("tests.id"), nullable=False, index=True)
    row_index    = Column(Integer)
    time         = Column(Float)
    cof          = Column(Float)
    filtered_cof = Column(Float)

    test = relationship("Test", back_populates="raw_samples")


def create_tables() -> None:
    """Create all tables if they do not exist yet, and add any columns that
    are new to the models but missing from an already-created table. This app
    has a single local SQLite file with no other consumers, so a plain
    ALTER TABLE ADD COLUMN is sufficient — no migration tool needed."""
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if table.name not in existing_tables:
                continue  # just created above, already has every column
            existing_cols = set()
            for c in inspector.get_columns(table.name):
                existing_cols.add(c["name"])
            for column in table.columns:
                if column.name not in existing_cols:
                    col_type = column.type.compile(dialect=engine.dialect)
                    conn.execute(text(
                        f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {col_type}'
                    ))


def _clean(v) -> Optional[float]:
    """Convert NaN / inf to None so SQLite accepts it."""
    try:
        if v is None:
            return None
        v_as_float = float(v)
        if math.isnan(v_as_float) or math.isinf(v_as_float):
            return None
        return v_as_float
    except (TypeError, ValueError):
        return None


def save_evaluation(
    file_name: str,
    data_type: str,
    filter_window,
    static_range: float,
    dynamic_min: float,
    dynamic_max: float,
    stats_df: pd.DataFrame,       # from stat_funcs.CoF_Stat — one row per active step
    per_cycle_df: pd.DataFrame,   # from cof_eval["cof_res"] — one row per cycle
    raw_df: Optional[pd.DataFrame] = None,    # "Zeit", "CoF", optionally "Filtered CoF" — one row per raw sample
    minima_df: Optional[pd.DataFrame] = None, # from cof_eval["minima"] — one row per zero-crossing pair
    static_method: str = "fixed_window",      # see Test.static_method
    step_df: Optional[pd.DataFrame] = None,   # the file's step table — see Step
) -> int:
    """Persist one complete evaluation to the database. Returns the new test.id."""
    db = SessionLocal()
    try:
        if filter_window is None:
            _filter_window_value = None
        else:
            _filter_window_value = int(filter_window)
        test = Test(
            file_name=file_name, data_type=data_type,
            filter_window=_filter_window_value,
            static_range=static_range, dynamic_min=dynamic_min, dynamic_max=dynamic_max,
            static_method=static_method,
        )
        db.add(test)
        db.flush()  # populate test.id before adding children

        for _, row in stats_df.iterrows():
            db.add(Result(
                test_id=test.id,
                time_range=row.get("Time Range"),
                static_mean_cof=_clean(row.get("Static Avg")),
                static_sd=_clean(row.get("Static Std Dev")),
                static_n=_clean(row.get("Static N")),
                static_sum=_clean(row.get("Static Avg x N")),
                static_variance=_clean(row.get("Static Var")),
                dynamic_mean_cof=_clean(row.get("Dynamic Avg")),
                dynamic_sd=_clean(row.get("Dynamic Std Dev")),
                dynamic_n=_clean(row.get("Dynamic N")),
                dynamic_sum=_clean(row.get("Dynamic Avg x N")),
                dynamic_variance=_clean(row.get("Dynamic Var")),
            ))

        for idx, row in per_cycle_df.iterrows():
            db.add(PerCycle(
                test_id=test.id, cycle_index=int(idx),
                static_cof_time=_clean(row.get("staticCoFTime")),
                static_cof=_clean(row.get("staticCoF")),
                dynamic_cof_time=_clean(row.get("dynamicCoFTime")),
                dynamic_cof=_clean(row.get("dynamicCoF")),
                dynamic_sd=_clean(row.get("dynamicCoFSD")),
                dynamic_n=_clean(row.get("dynamicCoFn")),
                dynamic_sigma=_clean(row.get("dynamicCoFsigma")),
                dynamic_variance=_clean(row.get("dynamicCoFvariance")),
                start_dynamic_time=_clean(row.get("startdynamicTime")),
                start_dynamic_cof=_clean(row.get("startdynamicCoF")),
                end_dynamic_time=_clean(row.get("enddynamicTime")),
                end_dynamic_cof=_clean(row.get("enddynamicCoF")),
            ))

        if minima_df is not None and not minima_df.empty:
            _records = []
            for idx, row in minima_df.iterrows():
                _records.append({
                    "test_id": test.id, "crossing_index": int(idx),
                    "minus_min_time": _clean(row.get("-Min Zeit")),
                    "minus_min_cof": _clean(row.get("-Min CoF")),
                    "plus_min_time": _clean(row.get("+Min Zeit")),
                    "plus_min_cof": _clean(row.get("+Min CoF")),
                    "min_time": _clean(row.get("Min Zeit")),
                    "min_cof": _clean(row.get("Min CoF")),
                })
            db.bulk_insert_mappings(Minima, _records)

        if step_df is not None and not step_df.empty:
            for idx, row in step_df.iterrows():
                if "Drehzahl" in step_df.columns:
                    _speed = _clean(row.get("Drehzahl"))
                else:
                    _speed = None
                if "inactive" in step_df.columns and bool(row.get("inactive")):
                    _inactive = 1
                else:
                    _inactive = 0
                db.add(Step(
                    test_id=test.id, step_index=int(idx),
                    start_time=_clean(row.get("Startzeit [s]")),
                    end_time=_clean(row.get("Endzeit [s]")),
                    speed=_speed, inactive=_inactive,
                ))

        if raw_df is not None and not raw_df.empty:
            _times = raw_df["Zeit"].tolist()
            _cofs = raw_df["CoF"].tolist()
            _has_filtered = "Filtered CoF" in raw_df.columns
            if _has_filtered:
                _filtered = raw_df["Filtered CoF"].tolist()
            else:
                _filtered = [None] * len(raw_df)

            _records = []
            for i in range(len(_times)):
                if _has_filtered:
                    _filtered_cof_value = _clean(_filtered[i])
                else:
                    _filtered_cof_value = None
                _records.append({
                    "test_id": test.id, "row_index": i,
                    "time": _clean(_times[i]), "cof": _clean(_cofs[i]),
                    "filtered_cof": _filtered_cof_value,
                })
            db.bulk_insert_mappings(RawSample, _records)

        db.commit()
        return test.id
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def find_existing_test(file_name: str):
    """Return the existing Test row with this exact file name, or None."""
    db = SessionLocal()
    try:
        return db.query(Test).filter(Test.file_name == file_name).first()
    finally:
        db.close()


def list_tests() -> list[dict]:
    """All saved tests, newest first, with their Result rows flattened in."""
    db = SessionLocal()
    try:
        tests = db.query(Test).order_by(Test.id.desc()).all()
        out = []
        for t in tests:
            # For a test evaluated with the speed pulse the Static % window
            # was not what found the static CoF, so the column says so
            # instead of showing a number that was not used.
            if t.static_method == "pulse":
                static_range_shown = "pulse"
            else:
                static_range_shown = t.static_range
            row = {
                "id": t.id,
                "file_name": t.file_name,
                "data_type": t.data_type,
                "uploaded_at": t.uploaded_at,
                "filter_window": t.filter_window,
                "static_range": static_range_shown,
                "dynamic_min": t.dynamic_min,
                "dynamic_max": t.dynamic_max,
                "steps": len(t.results),
                "labels": _labels_summary(t.per_cycle),
            }
            out.append(row)
        return out
    finally:
        db.close()


def _labels_summary(per_cycle_rows) -> str:
    """'12 ok, 3 wrong' for the History list; '' when nothing is labelled.
    Plain ASCII on purpose (no check marks) - see ANALYSIS_TAB in app.py."""
    n_correct = 0
    n_wrong = 0
    for r in per_cycle_rows:
        if r.label == "correct":
            n_correct += 1
        elif r.label == "wrong":
            n_wrong += 1
    if n_correct == 0 and n_wrong == 0:
        return ""
    return f"{n_correct} ok, {n_wrong} wrong"


def list_tests_df() -> pd.DataFrame:
    """list_tests(), as a DataFrame with the right columns present even when
    there are no saved tests yet - so the History table doesn't render with a
    blank schema.
    """
    tests = list_tests()
    if tests:
        return pd.DataFrame(tests)
    return pd.DataFrame(columns=[
        "id", "file_name", "data_type", "uploaded_at", "filter_window",
        "static_range", "dynamic_min", "dynamic_max", "steps", "labels",
    ])


def save_full_evaluation(
    file_name: str,
    filter_params,
    eval_params,
    df_display: pd.DataFrame,
    df_proc: pd.DataFrame,
    filter_active: bool,
    cof_eval: dict,
    stats_result: pd.DataFrame,
    step_df: Optional[pd.DataFrame] = None,
) -> int:
    """Build the raw-sample dataframe from the current pipeline state and
    persist one full evaluation via save_evaluation(). Returns the new
    test.id. The caller is responsible for any overwrite/conflict handling
    (find_existing_test + delete_test) before calling this - it always
    inserts a fresh row.
    """
    raw_df = df_display[["Zeit", "CoF"]].copy()
    if filter_active:
        raw_df["Filtered CoF"] = df_proc["CoF"].values
    if filter_params:
        filter_window = int(filter_params["filter_points"])
    else:
        filter_window = None
    return save_evaluation(
        file_name=file_name,
        data_type="OFT",
        filter_window=filter_window,
        static_range=float(eval_params["static_range"]),
        dynamic_min=float(eval_params["dyn_min"]),
        dynamic_max=float(eval_params["dyn_max"]),
        stats_df=stats_result,
        per_cycle_df=cof_eval["cof_res"],
        raw_df=raw_df,
        minima_df=cof_eval["minima"],
        static_method=cof_eval.get("static_method", "fixed_window"),
        step_df=step_df,
    )


def get_step_df(test_id: int):
    """The saved test's step table in the shape the pipeline uses
    ("Startzeit [s]", "Endzeit [s]", "inactive", and "Drehzahl" when any
    speed is stored), or None when the test has no steps at all.

    Tests saved before the steps table existed have no Step rows; their
    step windows are recovered from the Result rows' "start-end" time-range
    text instead (no speed is known for those, so no Drehzahl column).
    """
    db = SessionLocal()
    try:
        steps = (
            db.query(Step).filter(Step.test_id == test_id)
            .order_by(Step.step_index).all()
        )
        results = db.query(Result).filter(Result.test_id == test_id).all()
    finally:
        db.close()

    starts = []
    ends = []
    speeds = []
    inactive = []
    if len(steps) > 0:
        for s in steps:
            starts.append(s.start_time)
            ends.append(s.end_time)
            speeds.append(s.speed)
            inactive.append(bool(s.inactive))
    else:
        for r in results:
            text_range = r.time_range
            if not text_range:
                continue
            # "60.0-80.0"; older rows used an en dash as the separator
            parts = str(text_range).replace("\u2013", "-").split("-")
            if len(parts) != 2:
                continue
            try:
                starts.append(float(parts[0]))
                ends.append(float(parts[1]))
            except ValueError:
                continue
            speeds.append(None)
            inactive.append(False)

    if len(starts) == 0:
        return None
    step_df = pd.DataFrame({
        "Startzeit [s]": starts,
        "Endzeit [s]": ends,
        "inactive": inactive,
    })
    has_speed = False
    for v in speeds:
        if v is not None:
            has_speed = True
    if has_speed:
        step_df["Drehzahl"] = speeds
    return step_df


def load_test_for_analysis(test_id: int) -> dict:
    """Everything the Analysis tab needs to show a saved test as if it had
    just been evaluated: the raw and filtered signal, the parameters, the
    evaluation result in Evaluate()'s own column names, and the step table.
    Returns None if the test does not exist."""
    from physics import utility_functions

    db = SessionLocal()
    try:
        test = db.query(Test).filter(Test.id == test_id).first()
        if test is None:
            return None
        file_name = test.file_name
        filter_window = test.filter_window
        eval_params = {
            "static_range": str(test.static_range),
            "dyn_min": str(test.dynamic_min),
            "dyn_max": str(test.dynamic_max),
        }
        static_method = test.static_method or "fixed_window"
        cycles = (
            db.query(PerCycle).filter(PerCycle.test_id == test_id)
            .order_by(PerCycle.cycle_index).all()
        )
        mins = (
            db.query(Minima).filter(Minima.test_id == test_id)
            .order_by(Minima.crossing_index).all()
        )
    finally:
        db.close()

    raw = get_full_raw_table(test_id)
    step_df = get_step_df(test_id)

    df_display = pd.DataFrame({"Zeit": raw["Time [s]"], "CoF": raw["CoF"]})
    if step_df is not None and "Drehzahl" in step_df.columns:
        df_display = utility_functions.assign_step_speed(df_display, step_df)
    if "Filtered CoF" in raw.columns:
        df_proc = df_display.copy()
        df_proc["CoF"] = raw["Filtered CoF"].values
        filter_params = {"filter_points": str(filter_window)}
    else:
        df_proc = df_display.copy()
        filter_params = None

    def _col(rows, name):
        values = []
        for r in rows:
            values.append(getattr(r, name))
        return values

    cof_res = pd.DataFrame({
        "startdynamicTime": _col(cycles, "start_dynamic_time"),
        "startdynamicCoF": _col(cycles, "start_dynamic_cof"),
        "enddynamicTime": _col(cycles, "end_dynamic_time"),
        "enddynamicCoF": _col(cycles, "end_dynamic_cof"),
        "dynamicCoFTime": _col(cycles, "dynamic_cof_time"),
        "dynamicCoF": _col(cycles, "dynamic_cof"),
        "dynamicCoFSD": _col(cycles, "dynamic_sd"),
        "dynamicCoFn": _col(cycles, "dynamic_n"),
        "dynamicCoFsigma": _col(cycles, "dynamic_sigma"),
        "dynamicCoFvariance": _col(cycles, "dynamic_variance"),
        "staticCoF": _col(cycles, "static_cof"),
        "staticCoFTime": _col(cycles, "static_cof_time"),
    })
    minima = pd.DataFrame({
        "-Min Zeit": _col(mins, "minus_min_time"),
        "-Min CoF": _col(mins, "minus_min_cof"),
        "+Min Zeit": _col(mins, "plus_min_time"),
        "+Min CoF": _col(mins, "plus_min_cof"),
        "Min Zeit": _col(mins, "min_time"),
        "Min CoF": _col(mins, "min_cof"),
    })
    return {
        "test_id": test_id,
        "file_name": file_name,
        "df_display": df_display,
        "df_proc": df_proc,
        "filter_params": filter_params,
        "eval_params": eval_params,
        "static_method": static_method,
        "cof_eval": {"minima": minima, "cof_res": cof_res, "static_method": static_method},
        "step_df": step_df,
    }


def get_labels_for_test(test_id: int) -> dict:
    """{static_cof_time: {"label": ..., "corrected_t": ...}} for every
    labelled cycle of one saved test - used to draw saved labels again."""
    db = SessionLocal()
    try:
        rows = (
            db.query(PerCycle)
            .filter(PerCycle.test_id == test_id, PerCycle.label.isnot(None))
            .all()
        )
        out = {}
        for r in rows:
            if r.static_cof_time is None:
                continue
            out[r.static_cof_time] = {"label": r.label, "corrected_t": r.corrected_static_time}
        return out
    finally:
        db.close()


def get_labels_for_file(file_name: str) -> dict:
    """Saved labels of the test with this file name, or {} if none."""
    test = find_existing_test(file_name)
    if test is None:
        return {}
    return get_labels_for_test(test.id)


def get_cycles(test_id: int) -> list[dict]:
    """Per-cycle rows for one test, ordered by cycle_index."""
    db = SessionLocal()
    try:
        rows = (
            db.query(PerCycle)
            .filter(PerCycle.test_id == test_id)
            .order_by(PerCycle.cycle_index)
            .all()
        )
        out = []
        for r in rows:
            out.append({
                "cycle_index": r.cycle_index,
                "static_cof_time": r.static_cof_time,
                "static_cof": r.static_cof,
                "dynamic_cof_time": r.dynamic_cof_time,
                "dynamic_cof": r.dynamic_cof,
                "dynamic_sd": r.dynamic_sd,
                "dynamic_n": r.dynamic_n,
                "dynamic_sigma": r.dynamic_sigma,
                "dynamic_variance": r.dynamic_variance,
                "start_dynamic_time": r.start_dynamic_time,
                "start_dynamic_cof": r.start_dynamic_cof,
                "end_dynamic_time": r.end_dynamic_time,
                "end_dynamic_cof": r.end_dynamic_cof,
            })
        return out
    finally:
        db.close()


def get_minima(test_id: int) -> list[dict]:
    """Zero-crossing rows for one test, ordered by crossing_index."""
    db = SessionLocal()
    try:
        rows = (
            db.query(Minima)
            .filter(Minima.test_id == test_id)
            .order_by(Minima.crossing_index)
            .all()
        )
        out = []
        for r in rows:
            out.append({
                "crossing_index": r.crossing_index,
                "minus_min_time": r.minus_min_time,
                "minus_min_cof": r.minus_min_cof,
                "plus_min_time": r.plus_min_time,
                "plus_min_cof": r.plus_min_cof,
                "min_time": r.min_time,
                "min_cof": r.min_cof,
            })
        return out
    finally:
        db.close()


def count_raw_samples(test_id: int) -> int:
    """How many raw samples are saved for a test - a cheap count, without
    fetching the (possibly 100,000+ row) table itself."""
    db = SessionLocal()
    try:
        return db.query(func.count(RawSample.id)).filter(RawSample.test_id == test_id).scalar()
    finally:
        db.close()


def count_cycles(test_id: int) -> int:
    """How many evaluated cycles are saved for a test - a cheap count,
    without fetching the per-cycle table itself."""
    db = SessionLocal()
    try:
        return db.query(func.count(PerCycle.id)).filter(PerCycle.test_id == test_id).scalar()
    finally:
        db.close()


# A label is matched to its cycle by the static point's time (the chart
# knows the time, not the row); anything closer than this counts as the
# same point. Samples are 1 ms apart, so half a millisecond is unambiguous.
LABEL_MATCH_TOLERANCE_S = 0.0005


def save_cycle_labels(test_id: int, labels: list) -> tuple:
    """Store hand-made labels on a saved test's cycles.

    `labels` is a list of dicts {"t": static point time [s],
    "label": "correct" | "wrong" | None, "corrected_t": time [s] or None}.
    Each one is matched to the PerCycle row of `test_id` whose
    static_cof_time is within LABEL_MATCH_TOLERANCE_S of "t"; a label of None
    clears that row's label again. Returns (matched, unmatched) counts.
    """
    db = SessionLocal()
    try:
        rows = db.query(PerCycle).filter(PerCycle.test_id == test_id).all()
        matched = 0
        unmatched = 0
        for item in labels:
            t = item.get("t")
            if t is None:
                unmatched += 1
                continue
            hit = None
            for r in rows:
                if r.static_cof_time is not None and abs(r.static_cof_time - float(t)) <= LABEL_MATCH_TOLERANCE_S:
                    hit = r
                    break
            if hit is None:
                unmatched += 1
                continue
            label = item.get("label")
            if label not in ("correct", "wrong"):
                label = None
            hit.label = label
            corrected = item.get("corrected_t")
            if label == "wrong" and corrected is not None:
                hit.corrected_static_time = _clean(corrected)
            else:
                hit.corrected_static_time = None
            matched += 1
        db.commit()
        return matched, unmatched
    finally:
        db.close()


def count_labels(test_id: int) -> tuple:
    """(n_correct, n_wrong) for one saved test."""
    db = SessionLocal()
    try:
        rows = db.query(PerCycle).filter(PerCycle.test_id == test_id).all()
        n_correct = 0
        n_wrong = 0
        for r in rows:
            if r.label == "correct":
                n_correct += 1
            elif r.label == "wrong":
                n_wrong += 1
        return n_correct, n_wrong
    finally:
        db.close()


def export_labels_df() -> pd.DataFrame:
    """Every labelled cycle across all saved tests, one row each, with the
    test's file name and static method - the training table for a future
    peak detector."""
    db = SessionLocal()
    try:
        rows = (
            db.query(PerCycle, Test)
            .join(Test, PerCycle.test_id == Test.id)
            .filter(PerCycle.label.isnot(None))
            .order_by(Test.id, PerCycle.cycle_index)
            .all()
        )
        records = []
        for cycle, test in rows:
            records.append({
                "test_id": test.id,
                "file_name": test.file_name,
                "static_method": test.static_method or "fixed_window",
                "cycle_index": cycle.cycle_index,
                "static_cof_time": cycle.static_cof_time,
                "static_cof": cycle.static_cof,
                "dynamic_cof_time": cycle.dynamic_cof_time,
                "dynamic_cof": cycle.dynamic_cof,
                "label": cycle.label,
                "corrected_static_time": cycle.corrected_static_time,
            })
        columns = [
            "test_id", "file_name", "static_method", "cycle_index",
            "static_cof_time", "static_cof", "dynamic_cof_time", "dynamic_cof",
            "label", "corrected_static_time",
        ]
        return pd.DataFrame(records, columns=columns)
    finally:
        db.close()


def get_full_raw_table(test_id: int) -> pd.DataFrame:
    """Per-sample table for a saved test: Time, CoF, and (if filtering was
    used) Filtered CoF - one row per raw sample. Same shape as the live
    Results page's raw table (results_table.build_raw_table)."""
    db = SessionLocal()
    try:
        raw = (
            db.query(RawSample).filter(RawSample.test_id == test_id)
            .order_by(RawSample.row_index).all()
        )
    finally:
        db.close()

    times = []
    cofs = []
    filtered_cofs = []
    has_filtered_cof = False
    for r in raw:
        times.append(r.time)
        cofs.append(r.cof)
        filtered_cofs.append(r.filtered_cof)
        if r.filtered_cof is not None:
            has_filtered_cof = True

    cols = {"Time [s]": times, "CoF": cofs}
    if has_filtered_cof:
        cols["Filtered CoF"] = filtered_cofs
    return pd.DataFrame(cols)


def get_full_eval_table(test_id: int) -> pd.DataFrame:
    """Per-cycle/per-step evaluation table for a saved test - one row per
    cycle/step/zero-crossing, padded only up to each other's row count (not
    to the raw sample count). Same shape as the live Results page's
    evaluation table (results_table.build_eval_table)."""
    import numpy as np

    db = SessionLocal()
    try:
        cycles = (
            db.query(PerCycle).filter(PerCycle.test_id == test_id)
            .order_by(PerCycle.cycle_index).all()
        )
        results = db.query(Result).filter(Result.test_id == test_id).all()
        mins = (
            db.query(Minima).filter(Minima.test_id == test_id)
            .order_by(Minima.crossing_index).all()
        )
    finally:
        db.close()

    n = max(len(cycles), len(results), len(mins))

    def _pad(values):
        return list(values) + [np.nan] * (n - len(values))

    def _column(collection, attribute_name):
        """Pull one attribute out of every row in `collection` into a plain
        list, then pad it with NaN so every column ends up the same length."""
        values = []
        for row in collection:
            values.append(getattr(row, attribute_name))
        return _pad(values)

    cols = {}
    cols["Static CoF time [s]"] = _column(cycles, "static_cof_time")
    cols["Static CoF"] = _column(cycles, "static_cof")
    cols["Dynamic CoF time [s]"] = _column(cycles, "dynamic_cof_time")
    cols["Dynamic CoF"] = _column(cycles, "dynamic_cof")
    cols["Dynamic std dev"] = _column(cycles, "dynamic_sd")
    cols["Dynamic N"] = _column(cycles, "dynamic_n")
    cols["Dynamic CoF sum"] = _column(cycles, "dynamic_sigma")
    cols["Dynamic CoF variance"] = _column(cycles, "dynamic_variance")
    cols["Time range [s]"] = _column(results, "time_range")
    cols["Static mean CoF"] = _column(results, "static_mean_cof")
    cols["Static std dev"] = _column(results, "static_sd")
    cols["Static N"] = _column(results, "static_n")
    cols["Static CoF sum"] = _column(results, "static_sum")
    cols["Static CoF variance"] = _column(results, "static_variance")
    cols["Dynamic mean CoF"] = _column(results, "dynamic_mean_cof")
    cols["Dynamic mean std dev"] = _column(results, "dynamic_sd")
    cols["Dynamic mean N"] = _column(results, "dynamic_n")
    cols["Dynamic CoF avg×N"] = _column(results, "dynamic_sum")
    cols["Dynamic CoF var (step)"] = _column(results, "dynamic_variance")
    cols["-Min time [s]"] = _column(mins, "minus_min_time")
    cols["-Min CoF"] = _column(mins, "minus_min_cof")
    cols["+Min time [s]"] = _column(mins, "plus_min_time")
    cols["+Min CoF"] = _column(mins, "plus_min_cof")
    cols["Min time [s]"] = _column(mins, "min_time")
    cols["CoF minima"] = _column(mins, "min_cof")
    cols["Dynamic start time [s]"] = _column(cycles, "start_dynamic_time")
    cols["Dynamic start CoF"] = _column(cycles, "start_dynamic_cof")
    cols["Dynamic end time [s]"] = _column(cycles, "end_dynamic_time")
    cols["Dynamic end CoF"] = _column(cycles, "end_dynamic_cof")
    cols["Label"] = _column(cycles, "label")
    cols["Corrected static time [s]"] = _column(cycles, "corrected_static_time")

    return pd.DataFrame(cols)


def delete_test(test_id: int) -> bool:
    """Delete a Test (cascades to its Result/PerCycle rows). Returns whether found."""
    db = SessionLocal()
    try:
        test = db.query(Test).filter(Test.id == test_id).first()
        if test is None:
            return False
        db.delete(test)
        db.commit()
        return True
    finally:
        db.close()
