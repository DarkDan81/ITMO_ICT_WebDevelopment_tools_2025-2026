# Practice 1.2

Вторая практика по теме сервиса управления личными финансами.

## Что реализовано

- подключение к `PostgreSQL`;
- ORM-модели на `SQLModel`;
- связь `one-to-many` между `user`, `category` и `operation`;
- связь `many-to-many` между `operation` и `tag`;
- ассоциативная сущность `OperationTagLink` с дополнительным полем `assigned_at`;
- `CRUD` для пользователей, категорий, тегов и операций;
- вложенное отображение связанных объектов в ответах API;
- автоматическое создание таблиц при старте приложения.

## Установка

1. Создать и активировать виртуальное окружение.
2. Установить зависимости:

```bash
pip install -r requirements.txt
```

## Настройка базы данных

Приложение ожидает локальный `PostgreSQL` по адресу:

```text
postgresql://postgres@localhost:5432/personal_finance_practice_db
```

При необходимости строку подключения можно переопределить через переменную окружения `DATABASE_URL`.

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
