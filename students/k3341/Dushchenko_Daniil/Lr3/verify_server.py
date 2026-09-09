"""Проверка поднятой ЛР3: CRUD, отчёт, HTTP-парсер и Celery.

Создаёт временного пользователя и удаляет его учебные данные после проверки.
Успешные результаты парсинга остаются в ParsedPage.
"""
import argparse
import secrets
import time
import requests


def verify(base: str, parser: bool = True) -> None:
    client = requests.Session()
    suffix = secrets.token_hex(5)
    user_id = None
    category_id = None
    operation_id = None
    tag_id = None

    def call(method: str, path: str, expected: int, **kwargs):
        response = client.request(method, base.rstrip("/") + path, timeout=45, **kwargs)
        assert response.status_code == expected, f"{method} {path}: {response.status_code} {response.text}"
        return response.json() if response.content else None

    try:
        call("GET", "/health", 200)
        call("GET", "/operations", 401)
        user = call("POST", "/auth/register", 201, json={"email": f"check-{suffix}@example.com",
                    "full_name": "Проверка лабораторной", "password": "Temporary-" + suffix})
        user_id = user["id"]
        token = call("POST", "/auth/token", 200, data={"username": user["email"], "password": "Temporary-" + suffix})
        client.headers["Authorization"] = "Bearer " + token["access_token"]
        category = call("POST", "/categories", 201, json={"name": "Еда", "monthly_limit": 100})
        category_id = category["id"]
        tag_id = call("POST", "/tags", 201, json={"name": "check-" + suffix})["id"]
        operation = call("POST", "/operations", 201, json={"title": "Обед", "amount": 120,
                         "operation_type": "expense", "operation_date": "2026-09-09T12:00:00",
                         "category_id": category_id, "tags": [{"tag_id": tag_id, "priority": 3}]})
        operation_id = operation["id"]
        assert operation["tags"][0]["priority"] == 3
        report = call("GET", "/reports/monthly?year=2026&month=9", 200)
        assert report["expense"] == 120 and report["categories"][0]["exceeded"]
        call("PATCH", f"/operations/{operation_id}", 422, json={"title": None})
        call("PATCH", f"/operations/{operation_id}", 200, json={"amount": 80})
        print("PASS registration, JWT, CRUD, validation, monthly report", flush=True)
        if parser:
            result = call("POST", "/parser/parse-sync", 201, json={"url": "https://www.worldbank.org/"})
            assert result["status_code"] == 200 and result["title"]
            print("PASS synchronous parser:", result["title"], flush=True)
            accepted = call("POST", "/parser/parse-async", 202, json={"url": "https://www.worldbank.org/"})
            for _ in range(45):
                status = call("GET", "/parser/tasks/" + accepted["task_id"], 200)
                if status["ready"]:
                    break
                time.sleep(1)
            assert status["status"] == "SUCCESS", status
            assert status["result"]["status_code"] == 200
            print("PASS Celery task:", accepted["task_id"], status["status"], flush=True)
    finally:
        for path in [f"/operations/{operation_id}" if operation_id else None,
                     f"/tags/{tag_id}" if tag_id else None,
                     f"/categories/{category_id}" if category_id else None,
                     f"/users/{user_id}" if user_id else None]:
            if path:
                call("DELETE", path, 204)
        client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--without-parser", action="store_true")
    args = parser.parse_args()
    verify(args.api, not args.without_parser)
