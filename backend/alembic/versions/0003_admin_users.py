"""Add the server-managed administrator allowlist.

Revision ID: 0003_admin_users
Revises: 0002_supabase_rls
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID


revision: str = "0003_admin_users"
down_revision: Union[str, Sequence[str], None] = "0002_supabase_rls"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "admin_users",
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    # No policies are intentional: authenticated clients receive no access.
    op.execute("ALTER TABLE public.admin_users ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.execute("ALTER TABLE public.admin_users DISABLE ROW LEVEL SECURITY")
    op.drop_table("admin_users")
