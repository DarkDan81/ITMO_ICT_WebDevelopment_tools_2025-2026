from app.celery_app import celery_app
from app.parser_client import parse_via_service
from app.parser_models import ParseRequest


@celery_app.task(name="app.tasks.parse_url_task")
def parse_url_task(url: str) -> dict:
    return parse_via_service(ParseRequest(url=url))
