"""Создать настройки для локального запуска; существующий .env не меняется."""
from pathlib import Path
import secrets

root = Path(__file__).resolve().parent
target = root / ".env"
if target.exists():
    print(".env уже существует, настройки сохранены")
else:
    content = (root / ".env.example").read_text(encoding="utf-8")
    content = content.replace("JWT_SECRET=", "JWT_SECRET=" + secrets.token_hex(32), 1)
    target.write_text(content, encoding="utf-8")
    print("Создан .env с отдельным ключом JWT")
