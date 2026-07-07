"""

Revision ID: 5afa2faea43f
Revises: 7eaafaa65b32
Create Date: 2025-01-14 14:12:47.013413

"""
import sqlalchemy as sa
import sqlmodel
from alembic import op
from ecoindex.database.helper import column_exists

revision = "5afa2faea43f"
down_revision = "7eaafaa65b32"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if not column_exists(op.get_bind(), "apiecoindex", "source"):
        op.add_column(
            "apiecoindex",
            sa.Column("source", sqlmodel.sql.sqltypes.AutoString(), nullable=True),  # type: ignore
        )


def downgrade() -> None:
    if column_exists(op.get_bind(), "apiecoindex", "source"):
        op.drop_column("apiecoindex", "source")
