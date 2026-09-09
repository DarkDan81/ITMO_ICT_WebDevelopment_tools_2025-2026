"""Синхронизировать отчёты и примеры кода перед mkdocs build."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
STUDENT = ROOT / "students/k3341/Dushchenko_Daniil"
DOCS = STUDENT / "docs"
REPO = "https://github.com/DarkDan81/ITMO_ICT_WebDevelopment_tools_2025-2026/tree/main/students/k3341/Dushchenko_Daniil"


def write(name: str, text: str) -> None:
    path = STUDENT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(line.rstrip() for line in text.strip().splitlines()) + "\n", encoding="utf-8")


lr1 = f"""# Лабораторная работа 1. Сервис личных финансов

**Дущенко Даниил, К3341.** Тема: учёт доходов и расходов, бюджеты категорий и финансовые отчёты.

## Этапы работы

| Практика | Реализация |
| --- | --- |
| [1.1]({REPO}/Lr1/practice_1_1) | Временная БД из трёх операций, Pydantic, вложенная категория и список тегов, CRUD |
| [1.2]({REPO}/Lr1/practice_1_2) | PostgreSQL, SQLModel, CRUD и связи между таблицами |
| [1.3]({REPO}/Lr1/practice_1_3) | Alembic, .env; итоговый API с авторизацией и отчётами |

## Модель данных

В основной схеме пять таблиц: `user`, `category`, `operation`, `tag`, `operationtaglink`.
Пользователь имеет несколько категорий и операций (one-to-many). Операция может иметь несколько тегов,
а тег — относиться к нескольким операциям (many-to-many).
В таблице связи хранятся дата назначения `assigned_at` и приоритет `priority` от 1 до 5.

Категория содержит месячный бюджет `monthly_limit`. В операции задаются сумма, тип `income`/`expense`,
дата и категория. Суммы должны быть положительными. Время хранится в UTC.
Теги являются общим справочником; финансовые операции, категории и отчёты доступны только владельцу.

## API

| Метод и путь | Назначение |
| --- | --- |
| `GET /`, `GET /health` | Информация о приложении, проверка БД |
| `POST /auth/register`, `POST /users` | Регистрация с email и паролем |
| `POST /auth/token` | Вход: email передаётся в поле формы `username` |
| `GET /users/me` | Собственный профиль с вложенными категориями |
| `POST /users/me/password` | Смена пароля с проверкой текущего |
| `GET /users`, `GET /users/{{id}}` | Список пользователей и базовые данные пользователя |
| `PATCH /users/{{id}}`, `DELETE /users/{{id}}` | Изменение и удаление своего профиля |
| `GET /categories`, `GET /categories/{{id}}`, `POST /categories`, `PATCH /categories/{{id}}`, `DELETE /categories/{{id}}` | CRUD категорий |
| `GET /tags`, `GET /tags/{{id}}`, `POST /tags`, `PATCH /tags/{{id}}`, `DELETE /tags/{{id}}` | CRUD справочника тегов |
| `GET /operations`, `GET /operations/{{id}}`, `POST /operations`, `PATCH /operations/{{id}}`, `DELETE /operations/{{id}}` | CRUD операций с вложенными объектами |
| `GET /reports/monthly?year=2026&month=9` | Доходы, расходы, баланс и остатки бюджетов за месяц |

В Swagger `/docs` доступны схемы запросов и ответов. Сначала нужно зарегистрироваться, затем нажать
**Authorize** и ввести email в поле username и свой пароль. Остальные запросы будут отправляться с JWT.

Регистрация, поиск пользователя и проверка токена написаны вручную. Для JWT используется PyJWT.
Пароль хранится как PBKDF2-HMAC-SHA256 с отдельной случайной солью и 600000 итерациями.
Токен действует 30 минут. После смены пароля увеличивается `token_version`, поэтому старые токены отклоняются.
Хеши паролей не входят в модели ответов.

## Пример проверки

1. Зарегистрировать пользователя: email, full_name, password (не короче 8 символов).
2. Создать категорию: `{{"name": "Еда", "monthly_limit": 100}}`.
3. Создать расход: `{{"title": "Обед", "amount": 120, "operation_type": "expense", "operation_date": "2026-09-09T12:00:00", "category_id": 1}}`.
   Вместо 1 использовать id созданной категории.
4. Запросить отчёт за сентябрь 2026: расход 120, остаток бюджета −20, `exceeded=true`.

Операция и связи с тегами сохраняются одной транзакцией. Неверный тег не оставляет частично созданной операции.
Повтор тега и `null` в обязательных полях дают 422. Попытка обратиться к чужой операции даёт 404.
Сначала удаляются операции, затем используемые ими категории и теги.

## Запуск и миграции

Самый простой запуск всех сервисов описан в [README ЛР3]({REPO}/Lr3).
Для отдельного запуска из `Lr1/practice_1_3`:

```bash
python -m venv .venv
# Linux: source .venv/bin/activate
# PowerShell: .venv/Scripts/Activate.ps1
pip install -r requirements.txt
```

Скопировать `.env.example` в `.env`, указать адрес своей PostgreSQL-БД и случайный `JWT_SECRET`.
Ключ можно получить командой `python -c "import secrets; print(secrets.token_hex(32))"`.

```bash
alembic upgrade head
uvicorn app.main:app --reload
python -m unittest discover -s tests -v
```

Миграции: исходная схема → поле priority → hashed_password и token_version.
Старые учебные записи сохраняются без пароля; автоматически входить под ними нельзя.
Для демонстрации авторизации используется новая регистрация.

## Проверка и вывод

Автоматические тесты проверяют CRUD, финансовый отчёт, изоляцию пользователей, отклонение неверных запросов
и смену пароля. На PostgreSQL проверены `upgrade head`, `downgrade base` и повторный `upgrade head`
в отдельной тестовой базе. Рабочая база при этом не очищалась.

В результате получен API по выбранной теме с ORM, миграциями и самостоятельной реализацией авторизации.
Отдельный месячный отчёт позволяет сравнить расходы с бюджетами категорий.
"""

lr3 = """# Лабораторная работа 3. Docker и очередь задач

**Дущенко Даниил, К3341.** Использованы API из ЛР1 и парсер финансовых сайтов из ЛР2.

## Контейнеры

| Сервис | Назначение |
| --- | --- |
| db | PostgreSQL 16 и постоянный том с данными |
| redis | Брокер Celery и хранилище результатов на 24 часа |
| migrate | Однократное применение миграций перед запуском API |
| finance-api | API ЛР3 с HTTP-вызовом парсера и постановкой в очередь |
| parser-service | Получение HTML, извлечение первого title, запись в ParsedPage |
| celery-worker | Выполнение задач парсинга; два рабочих процесса |
| celery-beat | Отправка периодической задачи каждые шесть часов |
| lr1-api | Отдельный запуск итоговой ЛР1 с той же финансовой БД |

Для приложений созданы Dockerfile на Python 3.12. Docker Compose связывает сервисы внутренней сетью.
API запускаются после успешной миграции, готовности PostgreSQL и парсера.
У контейнера migrate состояние Exited (0) нормально: после обновления схемы его работа завершена.

## Вызов парсера

`POST /parser/parse-sync` принимает `{"url": "https://www.worldbank.org/"}`.
Основной API отправляет HTTP-запрос в отдельный контейнер parser-service на `POST /parse`.
Парсер извлекает заголовок, сохраняет его в PostgreSQL и возвращает результат.

`POST /parser/parse-async` возвращает 202 и task_id. Celery получает задание через Redis,
вызывает тот же HTTP-сервис и сохраняет результат в Redis.
`GET /parser/tasks/{task_id}` возвращает состояние PENDING, STARTED, RETRY, SUCCESS или FAILURE.
Статус и результат доступны пользователю, который создал задание.
При сетевом сбое выполняются не более двух повторных попыток; ошибка видна в ответе проверки статуса.

Внешние запросы ограничены тайм-аутами. Разрешены публичные HTTP/HTTPS-адреса, размер страницы до 2 МБ.
HTTP-ошибки и отсутствие title не записываются как успешный результат.
Таблица ParsedPage хранит URL, источник, заголовок, способ загрузки, HTTP-статус и время.

## Запуск

Из папки `Lr3`:

```bash
python prepare_env.py
docker compose up -d --build
docker compose ps
```

`prepare_env.py` создаёт `.env` с новым ключом JWT и не перезаписывает существующие настройки.

| Приложение | Локальный адрес |
| --- | --- |
| ЛР3 | http://127.0.0.1:8000/docs |
| Парсер | http://127.0.0.1:8001/docs |
| ЛР1 | http://127.0.0.1:8011/docs |
| PostgreSQL | 127.0.0.1:5434 |

Зарегистрировать пользователя через `/auth/register`, затем войти кнопкой Authorize в Swagger.
Для полного сценария проверки:

```bash
pip install requests
python verify_server.py --api http://127.0.0.1:8000
python verify_server.py --api http://127.0.0.1:8011 --without-parser
```

Скрипт проверяет регистрацию, JWT, операции, месячный отчёт, прямой и фоновый вызов парсера.
Созданные им пользователь, операция, категория и тег удаляются в конце; результаты парсинга остаются.

## Периодическая задача и проверка

Адрес задаётся через SCHEDULED_PARSE_URL (по умолчанию World Bank), интервал — PARSE_INTERVAL_SECONDS (21600).
На сервере 09.09.2026 проверены синхронный запрос и задача Celery: оба завершились успешно и записали данные.
Для проверки таймера интервал временно уменьшался до 60 секунд: Beat отправил задание, worker выполнил его
со статусом SUCCESS. После проверки установлен обычный интервал шесть часов.

ЛР1 и ЛР3 работают на сервере в контейнерах с автоматическим перезапуском.
Адреса Swagger на сервере: `/web-labs/api/lr1/docs` и `/web-labs/api/lr3/docs` на darkdan.ru.
Перед доступом действует существующий вход на сайт, а внутри API — регистрация и JWT лабораторной.

## Вывод

Реализованы все три подзадачи: контейнеризация, взаимодействие через HTTP и очередь Celery/Redis.
Отдельный worker позволяет вернуть пользователю task_id сразу, не дожидаясь загрузки страницы.
Дополнительно проверен периодический запуск через Celery Beat.
"""


def main() -> None:
    data = json.loads((STUDENT / "Lr2/lab_2/benchmark_results.json").read_text(encoding="utf-8"))
    tables = []
    for start in [0, 3, 6]:
        table = "| Подход | Время, с | Результат |\n| --- | ---: | --- |\n"
        for run in data["runs"][start:start + 3]:
            duration = re.search(r"Duration: ([\d.]+)", run["stdout"]).group(1)
            result = "Правильная сумма" if start != 6 else "4 успешно, 0 ошибок"
            table += f'| {run["program"].removesuffix(".py").split("_", 1)[1]} | {duration} | {result} |\n'
        tables.append(table)
    lr2 = f"""# Лабораторная работа 2. Потоки, процессы и asyncio

**Дущенко Даниил, К3341.** Сравнение подходов на вычислениях и сетевом вводе-выводе.

## Программы

| Файл | Реализация |
| --- | --- |
| task1_threading.py | threading.Thread, отдельный результат для каждой части диапазона, join |
| task1_multiprocessing.py | multiprocessing.Pool, передача диапазонов процессам |
| task1_async.py | async calculate_sum, asyncio.gather и передача управления через await |
| task2_threading.py | Поток для каждой части списка URL |
| task2_multiprocessing.py | Процесс обрабатывает свою часть списка URL |
| task2_async.py | aiohttp, общая ClientSession и параллельно ожидающие корутины |

Каждая вычислительная программа содержит calculate_sum, каждый парсер — parse_and_save.
Список URL делится на части одинакового размера либо с разницей в один элемент.
Запись в БД использует отдельную сессию для каждой страницы. В async блокирующая запись SQLModel
вынесена в asyncio.to_thread. Соединения родителя закрываются перед запуском процессов.

## Вычисление суммы

По заданию считается сумма от 1 до 10¹³. Для такого диапазона применяется формула арифметической прогрессии
к каждой части, затем результаты складываются. Итог: **50000000000005000000000000**.
Этот режим показывает главным образом накладные расходы запуска.

{tables[0]}

Для сравнения CPU-bound работы добавлен режим loop: те же программы суммируют числа обычным циклом.
В измерении использован диапазон 1..5000000; результат 12500002500000.

{tables[1]}

В данном запуске процессы быстрее потоков на цикле. В обычном CPython GIL ограничивает одновременное
выполнение Python-кода потоками. asyncio работает в одном потоке и не ускоряет вычисления на CPU;
await позволяет переключаться между корутинами, но не выполняет их на разных ядрах.
Дополнительные проверки и переключения делают этот вариант цикла медленнее.

## Парсинг

Использованы сайты World Bank, Federal Reserve, Банка России и BIS. Все четыре вернули HTTP 200.
Результаты сохраняются в таблицу ParsedPage той же PostgreSQL-БД, которая используется для ЛР1.
Поля: url, source_name, title, fetch_method, status_code, fetched_at.
При сетевой ошибке программа выводит причину, продолжает остальные URL и отдельно считает неудачи.
При повторном запуске старые результаты сохраняются.

{tables[2]}

На четырёх сайтах разница невелика. Эти значения не доказывают, что один подход всегда быстрее:
на время влияют сеть, ответы сайтов и нагрузка сервера. Потоки и asyncio удобны для ожидания сети,
а процессы дают дополнительные расходы на запуск и обмен данными.

## Условия измерения

Дата: {data['measured_at']}. Python {data['python']}, {data['platform']}.
Доступно CPU: {data['cpu_count']}; в каждом варианте использовано четыре работника.
Программы запускались последовательно на сервере, по одному измерению каждого варианта.
Вывод сохранён в [benchmark_results.json]({REPO}/Lr2/lab_2/benchmark_results.json).

## Запуск

Из `Lr2/lab_2` установить `pip install -r requirements.txt` и настроить DATABASE_URL в `.env`.
Если используется Compose ЛР3: `postgresql://postgres:postgres@127.0.0.1:5434/personal_finance_lab3`.

```bash
python task1_threading.py
python task1_multiprocessing.py
python task1_async.py
python task2_threading.py
python task2_multiprocessing.py
python task2_async.py
python benchmark.py
python -m unittest discover -s tests -v
```

benchmark.py автоматически выполняет оба режима вычислений и три парсера с одинаковыми настройками.
Для ручного выбора режима задать LAB2_SUM_MODE=loop, LAB2_SUM_LIMIT=5000000 и LAB2_WORKERS=4
в `.env` или переменных окружения. LAB2_URLS позволяет передать свой JSON-список URL.
Автотесты используют локальные страницы и временную БД: проверяются успешный парсинг, HTTP 500,
отсутствие title, продолжение обработки после ошибки и корректность суммы на неровном диапазоне.
"""
    for name, text in [("lr1", lr1), ("lr2", lr2), ("lr3", lr3)]:
        write(f"docs/{name}.md", text)
        write(f"Lr{name[-1]}/REPORT.md", text)
    write("Lr2/lab_2/REPORT.md", lr2)
    write("Lr2/lab_2/README.md", "# ЛР2\n\nПорядок запуска, результаты и объяснения: [REPORT.md](REPORT.md).")
    write("Lr1/practice_1_3/README.md", lr1)
    write("Lr3/README.md", lr3)
    for lab, folders in [("lr1", ["Lr1/practice_1_3/app", "Lr1/practice_1_3/migrations"]),
                         ("lr2", ["Lr2/lab_2/app"]),
                         ("lr3", ["Lr3/parser_service/app", "Lr3/finance_api/app"])]:
        code = f"# Исходный код {lab.upper()}\n\nКод соответствует текущим файлам проекта.\n"
        files = []
        for folder in folders:
            files.extend(sorted((STUDENT / folder).rglob("*.py")))
        if lab == "lr2":
            files.extend(sorted((STUDENT / "Lr2/lab_2").glob("task*.py")))
        if lab == "lr3":
            files += [STUDENT / "Lr3/docker-compose.yml", STUDENT / "Lr3/finance_api/Dockerfile", STUDENT / "Lr3/parser_service/Dockerfile"]
        for file in files:
            if file.name == "__init__.py":
                continue
            rel = file.relative_to(STUDENT).as_posix()
            language = "python" if file.suffix == ".py" else "yaml" if file.suffix == ".yml" else "dockerfile"
            code += f"\n## {rel}\n\n```{language}\n{file.read_text(encoding='utf-8').rstrip()}\n```\n"
        write(f"docs/{lab}-code.md", code)
    write("docs/index.md", """# Средства Web-программирования

Дущенко Даниил · К3341 · 2025–2026

Тема проекта — сервис управления личными финансами.

| Работа | Содержание |
| --- | --- |
| [ЛР1](lr1.md) | FastAPI, PostgreSQL, SQLModel, Alembic, JWT и финансовый отчёт |
| [ЛР2](lr2.md) | Потоки, процессы, asyncio: сумма и парсинг финансовых сайтов |
| [ЛР3](lr3.md) | Docker Compose, HTTP-парсер, Redis, Celery и периодические задачи |

Для каждой работы приведены ход выполнения, команды запуска, результаты проверки и исходный код.
Отчёт собран с помощью MkDocs. Измерения ЛР2 и проверка серверной сборки выполнены 09.09.2026.

## Демонстрация на сервере

- [Swagger ЛР1](https://darkdan.ru/web-labs/api/lr1/docs)
- [Swagger ЛР3](https://darkdan.ru/web-labs/api/lr3/docs)
- [Swagger парсера](https://darkdan.ru/web-labs/api/parser/docs)

После входа на сайт нужно зарегистрировать пользователя в API и выполнить Authorize в Swagger.

## Задания

- [Репозиторий дисциплины](https://github.com/TonikX/ITMO_ICT_WebDevelopment_tools_2025-2026)
- [Текст ЛР1 и практики](https://rendex85.github.io/WebDevelopmentLabsDocs/lr2/lr2/)
""")
    write("README.md", """# Дущенко Даниил, К3341

Лабораторные по средствам Web-программирования.

- [ЛР1: FastAPI и авторизация](Lr1/REPORT.md)
- [ЛР2: потоки, процессы и asyncio](Lr2/REPORT.md)
- [ЛР3: запуск всех сервисов в Docker](Lr3/README.md)
- [Отчёт на сервере](https://darkdan.ru/web-labs/)

Сборка документации из корня репозитория:

```bash
pip install -r requirements-docs.txt
python tools/update_report.py
mkdocs build --strict
```

Исходники документации находятся в docs этой папки. Готовый сайт — в папке docs в корне репозитория;
эту папку можно использовать как источник GitHub Pages.
""")


if __name__ == "__main__":
    main()
