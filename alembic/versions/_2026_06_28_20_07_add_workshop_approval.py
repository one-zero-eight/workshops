"""add workshop approval

Revision ID: 1a7f8cf03d2b
Revises: 20dcf337bb3e
Create Date: 2026-06-28 19:56:52.457423

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1a7f8cf03d2b"
down_revision: str | None = "20dcf337bb3e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "workshops",
        sa.Column("is_approved", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("workshops", "is_approved")
