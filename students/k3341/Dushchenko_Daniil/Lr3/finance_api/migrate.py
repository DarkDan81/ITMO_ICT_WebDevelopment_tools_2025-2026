"""Обновление БД, в том числе старой версии ЛР3 без alembic_version."""
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from app.db import engine

config = Config("alembic.ini")
inspector = inspect(engine)
tables = set(inspector.get_table_names())
if "user" in tables and "alembic_version" not in tables:
    required = {"user", "category", "operation", "tag", "operationtaglink"}
    columns = {c["name"] for c in inspector.get_columns("operationtaglink")} if "operationtaglink" in tables else set()
    if not required.issubset(tables) or not {"assigned_at", "priority"}.issubset(columns):
        raise RuntimeError("Неизвестная старая схема БД; автоматический stamp запрещён")
    # Эта схема была создана SQLModel.create_all в исходной версии ЛР3.
    command.stamp(config, "b8d18406f516")
command.upgrade(config, "head")
