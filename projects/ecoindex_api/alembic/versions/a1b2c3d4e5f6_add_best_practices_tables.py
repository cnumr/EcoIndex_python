"""Add best practices catalog and results tables

Revision ID: a1b2c3d4e5f6
Revises: c3e8f1a90b12
Create Date: 2026-10-02 13:20:00.000000

"""

import sqlalchemy as sa
import sqlmodel
from alembic import op
from ecoindex.database.helper import index_exists, table_exists

revision = "a1b2c3d4e5f6"
down_revision = "c3e8f1a90b12"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if not table_exists(op.get_bind(), "apiecoindexbestpractices"):
        op.create_table(
            "apiecoindexbestpractices",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("rule_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column("rweb_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
            sa.Column("category", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column("title", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column(
                "description",
                sa.Text(),
                nullable=False,
                server_default="",
            ),
            sa.Column("url", sa.Text(), nullable=True),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("threshold_warn", sa.Float(), nullable=True),
            sa.Column("threshold_fail", sa.Float(), nullable=True),
            sa.Column(
                "higher_is_worse",
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "rule_id", name="uq_apiecoindexbestpractices_rule_id"
            ),
        )

    if not index_exists(
        op.get_bind(), "apiecoindexbestpractices", "ix_apiecoindexbestpractices_rule_id"
    ):
        op.create_index(
            op.f("ix_apiecoindexbestpractices_rule_id"),
            "apiecoindexbestpractices",
            ["rule_id"],
            unique=False,
        )

    if not table_exists(op.get_bind(), "apiecoindexbestpracticeresults"):
        op.create_table(
            "apiecoindexbestpracticeresults",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("analysis_id", sa.Uuid(), nullable=False),
            sa.Column("best_practice_id", sa.Uuid(), nullable=False),
            sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column("value", sa.Float(), nullable=False),
            sa.Column("threshold_warn", sa.Float(), nullable=True),
            sa.Column("threshold_fail", sa.Float(), nullable=True),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("details", sa.JSON(), nullable=False),
            sa.ForeignKeyConstraint(
                ["analysis_id"],
                ["apiecoindex.id"],
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["best_practice_id"],
                ["apiecoindexbestpractices.id"],
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "analysis_id",
                "best_practice_id",
                name="uq_apiecoindexbestpracticeresults_analysis_practice",
            ),
        )

    if not index_exists(
        op.get_bind(),
        "apiecoindexbestpracticeresults",
        "ix_apiecoindexbestpracticeresults_analysis_id",
    ):
        op.create_index(
            op.f("ix_apiecoindexbestpracticeresults_analysis_id"),
            "apiecoindexbestpracticeresults",
            ["analysis_id"],
            unique=False,
        )

    if not index_exists(
        op.get_bind(),
        "apiecoindexbestpracticeresults",
        "ix_apiecoindexbestpracticeresults_best_practice_id",
    ):
        op.create_index(
            op.f("ix_apiecoindexbestpracticeresults_best_practice_id"),
            "apiecoindexbestpracticeresults",
            ["best_practice_id"],
            unique=False,
        )


def downgrade() -> None:
    if index_exists(
        op.get_bind(),
        "apiecoindexbestpracticeresults",
        "ix_apiecoindexbestpracticeresults_best_practice_id",
    ):
        op.drop_index(
            op.f("ix_apiecoindexbestpracticeresults_best_practice_id"),
            table_name="apiecoindexbestpracticeresults",
        )

    if index_exists(
        op.get_bind(),
        "apiecoindexbestpracticeresults",
        "ix_apiecoindexbestpracticeresults_analysis_id",
    ):
        op.drop_index(
            op.f("ix_apiecoindexbestpracticeresults_analysis_id"),
            table_name="apiecoindexbestpracticeresults",
        )

    if table_exists(op.get_bind(), "apiecoindexbestpracticeresults"):
        op.drop_table("apiecoindexbestpracticeresults")

    if index_exists(
        op.get_bind(), "apiecoindexbestpractices", "ix_apiecoindexbestpractices_rule_id"
    ):
        op.drop_index(
            op.f("ix_apiecoindexbestpractices_rule_id"),
            table_name="apiecoindexbestpractices",
        )

    if table_exists(op.get_bind(), "apiecoindexbestpractices"):
        op.drop_table("apiecoindexbestpractices")
