"""phase12 user_id and per user index

Revision ID: 3c1e7a3e9d78
Revises: 9c8f64a81798
Create Date: 2026-05-04 10:50:18.990969

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3c1e7a3e9d78"
down_revision: str | Sequence[str] | None = "9c8f64a81798"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("TRUNCATE TABLE calculation_outputs, calculation_inputs CASCADE")
    else:
        op.execute("DELETE FROM calculation_outputs")
        op.execute("DELETE FROM calculation_inputs")

    op.add_column(
        "calculation_inputs",
        sa.Column("user_id", sa.String(length=64), nullable=False),
    )
    op.create_index(
        "ix_calculation_inputs_user_id_created_at",
        "calculation_inputs",
        ["user_id", sa.text("created_at DESC")],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_calculation_inputs_user_id_created_at",
        table_name="calculation_inputs",
    )
    op.drop_column("calculation_inputs", "user_id")
