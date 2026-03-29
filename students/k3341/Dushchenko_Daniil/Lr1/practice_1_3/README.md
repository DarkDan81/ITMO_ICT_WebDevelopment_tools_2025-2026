# Practice 1.3

Третья практика по теме сервиса управления личными финансами.

## Что реализовано

- `FastAPI` + `SQLModel` + `PostgreSQL`;
- подключение к базе данных через `.env`;
- настройка `Alembic`;
- автогенерация и применение миграций;
- история миграций для основной схемы и изменения ассоциативной сущности;
- связь `many-to-many` между `operation` и `tag`;
- дополнительное поле `priority` в `operation_tag_link`.

## Установка

1. Создать и активировать виртуальное окружение.
2. Установить зависимости:

```bash
pip install -r requirements.txt
```

3. Создать локальный `.env` по примеру `.env.example`.

## Настройка переменных окружения

Пример переменной для БД:

```text
DATABASE_URL=postgresql://postgres@localhost:5432/personal_finance_practice_3_db
```

## Миграции

Создание новой миграции:

```bash
alembic revision --autogenerate -m "your message"
```

Применение миграций:

```bash
alembic upgrade head
```

## Запуск

```bash
uvicorn app.main:app --reload
```

## Основные эндпоинты

- `GET /`
- `GET /users`
- `GET /users/{user_id}`
- `POST /users`
- `PATCH /users/{user_id}`
- `DELETE /users/{user_id}`
- `GET /categories`
- `GET /categories/{category_id}`
- `POST /categories`
- `PATCH /categories/{category_id}`
- `DELETE /categories/{category_id}`
- `GET /tags`
- `GET /tags/{tag_id}`
- `POST /tags`
- `PATCH /tags/{tag_id}`
- `DELETE /tags/{tag_id}`
- `GET /operations`
- `GET /operations/{operation_id}`
- `POST /operations`
- `PATCH /operations/{operation_id}`
- `DELETE /operations/{operation_id}`
