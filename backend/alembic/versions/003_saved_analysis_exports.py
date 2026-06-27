"""Add saved analysis exports

Revision ID: 003
Revises: 002
Create Date: 2026-06-27

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(name: str) -> bool:
    return name in inspect(op.get_bind()).get_table_names()


def upgrade() -> None:
    if not _table_exists("saved_analysis_exports"):
        op.create_table(
            "saved_analysis_exports",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("filename", sa.String(length=255), nullable=False),
            sa.Column("file_path", sa.String(length=512), nullable=False),
            sa.Column("source_type", sa.String(length=20), nullable=False),
            sa.Column("source_name", sa.String(length=255), nullable=False),
            sa.Column("report_id", sa.Integer(), nullable=True),
            sa.Column("batch_id", sa.Integer(), nullable=True),
            sa.Column("analysis_id", sa.Integer(), nullable=True),
            sa.Column("batch_analysis_id", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["batch_analysis_id"], ["batch_analyses.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["batch_id"], ["report_batches.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["report_id"], ["reports.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_saved_analysis_exports_id"), "saved_analysis_exports", ["id"], unique=False
        )


def downgrade() -> None:
    if _table_exists("saved_analysis_exports"):
        op.drop_index(op.f("ix_saved_analysis_exports_id"), table_name="saved_analysis_exports")
        op.drop_table("saved_analysis_exports")
