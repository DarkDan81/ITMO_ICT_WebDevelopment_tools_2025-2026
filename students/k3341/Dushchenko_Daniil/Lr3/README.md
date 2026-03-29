# Лабораторная работа 3

## Состав проекта

- `finance_api` — основное `FastAPI`-приложение сервиса личных финансов
- `parser_service` — отдельный HTTP-сервис парсинга
- `docker-compose.yml` — оркестрация `FastAPI`, `PostgreSQL`, `Redis`, parser-service и `Celery`

## Что реализовано

- контейнеризация основного API
- контейнеризация сервиса парсинга
- `PostgreSQL` в `Docker`
- синхронный вызов парсера из основного `FastAPI`
- асинхронный вызов парсера через `Celery + Redis`
- `Celery Beat` для периодической задачи

## Основные маршруты

### Основной API

- `GET /` — проверка сервиса
- `POST /parser/parse-sync` — синхронный вызов parser-service
- `POST /parser/parse-async` — постановка задачи в очередь
- `GET /parser/tasks/{task_id}` — статус фоновой задачи

### Parser-service

- `GET /health`
- `POST /parse`

## Запуск

```powershell
docker compose up --build
```

После запуска:

- основной API: `http://127.0.0.1:8000/docs`
- parser-service: `http://127.0.0.1:8001/docs`

## Пример синхронного запроса

```bash
curl -X POST http://127.0.0.1:8000/parser/parse-sync ^
  -H "Content-Type: application/json" ^
  -d "{\"url\":\"https://www.imf.org/\"}"
```

## Пример асинхронного запроса

```bash
curl -X POST http://127.0.0.1:8000/parser/parse-async ^
  -H "Content-Type: application/json" ^
  -d "{\"url\":\"https://www.worldbank.org/\"}"
```
