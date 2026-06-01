"""
Persistent storage for friction test results.

One SQLite file (tribology.db) is created next to main.py when the
backend starts. Three tables:

  tests      — one row per uploaded + evaluated file (metadata + params)
  results    — one aggregate row per test (or per step for SRV_FSA)
  per_cycle  — one row per cycle (for future ML / AI training)
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from sqlalchemy import (
    Column, DateTime, Float, ForeignKey, Integer, String, Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

DATABASE_URL = f"sqlite:///{Path(__file__).parent / 'tribology.db'}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------

class Test(Base):
    """One row per evaluated test file."""
    __tablename__ = "tests"

    id            = Column(Integer, primary_key=True, index=True)
    file_name     = Column(Text,    nullable=False)
    data_type     = Column(String,  nullable=False)          # OFT / SRV / SRV_FSA
    uploaded_at   = Column(DateTime, default=datetime.utcnow)

    # Parameters used for this evaluation
    filter_window = Column(Integer)
    static_range  = Column(Float)
    dynamic_min   = Column(Float)
    dynamic_max   = Column(Float)

    results   = relationship("Result",   back_populates="test",
                             cascade="all, delete-orphan")
    per_cycle = relationship("PerCycle", back_populates="test",
                             cascade="all, delete-orphan")


class Result(Base):
    """
    Aggregate statistics — one row per active step (SRV_FSA) or
    one row for the whole test (OFT / SRV).
    """
    __tablename__ = "results"

    id               = Column(Integer, primary_key=True)
    test_id          = Column(Integer, ForeignKey("tests.id"), nullable=False)

    time_range       = Column(Float)    # seconds

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
    """
    Per-cycle data — one row per friction cycle.
    This is the training data for future ML / AI models.
    """
    __tablename__ = "per_cycle"

    id          = Column(Integer, primary_key=True)
    test_id     = Column(Integer, ForeignKey("tests.id"), nullable=False)
    cycle_index = Column(Integer)

    static_cof_time = Column(Float)
    static_cof      = Column(Float)

    dynamic_cof_time = Column(Float)
    dynamic_cof      = Column(Float)
    dynamic_sd       = Column(Float)
    dynamic_n        = Column(Integer)
    dynamic_sigma    = Column(Float)
    dynamic_variance = Column(Float)

    test = relationship("Test", back_populates="per_cycle")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def create_tables() -> None:
    """Create all tables if they do not exist yet. Called on app startup."""
    Base.metadata.create_all(bind=engine)


def save_evaluation(
    file_name:     str,
    data_type:     str,
    filter_window: int,
    static_range:  float,
    dynamic_min:   float,
    dynamic_max:   float,
    agg:           dict,
    per_cycle_df,          # pandas DataFrame from cof_evaluate
    step_stats_df=None,    # pandas DataFrame from CoF_Discontstatistics (SRV_FSA)
) -> int:
    """
    Persist one complete evaluation to the database.

    Returns the new test.id so the caller can log or display it.
    """
    import math

    def _clean(v):
        """Convert NaN / inf to None so SQLite accepts it."""
        try:
            return None if (v is None or math.isnan(float(v)) or math.isinf(float(v))) else float(v)
        except (TypeError, ValueError):
            return None

    db = SessionLocal()
    try:
        # ---- Test row -------------------------------------------------------
        test = Test(
            file_name     = file_name,
            data_type     = data_type,
            filter_window = filter_window,
            static_range  = static_range,
            dynamic_min   = dynamic_min,
            dynamic_max   = dynamic_max,
        )
        db.add(test)
        db.flush()   # populate test.id before adding children

        # ---- Result row(s) --------------------------------------------------
        if step_stats_df is not None and not step_stats_df.empty:
            # SRV_FSA: one Result row per active step
            for _, row in step_stats_df.iterrows():
                db.add(Result(
                    test_id          = test.id,
                    static_mean_cof  = _clean(row.get("Static Avg")),
                    static_sd        = _clean(row.get("Static Std Dev")),
                    static_n         = _clean(row.get("Static N")),
                    static_sum       = _clean(row.get("Static Avg x N")),
                    static_variance  = _clean(row.get("Static Var")),
                    dynamic_mean_cof = _clean(row.get("Dynamic Avg")),
                    dynamic_sd       = _clean(row.get("Dynamic Std Dev")),
                    dynamic_n        = _clean(row.get("Dynamic N")),
                    dynamic_sum      = _clean(row.get("Dynamic Avg x N")),
                    dynamic_variance = _clean(row.get("Dynamic Var")),
                ))
        else:
            # OFT / SRV: single aggregate row
            db.add(Result(
                test_id          = test.id,
                time_range       = _clean(agg.get("timeRange")),
                static_mean_cof  = _clean(agg.get("staticMeanCoF")),
                static_sd        = _clean(agg.get("staticCoFSD_agg")),
                static_n         = _clean(agg.get("staticCoFN_agg")),
                static_sum       = _clean(agg.get("staticCoFSum_agg")),
                static_variance  = _clean(agg.get("staticCoFVar_agg")),
                dynamic_mean_cof = _clean(agg.get("dynamicMeanCoF")),
                dynamic_sd       = _clean(agg.get("dynamicCoFSD_agg")),
                dynamic_n        = _clean(agg.get("dynamicCoFN_agg")),
                dynamic_sum      = _clean(agg.get("dynamicCoFSum_agg")),
                dynamic_variance = _clean(agg.get("dynamicCoFVar_agg")),
            ))

        # ---- PerCycle rows --------------------------------------------------
        for idx, row in per_cycle_df.iterrows():
            db.add(PerCycle(
                test_id          = test.id,
                cycle_index      = int(idx),
                static_cof_time  = _clean(row.get("staticCoFTime")),
                static_cof       = _clean(row.get("staticCoF")),
                dynamic_cof_time = _clean(row.get("dynamicCoFTime")),
                dynamic_cof      = _clean(row.get("dynamicCoF")),
                dynamic_sd       = _clean(row.get("dynamicCoFSD")),
                dynamic_n        = _clean(row.get("dynamicCoFn")),
                dynamic_sigma    = _clean(row.get("dynamicCoFsigma")),
                dynamic_variance = _clean(row.get("dynamicCoFvariance")),
            ))

        db.commit()
        return test.id

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
