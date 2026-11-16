"""Ensure category names are unique.

Revision ID: c83f8414296f
Revises: b52894278bbe
"""
from alembic import op

revision = "c83f8414296f"
down_revision = "b52894278bbe"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint("uq_categories_name", "categories", ["name"])


def downgrade() -> None:
    op.drop_constraint("uq_categories_name", "categories", type_="unique")
