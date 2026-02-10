"""make host a list of Host objects

Revision ID: 55b046067d40
Revises: 17e3c4626f87
Create Date: 2026-02-10 21:25:20.457255

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "55b046067d40"
down_revision: str | None = "17e3c4626f87"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "workshops",
        sa.Column("host_new", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    connection = op.get_bind()
    connection.execute(
        sa.text("""
                UPDATE workshops
                SET host_new = jsonb_build_array(
                        jsonb_build_object(
                                'host_type', 'other',
                                'name', COALESCE(host, '')
                        )
                               )
                WHERE host IS NOT NULL
                  AND host != ''
                """)
    )

    connection.execute(
        sa.text("""
                UPDATE workshops
                SET host_new = '[]'::jsonb
                WHERE host IS NULL
                   OR host = ''
                """)
    )

    op.drop_column("workshops", "host")
    op.alter_column("workshops", "host_new", new_column_name="host", nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        "workshops",
        sa.Column("host_old", sa.VARCHAR(), nullable=True),
    )

    connection = op.get_bind()
    connection.execute(
        sa.text("""
                UPDATE workshops
                SET host_old = (SELECT name
                                FROM jsonb_to_recordset(host) AS x(host_type text, name text)
                                WHERE host_type = 'club'
                                LIMIT 1)
                WHERE jsonb_array_length(host) > 0
                """)
    )

    connection.execute(
        sa.text("""
                UPDATE workshops
                SET host_old = host -> 0 ->> 'name'
                WHERE host_old IS NULL
                  AND jsonb_array_length(host) > 0
                """)
    )

    # Drop new column and rename old one
    op.drop_column("workshops", "host")
    op.alter_column("workshops", "host_old", new_column_name="host", nullable=True)
