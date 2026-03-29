import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres@localhost:5432/personal_finance_practice_3_db",
)

SUM_LIMIT = 10_000_000_000_000
DEFAULT_WORKERS = int(os.getenv("LAB2_WORKERS", "8"))

URLS = [
    "https://www.imf.org/",
    "https://www.worldbank.org/",
    "https://www.ecb.europa.eu/",
    "https://www.federalreserve.gov/",
    "https://www.investopedia.com/",
    "https://www.cbr.ru/",
]
