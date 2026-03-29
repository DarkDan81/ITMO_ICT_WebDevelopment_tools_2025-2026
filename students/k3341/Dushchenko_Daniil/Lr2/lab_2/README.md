# Laboratory Work 2

Лабораторная работа 2 по теме сравнения `threading`, `multiprocessing` и `asyncio`.

## Что внутри

- три программы для вычислительной задачи;
- три программы для параллельного парсинга веб-страниц;
- сохранение результатов парсинга в PostgreSQL;
- документация с описанием подходов и таблицами сравнения.

## Структура

- `app/config.py` — настройки и загрузка `.env`;
- `app/db.py` — подключение к базе данных;
- `app/models.py` — таблица для результатов парсинга;
- `app/compute_shared.py` — общая логика для вычислительной задачи;
- `app/parse_shared.py` — общая логика парсинга и сохранения в БД;
- `task1_threading.py` — вычисления через `threading`;
- `task1_multiprocessing.py` — вычисления через `multiprocessing`;
- `task1_async.py` — вычисления через `asyncio`;
- `task2_threading.py` — парсинг через `threading`;
- `task2_multiprocessing.py` — парсинг через `multiprocessing`;
- `task2_async.py` — парсинг через `asyncio` + `aiohttp`;
- `REPORT.md` — документация по лабораторной.

## Установка

```bash
pip install -r requirements.txt
```

## Переменные окружения

Создай `.env` по примеру `.env.example`.

По умолчанию лабораторная использует БД из первой лабораторной:

```text
DATABASE_URL=postgresql://postgres@localhost:5432/personal_finance_practice_3_db
```

## Запуск программ

```bash
python task1_threading.py
python task1_multiprocessing.py
python task1_async.py

python task2_threading.py
python task2_multiprocessing.py
python task2_async.py
```
