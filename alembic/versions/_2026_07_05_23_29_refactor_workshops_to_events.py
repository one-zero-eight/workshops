"""refactor workshops to events

Revision ID: 341b543d4dd8
Revises: 1a7f8cf03d2b
Create Date: 2026-07-05 23:29:07.905946

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "341b543d4dd8"
down_revision: str | None = "1a7f8cf03d2b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Rename tables
    op.rename_table("workshops", "events")
    op.rename_table("workshopcheckin", "event_registrations")

    # Rename indexes and primary keys
    op.execute("ALTER INDEX ix_workshops_id RENAME TO ix_events_id")
    op.execute("ALTER INDEX ix_workshops_english_name RENAME TO ix_events_english_name")
    op.execute("ALTER INDEX ix_workshops_russian_name RENAME TO ix_events_russian_name")
    op.execute("ALTER INDEX workshops_pkey RENAME TO events_pkey")
    op.execute("ALTER INDEX workshopcheckin_pkey RENAME TO event_registrations_pkey")

    # 2. Update event_registrations
    op.alter_column("event_registrations", "workshop_id", new_column_name="event_id")
    op.drop_constraint("workshopcheckin_workshop_id_fkey", "event_registrations", type_="foreignkey")
    op.drop_constraint("workshopcheckin_user_id_fkey", "event_registrations", type_="foreignkey")
    op.create_foreign_key(
        op.f("event_registrations_event_id_fkey"),
        "event_registrations",
        "events",
        ["event_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        op.f("event_registrations_user_id_fkey"),
        "event_registrations",
        "users",
        ["user_id"],
        ["innohassle_id"],
        ondelete="CASCADE",
    )

    # 3. Rename ENUM types
    op.execute("ALTER TYPE workshoplanguage RENAME TO eventlanguage")

    # 4. Create new ENUM and add new columns
    sa.Enum("DRAFT", "PENDING_REVIEW", "APPROVED", "REJECTED", name="eventstatus").create(op.get_bind())
    op.add_column(
        "events",
        sa.Column(
            "status",
            postgresql.ENUM("DRAFT", "PENDING_REVIEW", "APPROVED", "REJECTED", name="eventstatus", create_type=False),
            server_default="DRAFT",
            nullable=False,
        ),
    )
    op.add_column("events", sa.Column("created_by", sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.create_foreign_key(op.f("events_created_by_fkey"), "events", "users", ["created_by"], ["innohassle_id"])

    # 5. Data Migration
    op.execute("""
        UPDATE events
        SET status =
            CASE
                WHEN is_approved = true THEN 'APPROVED'::eventstatus
                WHEN is_draft = true THEN 'DRAFT'::eventstatus
                ELSE 'PENDING_REVIEW'::eventstatus
            END
    """)

    # 6. Drop old columns
    op.drop_column("events", "is_approved")
    op.drop_column("events", "is_draft")
    op.drop_column("events", "is_active")


def downgrade() -> None:
    """Downgrade schema."""
    # 1. Add back old columns
    op.add_column(
        "events",
        sa.Column("is_active", sa.BOOLEAN(), server_default=sa.text("true"), autoincrement=False, nullable=False),
    )
    op.add_column(
        "events",
        sa.Column("is_draft", sa.BOOLEAN(), server_default=sa.text("true"), autoincrement=False, nullable=False),
    )
    op.add_column(
        "events",
        sa.Column("is_approved", sa.BOOLEAN(), server_default=sa.text("false"), autoincrement=False, nullable=False),
    )

    # 2. Revert data
    op.execute("""
        UPDATE events
        SET
            is_approved = (status = 'APPROVED'::eventstatus),
            is_draft = (status = 'DRAFT'::eventstatus),
            is_active = (status = 'APPROVED'::eventstatus OR status = 'PENDING_REVIEW'::eventstatus)
    """)

    # 3. Drop new columns and ENUM
    op.drop_constraint(op.f("events_created_by_fkey"), "events", type_="foreignkey")
    op.drop_column("events", "created_by")
    op.drop_column("events", "status")
    sa.Enum("DRAFT", "PENDING_REVIEW", "APPROVED", "REJECTED", name="eventstatus").drop(op.get_bind())

    # 4. Revert ENUM rename
    op.execute("ALTER TYPE eventlanguage RENAME TO workshoplanguage")

    # 5. Revert event_registrations
    op.drop_constraint(op.f("event_registrations_event_id_fkey"), "event_registrations", type_="foreignkey")
    op.drop_constraint(op.f("event_registrations_user_id_fkey"), "event_registrations", type_="foreignkey")
    op.alter_column("event_registrations", "event_id", new_column_name="workshop_id")
    op.create_foreign_key(
        "workshopcheckin_workshop_id_fkey", "event_registrations", "events", ["workshop_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "workshopcheckin_user_id_fkey",
        "event_registrations",
        "users",
        ["user_id"],
        ["innohassle_id"],
        ondelete="CASCADE",
    )

    # 6. Rename indexes back
    op.execute("ALTER INDEX ix_events_id RENAME TO ix_workshops_id")
    op.execute("ALTER INDEX ix_events_english_name RENAME TO ix_workshops_english_name")
    op.execute("ALTER INDEX ix_events_russian_name RENAME TO ix_workshops_russian_name")
    op.execute("ALTER INDEX events_pkey RENAME TO workshops_pkey")
    op.execute("ALTER INDEX event_registrations_pkey RENAME TO workshopcheckin_pkey")

    # 7. Rename tables back
    op.rename_table("event_registrations", "workshopcheckin")
    op.rename_table("events", "workshops")
