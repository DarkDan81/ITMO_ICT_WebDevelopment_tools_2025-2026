import os
import json

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres@localhost:5432/personal_finance_practice_3_db",
)

SUM_LIMIT = int(os.getenv("LAB2_SUM_LIMIT", "10000000000000"))
SUM_MODE = os.getenv("LAB2_SUM_MODE", "formula")
DEFAULT_WORKERS = int(os.getenv("LAB2_WORKERS", "4"))
if SUM_LIMIT < 1 or DEFAULT_WORKERS < 1 or SUM_MODE not in {"formula", "loop"}:
    raise ValueError("Проверьте LAB2_SUM_LIMIT, LAB2_WORKERS и LAB2_SUM_MODE")
REQUEST_TIMEOUT = 12

URLS = json.loads(os.getenv("LAB2_URLS", '["https://www.worldbank.org/", "https://www.federalreserve.gov/", "https://www.cbr.ru/", "https://www.bis.org/"]'))
if not URLS:
    raise ValueError("Список LAB2_URLS не должен быть пустым")


def split_items(items: list, workers: int) -> list[list]:
    """Размеры частей отличаются максимум на один элемент."""
    workers = min(workers, len(items))
    size, extra = divmod(len(items), workers)
    result = []
    start = 0
    for index in range(workers):
        end = start + size + (index < extra)
        result.append(items[start:end])
        start = end
    return result
