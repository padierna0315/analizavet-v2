"""add_raw_data_log_table

Revision ID: 7a1b2c3d4e5f
Revises: 57ba68ffb5ff
Create Date: 2026-05-17 06:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "7a1b2c3d4e5f"
down_revision: Union[str, None] = "57ba68ffb5ff"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "rawdatalog",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("raw_data", sa.Text(), nullable=False),
        sa.Column("received_at", sa.DateTime(), nullable=False),
        sa.Column("captured_at", sa.DateTime(), nullable=False),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.Column(
            "patient_id",
            sa.Integer(),
            sa.ForeignKey("patient.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "test_result_id",
            sa.Integer(),
            sa.ForeignKey("testresult.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "session_code", sqlmodel.sql.sqltypes.AutoString(), nullable=True
        ),
        sa.Column(
            "status",
            sqlmodel.sql.sqltypes.AutoString(),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_rawdatalog_patient_id", "rawdatalog", ["patient_id"], unique=False
    )
    op.create_index(
        "ix_rawdatalog_test_result_id",
        "rawdatalog",
        ["test_result_id"],
        unique=False,
    )
    op.create_index(
        "ix_rawdatalog_session_code",
        "rawdatalog",
        ["session_code"],
        unique=False,
    )
    op.create_index(
        "ix_rawdatalog_source", "rawdatalog", ["source"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_rawdatalog_source", table_name="rawdatalog")
    op.drop_index("ix_rawdatalog_session_code", table_name="rawdatalog")
    op.drop_index("ix_rawdatalog_test_result_id", table_name="rawdatalog")
    op.drop_index("ix_rawdatalog_patient_id", table_name="rawdatalog")
    op.drop_table("rawdatalog")
