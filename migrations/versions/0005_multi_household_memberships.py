"""allow users to belong to several households

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-19 10:00:00.000000
"""

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("memberships_pkey", "memberships", type_="primary")
    op.create_primary_key("memberships_pkey", "memberships", ["user_id", "household_id"])


def downgrade() -> None:
    # Ne garde qu'un foyer par utilisateur (le plus ancien) avant de rétablir l'unicité.
    op.execute(
        "DELETE FROM memberships m USING memberships o "
        "WHERE m.user_id = o.user_id AND m.household_id > o.household_id"
    )
    op.drop_constraint("memberships_pkey", "memberships", type_="primary")
    op.create_primary_key("memberships_pkey", "memberships", ["user_id"])
