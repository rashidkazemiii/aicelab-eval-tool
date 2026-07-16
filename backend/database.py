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

from sqlalchemy import (
    Column, DateTime, Float, ForeignKey, Integer, String, Text,
    create_engine, inspect, text,
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

    results     = relationship("Result",     back_populates="test",
                                cascade="all, delete-orphan")
    per_cycle   = relationship("PerCycle",   back_populates="test",
                                cascade="all, delete-orphan")
    raw_samples = relationship("RawSample",  back_populates="test",
                                cascade="all, delete-orphan")
    minima      = relationship("Minima",     back_populates="test",
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

    test = relationship("Test", back_populates="per_cycle")


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
            existing_cols = {c["name"] for c in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name not in existing_cols:
                    col_type = column.type.compile(dialect=engine.dialect)
                    conn.execute(text(
                        f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {col_type}'
                    ))


def _clean(v):
    """Convert NaN / inf to None so SQLite accepts it."""
    try:
        return None if (v is None or math.isnan(float(v)) or math.isinf(float(v))) else float(v)
    except (TypeError, ValueError):
        return None


def save_evaluation(
    file_name: str,
    data_type: str,
    filter_window,
    static_range: float,
    dynamic_min: float,
    dynamic_max: float,
    stats_df,       # DataFrame from stat_funcs.CoF_Stat — one row per active step
    per_cycle_df,   # DataFrame from cof_eval["cof_res"] — one row per cycle
    raw_df=None,    # DataFrame with "Zeit", "CoF", optionally "Filtered CoF" — one row per raw sample
    minima_df=None, # DataFrame from cof_eval["minima"] — one row per zero-crossing pair
) -> int:
    """Persist one complete evaluation to the database. Returns the new test.id."""
    db = SessionLocal()
    try:
        test = Test(
            file_name=file_name, data_type=data_type,
            filter_window=int(filter_window) if filter_window is not None else None,
            static_range=static_range, dynamic_min=dynamic_min, dynamic_max=dynamic_max,
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
            _records = [
                {
                    "test_id": test.id, "crossing_index": int(idx),
                    "minus_min_time": _clean(row.get("-Min Zeit")),
                    "minus_min_cof": _clean(row.get("-Min CoF")),
                    "plus_min_time": _clean(row.get("+Min Zeit")),
                    "plus_min_cof": _clean(row.get("+Min CoF")),
                    "min_time": _clean(row.get("Min Zeit")),
                    "min_cof": _clean(row.get("Min CoF")),
                }
                for idx, row in minima_df.iterrows()
            ]
            db.bulk_insert_mappings(Minima, _records)

        if raw_df is not None and not raw_df.empty:
            _times = raw_df["Zeit"].tolist()
            _cofs = raw_df["CoF"].tolist()
            _has_filtered = "Filtered CoF" in raw_df.columns
            _filtered = raw_df["Filtered CoF"].tolist() if _has_filtered else [None] * len(raw_df)
            _records = [
                {
                    "test_id": test.id, "row_index": i,
                    "time": _clean(t), "cof": _clean(c),
                    "filtered_cof": _clean(f) if _has_filtered else None,
                }
                for i, (t, c, f) in enumerate(zip(_times, _cofs, _filtered))
            ]
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
            row = {
                "id": t.id,
                "file_name": t.file_name,
                "data_type": t.data_type,
                "uploaded_at": t.uploaded_at,
                "filter_window": t.filter_window,
                "static_range": t.static_range,
                "dynamic_min": t.dynamic_min,
                "dynamic_max": t.dynamic_max,
            }
            if t.results:
                _r = t.results[0]
                row["static_mean_cof"] = _r.static_mean_cof
                row["dynamic_mean_cof"] = _r.dynamic_mean_cof
                row["steps"] = len(t.results)
            else:
                row["static_mean_cof"] = None
                row["dynamic_mean_cof"] = None
                row["steps"] = 0
            out.append(row)
        return out
    finally:
        db.close()


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
        return [
            {
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
            }
            for r in rows
        ]
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
        return [
            {
                "crossing_index": r.crossing_index,
                "minus_min_time": r.minus_min_time,
                "minus_min_cof": r.minus_min_cof,
                "plus_min_time": r.plus_min_time,
                "plus_min_cof": r.plus_min_cof,
                "min_time": r.min_time,
                "min_cof": r.min_cof,
            }
            for r in rows
        ]
    finally:
        db.close()


def get_full_table(test_id: int):
    """Reconstruct the exact CoF Analysis results table for a saved test —
    same columns, same padding, as app.py's results_panel builds live."""
    import numpy as np
    import pandas as pd

    db = SessionLocal()
    try:
        raw = (
            db.query(RawSample).filter(RawSample.test_id == test_id)
            .order_by(RawSample.row_index).all()
        )
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

    n = max(len(raw), len(cycles), len(results), len(mins))

    def _pad(values):
        return list(values) + [np.nan] * (n - len(values))

    cols = {}
    if raw:
        cols["Time [s]"] = _pad([r.time for r in raw])
        cols["CoF"] = _pad([r.cof for r in raw])
        if any(r.filtered_cof is not None for r in raw):
            cols["Filtered CoF"] = _pad([r.filtered_cof for r in raw])

    cols.update({
        "Static CoF time [s]":    _pad([c.static_cof_time for c in cycles]),
        "Static CoF":             _pad([c.static_cof for c in cycles]),
        "Dynamic CoF time [s]":   _pad([c.dynamic_cof_time for c in cycles]),
        "Dynamic CoF":            _pad([c.dynamic_cof for c in cycles]),
        "Dynamic std dev":        _pad([c.dynamic_sd for c in cycles]),
        "Dynamic N":              _pad([c.dynamic_n for c in cycles]),
        "Dynamic CoF sum":        _pad([c.dynamic_sigma for c in cycles]),
        "Dynamic CoF variance":   _pad([c.dynamic_variance for c in cycles]),
        "Time range [s]":         _pad([r.time_range for r in results]),
        "Static mean CoF":        _pad([r.static_mean_cof for r in results]),
        "Static std dev":         _pad([r.static_sd for r in results]),
        "Static N":               _pad([r.static_n for r in results]),
        "Static CoF sum":         _pad([r.static_sum for r in results]),
        "Static CoF variance":    _pad([r.static_variance for r in results]),
        "Dynamic mean CoF":       _pad([r.dynamic_mean_cof for r in results]),
        "Dynamic mean std dev":   _pad([r.dynamic_sd for r in results]),
        "Dynamic mean N":         _pad([r.dynamic_n for r in results]),
        "Dynamic CoF avg×N":      _pad([r.dynamic_sum for r in results]),
        "Dynamic CoF var (step)": _pad([r.dynamic_variance for r in results]),
        "-Min time [s]":          _pad([m.minus_min_time for m in mins]),
        "-Min CoF":               _pad([m.minus_min_cof for m in mins]),
        "+Min time [s]":          _pad([m.plus_min_time for m in mins]),
        "+Min CoF":               _pad([m.plus_min_cof for m in mins]),
        "Min time [s]":           _pad([m.min_time for m in mins]),
        "CoF minima":             _pad([m.min_cof for m in mins]),
        "Dynamic start time [s]": _pad([c.start_dynamic_time for c in cycles]),
        "Dynamic start CoF":      _pad([c.start_dynamic_cof for c in cycles]),
        "Dynamic end time [s]":   _pad([c.end_dynamic_time for c in cycles]),
        "Dynamic end CoF":        _pad([c.end_dynamic_cof for c in cycles]),
    })
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
