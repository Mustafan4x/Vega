"""add q to calculation_inputs

Revision ID: c6ca2f3c271c
Revises: 3c1e7a3e9d78
Create Date: 2026-05-05 00:06:08.238707

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c6ca2f3c271c"
down_revision: str | Sequence[str] | None = "3c1e7a3e9d78"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "calculation_inputs",
        sa.Column("q", sa.Float(), server_default="0.0", nullable=False),
    )


def downgrade() -> None:
    with op.batch_alter_table("calculation_inputs") as batch_op:
        batch_op.drop_column("q")
