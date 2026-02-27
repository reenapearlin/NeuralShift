"""add_scraped_cases_table

Revision ID: 9b3f4f2a1d10
Revises: 6dda79daab8b
Create Date: 2026-02-26 18:40:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9b3f4f2a1d10"
down_revision: Union[str, Sequence[str], None] = "6dda79daab8b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("scraped_cases"):
        return

    op.create_table(
        "scraped_cases",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("embeddings", sa.JSON(), nullable=True),
        sa.Column("scraped_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url"),
    )
    op.create_index("ix_scraped_cases_id", "scraped_cases", ["id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("scraped_cases"):
        return

    index_names = {item.get("name") for item in inspector.get_indexes("scraped_cases")}
    if "ix_scraped_cases_id" in index_names:
        op.drop_index("ix_scraped_cases_id", table_name="scraped_cases")
    op.drop_table("scraped_cases")
