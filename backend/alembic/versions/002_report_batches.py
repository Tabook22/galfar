"""Add report batches for multi-report analysis

Revision ID: 002
Revises: 001
Create Date: 2026-06-26

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(name: str) -> bool:
    return name in inspect(op.get_bind()).get_table_names()


def _column_exists(table: str, column: str) -> bool:
    if not _table_exists(table):
        return False
    return column in {col["name"] for col in inspect(op.get_bind()).get_columns(table)}


def upgrade() -> None:
    if not _table_exists("report_batches"):
        op.create_table(
            "report_batches",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("status", sa.String(length=50), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_report_batches_id"), "report_batches", ["id"], unique=False)

    if _table_exists("reports") and not _column_exists("reports", "batch_id"):
        op.add_column("reports", sa.Column("batch_id", sa.Integer(), nullable=True))
        op.create_index(op.f("ix_reports_batch_id"), "reports", ["batch_id"], unique=False)
        if op.get_bind().dialect.name != "sqlite":
            op.create_foreign_key(
                "fk_reports_batch_id", "reports", "report_batches", ["batch_id"], ["id"], ondelete="SET NULL"
            )

    if not _table_exists("batch_analyses"):
        op.create_table(
            "batch_analyses",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("batch_id", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=50), nullable=False),
            sa.Column("report_count", sa.Integer(), nullable=False),
            sa.Column("summary", sa.Text(), nullable=True),
            sa.Column("revenue", sa.Text(), nullable=True),
            sa.Column("expenses", sa.Text(), nullable=True),
            sa.Column("profit_loss", sa.Text(), nullable=True),
            sa.Column("cash_flow", sa.Text(), nullable=True),
            sa.Column("assets", sa.Text(), nullable=True),
            sa.Column("liabilities", sa.Text(), nullable=True),
            sa.Column("risks", sa.Text(), nullable=True),
            sa.Column("strengths", sa.Text(), nullable=True),
            sa.Column("weaknesses", sa.Text(), nullable=True),
            sa.Column("recommendations", sa.Text(), nullable=True),
            sa.Column("raw_result", sa.Text(), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["batch_id"], ["report_batches.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_batch_analyses_id"), "batch_analyses", ["id"], unique=False)

    if not _table_exists("batch_chat_messages"):
        op.create_table(
            "batch_chat_messages",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("batch_id", sa.Integer(), nullable=False),
            sa.Column("role", sa.String(length=20), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["batch_id"], ["report_batches.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_batch_chat_messages_id"), "batch_chat_messages", ["id"], unique=False)


def downgrade() -> None:
    if _table_exists("batch_chat_messages"):
        op.drop_index(op.f("ix_batch_chat_messages_id"), table_name="batch_chat_messages")
        op.drop_table("batch_chat_messages")
    if _table_exists("batch_analyses"):
        op.drop_index(op.f("ix_batch_analyses_id"), table_name="batch_analyses")
        op.drop_table("batch_analyses")
    if _column_exists("reports", "batch_id"):
        op.drop_constraint("fk_reports_batch_id", "reports", type_="foreignkey")
        op.drop_index(op.f("ix_reports_batch_id"), table_name="reports")
        op.drop_column("reports", "batch_id")
    if _table_exists("report_batches"):
        op.drop_index(op.f("ix_report_batches_id"), table_name="report_batches")
        op.drop_table("report_batches")
