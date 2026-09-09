from uuid import uuid4

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException
from requests import RequestException, Timeout
from redis.exceptions import RedisError
from kombu.exceptions import OperationalError

from app.celery_app import celery_app
from app.models import User
from app.parser_client import parse_via_service
from app.parser_models import AsyncParseAccepted, ParseRequest, ParseResultResponse, TaskStatusResponse
from app.security import get_current_user
from app.tasks import parse_url_task

router = APIRouter(prefix="/parser", tags=["Парсер"])


@router.post("/parse-sync", response_model=ParseResultResponse, status_code=201)
def parse_sync(payload: ParseRequest, user: User = Depends(get_current_user)) -> ParseResultResponse:
    try:
        return ParseResultResponse.model_validate(parse_via_service(payload))
    except Timeout:
        raise HTTPException(504, "Парсер не ответил вовремя")
    except RequestException:
        raise HTTPException(502, "Не удалось получить страницу; проверьте URL или повторите позже")


@router.post("/parse-async", response_model=AsyncParseAccepted, status_code=202)
def parse_async(payload: ParseRequest, user: User = Depends(get_current_user)) -> AsyncParseAccepted:
    task_id = str(uuid4())
    try:
        # Привязываем результат к пользователю до отправки задания воркеру.
        celery_app.backend.client.setex(f"parser-owner:{task_id}", 86400, str(user.id))
        parse_url_task.apply_async(args=[str(payload.url)], task_id=task_id)
    except (RedisError, OperationalError):
        raise HTTPException(503, "Очередь временно недоступна")
    return AsyncParseAccepted(message="Задание принято", task_id=task_id, url=str(payload.url))


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
def task_status(task_id: str, user: User = Depends(get_current_user)) -> TaskStatusResponse:
    try:
        owner = celery_app.backend.client.get(f"parser-owner:{task_id}")
        if owner is None or owner.decode() != str(user.id):
            raise HTTPException(404, "Задание не найдено или срок хранения истёк")
        task = AsyncResult(task_id, app=celery_app)
        state = task.state
        return TaskStatusResponse(task_id=task_id, status=state, ready=task.ready(),
                                  result=task.result if state == "SUCCESS" else None,
                                  error="Не удалось обработать URL после повторных попыток" if state == "FAILURE" else None)
    except (RedisError, OperationalError):
        raise HTTPException(503, "Хранилище результатов временно недоступно")
