# Лабораторная работа 1. Сервис личных финансов

**Дущенко Даниил, К3341.** Тема: учёт доходов и расходов, бюджеты категорий и финансовые отчёты.

## Этапы работы

| Практика | Реализация |
| --- | --- |
| [1.1](https://github.com/DarkDan81/ITMO_ICT_WebDevelopment_tools_2025-2026/tree/main/students/k3341/Dushchenko_Daniil/Lr1/practice_1_1) | Временная БД из трёх операций, Pydantic, вложенная категория и список тегов, CRUD |
| [1.2](https://github.com/DarkDan81/ITMO_ICT_WebDevelopment_tools_2025-2026/tree/main/students/k3341/Dushchenko_Daniil/Lr1/practice_1_2) | PostgreSQL, SQLModel, CRUD и связи между таблицами |
| [1.3](https://github.com/DarkDan81/ITMO_ICT_WebDevelopment_tools_2025-2026/tree/main/students/k3341/Dushchenko_Daniil/Lr1/practice_1_3) | Alembic, .env; итоговый API с авторизацией и отчётами |

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
| `GET /users`, `GET /users/{id}` | Список пользователей и базовые данные пользователя |
| `PATCH /users/{id}`, `DELETE /users/{id}` | Изменение и удаление своего профиля |
| `GET /categories`, `GET /categories/{id}`, `POST /categories`, `PATCH /categories/{id}`, `DELETE /categories/{id}` | CRUD категорий |
| `GET /tags`, `GET /tags/{id}`, `POST /tags`, `PATCH /tags/{id}`, `DELETE /tags/{id}` | CRUD справочника тегов |
| `GET /operations`, `GET /operations/{id}`, `POST /operations`, `PATCH /operations/{id}`, `DELETE /operations/{id}` | CRUD операций с вложенными объектами |
| `GET /reports/monthly?year=2026&month=9` | Доходы, расходы, баланс и остатки бюджетов за месяц |

В Swagger `/docs` доступны схемы запросов и ответов. Сначала нужно зарегистрироваться, затем нажать
**Authorize** и ввести email в поле username и свой пароль. Остальные запросы будут отправляться с JWT.

Регистрация, поиск пользователя и проверка токена написаны вручную. Для JWT используется PyJWT.
Пароль хранится как PBKDF2-HMAC-SHA256 с отдельной случайной солью и 600000 итерациями.
Токен действует 30 минут. После смены пароля увеличивается `token_version`, поэтому старые токены отклоняются.
Хеши паролей не входят в модели ответов.

## Пример проверки

1. Зарегистрировать пользователя: email, full_name, password (не короче 8 символов).
2. Создать категорию: `{"name": "Еда", "monthly_limit": 100}`.
3. Создать расход: `{"title": "Обед", "amount": 120, "operation_type": "expense", "operation_date": "2026-09-09T12:00:00", "category_id": 1}`.
   Вместо 1 использовать id созданной категории.
4. Запросить отчёт за сентябрь 2026: расход 120, остаток бюджета −20, `exceeded=true`.

Операция и связи с тегами сохраняются одной транзакцией. Неверный тег не оставляет частично созданной операции.
Повтор тега и `null` в обязательных полях дают 422. Попытка обратиться к чужой операции даёт 404.
Сначала удаляются операции, затем используемые ими категории и теги.

## Запуск и миграции

Самый простой запуск всех сервисов описан в [README ЛР3](https://github.com/DarkDan81/ITMO_ICT_WebDevelopment_tools_2025-2026/tree/main/students/k3341/Dushchenko_Daniil/Lr3).
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
