"""SQLAlchemy 2.x typed declarative models for calculation persistence.

Two tables, linked by ``calculation_id`` (UUID):

* ``calculation_inputs`` holds the request parameters of one heat map
  computation. One row per ``POST /api/calculations`` call.
* ``calculation_outputs`` holds the cells of the resulting grid. One
  row per cell (``rows`` x ``cols`` rows per calculation).

All queries use ORM relationships or parameterized SQL. Manual string
formatting of SQL is forbidden by the threat model (T1).
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

if TYPE_CHECKING:
    pass


class Base(DeclarativeBase):
    pass


class CalculationInput(Base):
    __tablename__ = "calculation_inputs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    s: Mapped[float] = mapped_column(Float, nullable=False)
    k: Mapped[float] = mapped_column(Float, nullable=False)
    t: Mapped[float] = mapped_column(Float, nullable=False)
    r: Mapped[float] = mapped_column(Float, nullable=False)
    sigma: Mapped[float] = mapped_column(Float, nullable=False)
    vol_shock_min: Mapped[float] = mapped_column(Float, nullable=False)
    vol_shock_max: Mapped[float] = mapped_column(Float, nullable=False)
    spot_shock_min: Mapped[float] = mapped_column(Float, nullable=False)
    spot_shock_max: Mapped[float] = mapped_column(Float, nullable=False)
    rows: Mapped[int] = mapped_column(Integer, nullable=False)
    cols: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    outputs: Mapped[list[CalculationOutput]] = relationship(
        back_populates="calculation",
        cascade="all, delete-orphan",
        order_by="CalculationOutput.row_index, CalculationOutput.col_index",
    )


class CalculationOutput(Base):
    __tablename__ = "calculation_outputs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    calculation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("calculation_inputs.id", ondelete="CASCADE"),
        nullable=False,
    )
    row_index: Mapped[int] = mapped_column(Integer, nullable=False)
    col_index: Mapped[int] = mapped_column(Integer, nullable=False)
    sigma_value: Mapped[float] = mapped_column(Float, nullable=False)
    spot_value: Mapped[float] = mapped_column(Float, nullable=False)
    call_value: Mapped[float] = mapped_column(Float, nullable=False)
    put_value: Mapped[float] = mapped_column(Float, nullable=False)

    calculation: Mapped[CalculationInput] = relationship(back_populates="outputs")

    __table_args__ = (
        Index(
            "ix_calculation_outputs_calculation_id",
            "calculation_id",
        ),
    )
