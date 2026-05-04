"""Schema tests for SQLAlchemy ORM models."""

from __future__ import annotations

from sqlalchemy import inspect

from app.db import CalculationInput


def test_calculation_input_has_user_id_not_null() -> None:
    columns = {c.name: c for c in inspect(CalculationInput).columns}
    assert "user_id" in columns
    assert columns["user_id"].nullable is False
    assert columns["user_id"].type.length == 64  # type: ignore[attr-defined]
