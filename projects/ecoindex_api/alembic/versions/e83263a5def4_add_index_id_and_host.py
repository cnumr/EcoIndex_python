"""Add index ID and host

Revision ID: e83263a5def4
Revises: 826abb0c4222
Create Date: 2023-02-13 15:58:55.102285

"""
import sqlalchemy as sa
import sqlmodel  # noqa: F401
from alembic import op
from ecoindex.database.helper import index_exists

# revision identifiers, used by Alembic.
revision = "e83263a5def4"
down_revision = "826abb0c4222"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("apiecoindex", schema=None) as batch_op:
        batch_op.alter_column(
            "id",
            existing_type=sa.Uuid(),
            nullable=False,
        )
        batch_op.alter_column("version", existing_type=sa.INTEGER(), nullable=False)

    if not index_exists(op.get_bind(), "apiecoindex", "ix_apiecoindex_id"):
        op.create_index(op.f("ix_apiecoindex_id"), "apiecoindex", ["id"], unique=False)

    if not index_exists(op.get_bind(), "apiecoindex", "ix_apiecoindex_host"):
        op.create_index(
            op.f("ix_apiecoindex_host"), "apiecoindex", ["host"], unique=False
        )


def downgrade() -> None:
    if index_exists(op.get_bind(), "apiecoindex", "ix_apiecoindex_host"):
        op.drop_index(op.f("ix_apiecoindex_host"), table_name="apiecoindex")

    if index_exists(op.get_bind(), "apiecoindex", "ix_apiecoindex_id"):
        op.drop_index(op.f("ix_apiecoindex_id"), table_name="apiecoindex")

    with op.batch_alter_table("apiecoindex", schema=None) as batch_op:
        batch_op.alter_column("version", existing_type=sa.INTEGER(), nullable=True)
        batch_op.alter_column(
            "id",
            existing_type=sa.Uuid(),
            nullable=True,
        )
