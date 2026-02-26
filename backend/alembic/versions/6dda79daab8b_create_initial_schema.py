"""create_initial_schema

Revision ID: 6dda79daab8b
Revises:
Create Date: 2026-02-25 23:11:29.560697

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6dda79daab8b"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


user_role_enum = sa.Enum("ADMIN", "LAWYER", name="user_role_enum")
case_status_enum = sa.Enum("PENDING", "APPROVED", "REJECTED", name="case_status_enum")


def upgrade() -> None:
    bind = op.get_bind()
    user_role_enum.create(bind, checkfirst=True)
    case_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", user_role_enum, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_id", "users", ["id"], unique=False)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "casefiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("case_title", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("status", case_status_enum, nullable=False),
        sa.Column("uploaded_by", sa.Integer(), nullable=False),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_casefiles_id", "casefiles", ["id"], unique=False)

    op.create_table(
        "metadata",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("casefile_id", sa.Integer(), nullable=False),
        sa.Column("meta_key", sa.String(length=100), nullable=False),
        sa.Column("meta_value", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["casefile_id"], ["casefiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_metadata_id", "metadata", ["id"], unique=False)
    op.create_index("ix_metadata_casefile_id", "metadata", ["casefile_id"], unique=False)

    op.create_table(
        "search_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("casefile_id", sa.Integer(), nullable=True),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("response_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["casefile_id"], ["casefiles.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_search_logs_id", "search_logs", ["id"], unique=False)
    op.create_index("ix_search_logs_user_id", "search_logs", ["user_id"], unique=False)
    op.create_index("ix_search_logs_casefile_id", "search_logs", ["casefile_id"], unique=False)

    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("casefile_id", sa.Integer(), nullable=False),
        sa.Column("generated_by", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["casefile_id"], ["casefiles.id"]),
        sa.ForeignKeyConstraint(["generated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reports_id", "reports", ["id"], unique=False)
    op.create_index("ix_reports_casefile_id", "reports", ["casefile_id"], unique=False)
    op.create_index("ix_reports_generated_by", "reports", ["generated_by"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_reports_generated_by", table_name="reports")
    op.drop_index("ix_reports_casefile_id", table_name="reports")
    op.drop_index("ix_reports_id", table_name="reports")
    op.drop_table("reports")

    op.drop_index("ix_search_logs_casefile_id", table_name="search_logs")
    op.drop_index("ix_search_logs_user_id", table_name="search_logs")
    op.drop_index("ix_search_logs_id", table_name="search_logs")
    op.drop_table("search_logs")

    op.drop_index("ix_metadata_casefile_id", table_name="metadata")
    op.drop_index("ix_metadata_id", table_name="metadata")
    op.drop_table("metadata")

    op.drop_index("ix_casefiles_id", table_name="casefiles")
    op.drop_table("casefiles")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")

    bind = op.get_bind()
    case_status_enum.drop(bind, checkfirst=True)
    user_role_enum.drop(bind, checkfirst=True)
