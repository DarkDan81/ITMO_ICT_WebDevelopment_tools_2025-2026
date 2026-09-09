from requests import RequestException
from app.celery_app import celery_app
from app.parser_client import parse_via_service
from app.parser_models import ParseRequest


@celery_app.task(name="app.tasks.parse_url_task", autoretry_for=(RequestException,),
                 retry_backoff=2, retry_backoff_max=10, retry_jitter=False,
                 retry_kwargs={"max_retries": 2})
def parse_url_task(url: str) -> dict:
    return parse_via_service(ParseRequest(url=url))
