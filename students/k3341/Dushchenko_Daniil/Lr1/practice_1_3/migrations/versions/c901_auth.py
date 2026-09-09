"""Пароли и отзыв токенов после смены пароля.

Старые учебные пользователи сохраняются без пароля: вход для них закрыт.
Для проверки авторизации нужно зарегистрировать нового пользователя.
"""
from alembic import op
import sqlalchemy as sa

revision = "c901_auth"
down_revision = "b8d18406f516"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("user", sa.Column("hashed_password", sa.String(255), nullable=True))
    op.add_column("user", sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("user", "token_version")
    op.drop_column("user", "hashed_password")
