import os

from celery import Celery

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)
SCHEDULED_PARSE_URL = os.getenv("SCHEDULED_PARSE_URL", "https://www.imf.org/")

celery_app = Celery(
    "finance_parser_tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["app.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Europe/Moscow",
    enable_utc=False,
    beat_schedule={
        "scheduled-parser-health-check": {
            "task": "app.tasks.parse_url_task",
            "schedule": 6 * 60 * 60,
            "args": (SCHEDULED_PARSE_URL,),
        }
    },
)
