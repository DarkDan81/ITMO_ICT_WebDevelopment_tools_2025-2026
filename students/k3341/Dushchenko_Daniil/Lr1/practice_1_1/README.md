# Practice 1.1

Первая практика по теме сервиса управления личными финансами.

## Что реализовано

- приложение на `FastAPI`;
- временная база данных для финансовых операций;
- одиночный вложенный объект `category`;
- список вложенных объектов `tags`;
- `CRUD` для операций;
- `CRUD` для категорий;
- `Pydantic`-модели с аннотацией типов;
- автодокументация по адресу `/docs`.

## Запуск

1. Создать и активировать виртуальное окружение.
2. Установить зависимости:

```bash
pip install -r requirements.txt
```

3. Запустить приложение:

```bash
uvicorn app.main:app --reload
```

## Основные эндпоинты

- `GET /`
- `GET /operations`
- `GET /operations/{operation_id}`
- `POST /operations`
- `PUT /operations/{operation_id}`
- `DELETE /operations/{operation_id}`
- `GET /categories`
- `GET /categories/{category_id}`
- `POST /categories`
- `PUT /categories/{category_id}`
- `DELETE /categories/{category_id}`
