"""Schema tests for SQLAlchemy ORM models."""

from __future__ import annotations

from sqlalchemy import inspect

from app.db import CalculationInput


def test_calculation_input_has_user_id_not_null() -> None:
    columns = {c.name: c for c in inspect(CalculationInput).columns}
    assert "user_id" in columns
    assert columns["user_id"].nullable is False
    assert columns["user_id"].type.length == 64  # type: ignore[attr-defined]


def test_calculation_input_has_q_column_with_zero_default() -> None:
    columns = {c.name: c for c in inspect(CalculationInput).columns}
    assert "q" in columns
    assert columns["q"].nullable is False
    server_default = columns["q"].server_default
    assert server_default is not None
    assert "0" in str(server_default.arg)


def test_calculation_input_q_round_trips() -> None:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    from app.db import Base

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False, future=True)

    with factory() as session:
        record = CalculationInput(
            id="00000000-0000-0000-0000-000000000001",
            s=100.0,
            k=100.0,
            t=1.0,
            r=0.05,
            sigma=0.20,
            q=0.03,
            vol_shock_min=-0.5,
            vol_shock_max=0.5,
            spot_shock_min=-0.2,
            spot_shock_max=0.2,
            rows=5,
            cols=5,
            user_id="auth0|test",
        )
        session.add(record)
        session.commit()
        loaded = session.get(CalculationInput, "00000000-0000-0000-0000-000000000001")
        assert loaded is not None
        assert loaded.q == 0.03

    engine.dispose()


def test_calculation_input_q_defaults_to_zero_at_db_level() -> None:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    from app.db import Base

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False, future=True)

    with factory() as session:
        session.execute(
            text(
                "INSERT INTO calculation_inputs "
                "(id, s, k, t, r, sigma, vol_shock_min, vol_shock_max, "
                "spot_shock_min, spot_shock_max, rows, cols, user_id) "
                "VALUES (:id, 100, 100, 1, 0.05, 0.2, -0.5, 0.5, -0.2, 0.2, 5, 5, 'u1')"
            ),
            {"id": "00000000-0000-0000-0000-000000000002"},
        )
        session.commit()
        loaded = session.get(CalculationInput, "00000000-0000-0000-0000-000000000002")
        assert loaded is not None
        assert loaded.q == 0.0

    engine.dispose()
