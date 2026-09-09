import os

from celery import Celery

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)
SCHEDULED_PARSE_URL = os.getenv("SCHEDULED_PARSE_URL", "https://www.worldbank.org/")

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
    enable_utc=True,
    result_expires=86400,
    task_track_started=True,
    task_soft_time_limit=50,
    task_time_limit=60,
    broker_connection_retry_on_startup=True,
    beat_schedule={
        "scheduled-parser-health-check": {
            "task": "app.tasks.parse_url_task",
            "schedule": int(os.getenv("PARSE_INTERVAL_SECONDS", "21600")),
            "args": (SCHEDULED_PARSE_URL,),
        }
    },
)
