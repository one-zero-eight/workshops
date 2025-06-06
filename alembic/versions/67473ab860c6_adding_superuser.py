"""adding superuser

Revision ID: 67473ab860c6
Revises: c9cb64c7e39f
Create Date: 2025-06-05 14:26:53.846668

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '67473ab860c6'
down_revision: Union[str, None] = 'c9cb64c7e39f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("UPDATE users SET role = 'admin' WHERE email = 'lol'")
    # sa.Column('role', sa.Enum('admin', 'user', name='userrole').with_variant(postgresql.ENUM('admin', 'user', name='userrole', create_type=False), "postgresql"), nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("UPDATE users SET role = 'user' WHERE email = 'lol'")
    pass
