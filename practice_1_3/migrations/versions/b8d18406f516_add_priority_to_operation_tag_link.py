"""add priority to operation tag link

Revision ID: b8d18406f516
Revises: a83973acb777
Create Date: 2026-03-29 22:31:27.271934

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'b8d18406f516'
down_revision: Union[str, Sequence[str], None] = 'a83973acb777'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "operationtaglink",
        sa.Column("priority", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("operationtaglink", "priority")
