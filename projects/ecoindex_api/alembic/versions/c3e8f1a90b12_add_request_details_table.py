"""Add request details table

Revision ID: c3e8f1a90b12
Revises: 5afa2faea43f
Create Date: 2026-08-17 10:30:00.000000

"""
import sqlalchemy as sa
import sqlmodel
from alembic import op
from ecoindex.database.helper import index_exists, table_exists

revision = "c3e8f1a90b12"
down_revision = "5afa2faea43f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if not table_exists(op.get_bind(), "apiecoindexrequest"):
        op.create_table(
            "apiecoindexrequest",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("analysis_id", sa.Uuid(), nullable=False),
            sa.Column("category", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column("domain", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column("status", sa.Integer(), nullable=False),
            sa.Column("url", sa.Text(), nullable=False),
            sa.Column("size", sa.Float(), nullable=False),
            sa.ForeignKeyConstraint(
                ["analysis_id"],
                ["apiecoindex.id"],
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
        )

    if not index_exists(
        op.get_bind(), "apiecoindexrequest", "ix_apiecoindexrequest_analysis_id"
    ):
        op.create_index(
            op.f("ix_apiecoindexrequest_analysis_id"),
            "apiecoindexrequest",
            ["analysis_id"],
            unique=False,
        )


def downgrade() -> None:
    if index_exists(
        op.get_bind(), "apiecoindexrequest", "ix_apiecoindexrequest_analysis_id"
    ):
        op.drop_index(
            op.f("ix_apiecoindexrequest_analysis_id"),
            table_name="apiecoindexrequest",
        )

    if table_exists(op.get_bind(), "apiecoindexrequest"):
        op.drop_table("apiecoindexrequest")
