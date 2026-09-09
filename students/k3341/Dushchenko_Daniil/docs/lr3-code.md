# Исходный код LR3

Код соответствует текущим файлам проекта.

## Lr3/parser_service/app/db.py

```python
import os

from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@db:5432/personal_finance_lab3",
)

engine = create_engine(DATABASE_URL, echo=False)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)
```

## Lr3/parser_service/app/main.py

```python
import os
import socket
from fastapi import FastAPI, HTTPException, status
from requests import RequestException, Timeout

from app.db import get_session, init_db
from sqlalchemy import text
from app.models import ParseRequest, ParseResponse
from app.services import parse_url_and_save

app = FastAPI(
    title="Personal Finance Parser Service",
    description="HTTP parser service for Docker-based laboratory work 3.",
    version="2.0.0",
    root_path=os.getenv("ROOT_PATH", ""),
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def healthcheck() -> dict:
    with get_session() as session:
        session.exec(text("SELECT 1"))
    return {"status": "ok", "service": "parser-service"}


@app.post("/parse", response_model=ParseResponse, status_code=status.HTTP_201_CREATED)
def parse(payload: ParseRequest) -> ParseResponse:
    try:
        with get_session() as session:
            page = parse_url_and_save(str(payload.url), session)
    except Timeout as exc:
        raise HTTPException(504, "Сайт не ответил вовремя") from exc
    except (ValueError, socket.gaierror) as exc:
        raise HTTPException(400, str(exc)) from exc
    except RequestException as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Parser request failed: {exc}",
        ) from exc

    return ParseResponse(
        message="Parsing completed",
        url=page.url,
        title=page.title,
        source_name=page.source_name,
        status_code=page.status_code,
        fetch_method=page.fetch_method,
    )
```

## Lr3/parser_service/app/models.py

```python
from datetime import datetime, timezone

from pydantic import BaseModel, HttpUrl, Field as PydanticField
from sqlmodel import Field, SQLModel


class ParsedPage(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    url: str = Field(index=True, max_length=500)
    source_name: str = Field(max_length=100)
    title: str = Field(max_length=500)
    fetch_method: str = Field(max_length=30, index=True)
    status_code: int
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class ParseRequest(BaseModel):
    url: HttpUrl = PydanticField(..., max_length=500)


class ParseResponse(BaseModel):
    message: str
    url: str
    title: str
    source_name: str
    status_code: int
    fetch_method: str
```

## Lr3/parser_service/app/services.py

```python
import ipaddress
import socket
from html.parser import HTMLParser
from urllib.parse import urlparse, urljoin

import requests
from charset_normalizer import from_bytes
from sqlmodel import Session
from app.models import ParsedPage


class TitleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inside = False
        self.done = False
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == "title" and not self.done:
            self.inside = True

    def handle_endtag(self, tag):
        if tag == "title" and self.inside:
            self.inside = False
            self.done = True

    def handle_data(self, data):
        if self.inside:
            self.parts.append(data)


def validate_public_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Нужен публичный HTTP/HTTPS URL без логина и пароля")
    if parsed.port not in {None, 80, 443}:
        raise ValueError("Разрешены порты 80 и 443")
    addresses = socket.getaddrinfo(parsed.hostname, parsed.port or 443)
    if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
        raise ValueError("Внутренние адреса не поддерживаются")


def parse_url_and_save(url: str, session: Session) -> ParsedPage:
    current = url
    for _ in range(6):
        validate_public_url(current)
        with requests.get(current, timeout=(3, 12), allow_redirects=False, stream=True) as response:
            if response.is_redirect:
                current = urljoin(current, response.headers["Location"])
                continue
            response.raise_for_status()
            content = bytearray()
            for chunk in response.iter_content(65536):
                content.extend(chunk)
                if len(content) > 2_000_000:
                    raise ValueError("Страница больше 2 МБ")
            decoded = from_bytes(bytes(content)).best()
            parser = TitleParser()
            parser.feed(str(decoded) if decoded is not None else content.decode("utf-8", errors="replace"))
            title = " ".join("".join(parser.parts).split())
            if not title:
                raise ValueError("На странице нет title")
            page = ParsedPage(url=url, source_name=(urlparse(url).hostname or "unknown")[:100],
                              title=title[:500], fetch_method="docker-http-parser", status_code=response.status_code)
            session.add(page)
            session.commit()
            session.refresh(page)
            return page
    raise ValueError("Слишком много перенаправлений")
```

## Lr3/finance_api/app/celery_app.py

```python
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
```

## Lr3/finance_api/app/db.py

```python
import os

from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres@localhost:5432/personal_finance_practice_3_db",
)

engine = create_engine(DATABASE_URL, echo=False)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
```

## Lr3/finance_api/app/finance.py

```python
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.db import get_session
from app.models import (Category, CategoryCreate, CategoryRead, CategoryReadWithUser, CategoryUpdate,
                        Operation, OperationCreate, OperationReadWithRelations, OperationTagLink,
                        OperationUpdate, Tag, TagCreate, TagRead, TagReadWithMetadata, TagUpdate, User, UserRead)
from app.security import get_current_user

router = APIRouter(tags=["Финансы"])


def owned(model, item_id: int, user: User, session: Session):
    item = session.get(model, item_id)
    if item is None or item.user_id != user.id:
        raise HTTPException(404, "Запись не найдена")
    return item


def check_owner(user_id: int | None, user: User) -> None:
    if user_id is not None and user_id != user.id:
        raise HTTPException(403, "Нельзя указать другого владельца")


def check_tags(assignments, session: Session) -> None:
    for assignment in assignments:
        if session.get(Tag, assignment.tag_id) is None:
            raise HTTPException(400, f"Тег {assignment.tag_id} не найден")


def set_tags(operation: Operation, assignments, session: Session) -> None:
    for link in session.exec(select(OperationTagLink).where(OperationTagLink.operation_id == operation.id)).all():
        session.delete(link)
    session.flush()
    for tag in assignments:
        session.add(OperationTagLink(operation_id=operation.id, tag_id=tag.tag_id, priority=tag.priority))


def serialize_operation(operation: Operation, session: Session) -> OperationReadWithRelations:
    links = session.exec(select(OperationTagLink).where(OperationTagLink.operation_id == operation.id)).all()
    tags = []
    for link in links:
        tag = session.get(Tag, link.tag_id)
        tags.append(TagReadWithMetadata(id=tag.id, name=tag.name, assigned_at=link.assigned_at, priority=link.priority))
    return OperationReadWithRelations(
        **operation.model_dump(), user=UserRead.model_validate(operation.user),
        category=CategoryRead.model_validate(operation.category), tags=tags,
    )


@router.get("/categories", response_model=list[CategoryRead])
def categories(user: User = Depends(get_current_user), session: Session = Depends(get_session)) -> list[Category]:
    return list(session.exec(select(Category).where(Category.user_id == user.id)).all())


@router.get("/categories/{category_id}", response_model=CategoryReadWithUser)
def category(category_id: int, user: User = Depends(get_current_user), session: Session = Depends(get_session)) -> Category:
    return owned(Category, category_id, user, session)


@router.post("/categories", response_model=CategoryRead, status_code=201)
def create_category(data: CategoryCreate, user: User = Depends(get_current_user),
                    session: Session = Depends(get_session)) -> Category:
    check_owner(data.user_id, user)
    item = Category.model_validate(data.model_dump() | {"user_id": user.id})
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.patch("/categories/{category_id}", response_model=CategoryRead)
def update_category(category_id: int, data: CategoryUpdate, user: User = Depends(get_current_user),
                    session: Session = Depends(get_session)) -> Category:
    item = owned(Category, category_id, user, session)
    check_owner(data.user_id, user)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.delete("/categories/{category_id}", status_code=204)
def delete_category(category_id: int, user: User = Depends(get_current_user),
                    session: Session = Depends(get_session)) -> Response:
    item = owned(Category, category_id, user, session)
    if item.operations:
        raise HTTPException(409, "Категория используется в операциях")
    session.delete(item)
    session.commit()
    return Response(status_code=204)


# Теги — общий справочник. Личные суммы и категории доступны только владельцу.
@router.get("/tags", response_model=list[TagRead])
def tags(user: User = Depends(get_current_user), session: Session = Depends(get_session)) -> list[Tag]:
    return list(session.exec(select(Tag)).all())


def get_tag(tag_id: int, session: Session) -> Tag:
    item = session.get(Tag, tag_id)
    if item is None:
        raise HTTPException(404, "Тег не найден")
    return item


@router.get("/tags/{tag_id}", response_model=TagRead)
def tag(tag_id: int, user: User = Depends(get_current_user), session: Session = Depends(get_session)) -> Tag:
    return get_tag(tag_id, session)


def save_tag(item: Tag, session: Session) -> Tag:
    session.add(item)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "Тег с таким именем уже существует")
    session.refresh(item)
    return item


@router.post("/tags", response_model=TagRead, status_code=201)
def create_tag(data: TagCreate, user: User = Depends(get_current_user), session: Session = Depends(get_session)) -> Tag:
    return save_tag(Tag.model_validate(data), session)


@router.patch("/tags/{tag_id}", response_model=TagRead)
def update_tag(tag_id: int, data: TagUpdate, user: User = Depends(get_current_user),
               session: Session = Depends(get_session)) -> Tag:
    item = get_tag(tag_id, session)
    if any(operation.user_id != user.id for operation in item.operations):
        raise HTTPException(409, "Тег используется другим пользователем")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    return save_tag(item, session)


@router.delete("/tags/{tag_id}", status_code=204)
def delete_tag(tag_id: int, user: User = Depends(get_current_user), session: Session = Depends(get_session)) -> Response:
    item = get_tag(tag_id, session)
    if item.operations:
        raise HTTPException(409, "Тег используется в операциях")
    session.delete(item)
    session.commit()
    return Response(status_code=204)


@router.get("/operations", response_model=list[OperationReadWithRelations])
def operations(user: User = Depends(get_current_user), session: Session = Depends(get_session)) -> list[OperationReadWithRelations]:
    items = session.exec(select(Operation).where(Operation.user_id == user.id)).all()
    return [serialize_operation(item, session) for item in items]


@router.get("/operations/{operation_id}", response_model=OperationReadWithRelations)
def operation(operation_id: int, user: User = Depends(get_current_user),
              session: Session = Depends(get_session)) -> OperationReadWithRelations:
    return serialize_operation(owned(Operation, operation_id, user, session), session)


@router.post("/operations", response_model=OperationReadWithRelations, status_code=201)
def create_operation(data: OperationCreate, user: User = Depends(get_current_user),
                     session: Session = Depends(get_session)) -> OperationReadWithRelations:
    check_owner(data.user_id, user)
    if data.category_id is None:
        raise HTTPException(422, "Нужно указать category_id")
    owned(Category, data.category_id, user, session)
    check_tags(data.tags, session)
    item = Operation.model_validate(data.model_dump(exclude={"tags"}) | {"user_id": user.id})
    session.add(item)
    session.flush()  # Получаем id, но ещё не фиксируем операцию.
    set_tags(item, data.tags, session)
    session.commit()  # Операция и её теги сохраняются вместе.
    session.refresh(item)
    return serialize_operation(item, session)


@router.patch("/operations/{operation_id}", response_model=OperationReadWithRelations)
def update_operation(operation_id: int, data: OperationUpdate, user: User = Depends(get_current_user),
                     session: Session = Depends(get_session)) -> OperationReadWithRelations:
    item = owned(Operation, operation_id, user, session)
    check_owner(data.user_id, user)
    if data.category_id is not None:
        owned(Category, data.category_id, user, session)
    if data.tags is not None:
        check_tags(data.tags, session)
    for key, value in data.model_dump(exclude_unset=True, exclude={"tags"}).items():
        setattr(item, key, value)
    session.add(item)
    if data.tags is not None:
        set_tags(item, data.tags, session)
    session.commit()
    session.refresh(item)
    return serialize_operation(item, session)


@router.delete("/operations/{operation_id}", status_code=204)
def delete_operation(operation_id: int, user: User = Depends(get_current_user),
                     session: Session = Depends(get_session)) -> Response:
    item = owned(Operation, operation_id, user, session)
    item.tags = []
    session.delete(item)
    session.commit()
    return Response(status_code=204)
```

## Lr3/finance_api/app/main.py

```python
import os
from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlmodel import Session

from app.db import get_session
from app.users import router as users_router
from app.finance import router as finance_router
from app.reports import router as reports_router

app = FastAPI(title="Личные финансы — ЛР3", version="2.0.0", root_path=os.getenv("ROOT_PATH", ""))
app.include_router(users_router)
app.include_router(finance_router)
app.include_router(reports_router)


@app.get("/")
def index() -> dict[str, str]:
    return {"message": "Сервис личных финансов", "docs": "docs"}


@app.get("/health")
def health(session: Session = Depends(get_session)) -> dict[str, str]:
    session.exec(text("SELECT 1"))
    return {"status": "ok"}

from app.parser_routes import router as parser_router
app.include_router(parser_router)
```

## Lr3/finance_api/app/models.py

```python
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field as PydanticField, model_validator
from sqlmodel import Field, Relationship, SQLModel


class AppModel(SQLModel):
    model_config = ConfigDict(allow_inf_nan=False, str_strip_whitespace=True)


class OperationType(str, Enum):
    income = "income"
    expense = "expense"


class UpdateModel(AppModel):
    @model_validator(mode="before")
    @classmethod
    def reject_null_required(cls, values):
        nullable = {"description", "monthly_limit", "priority"}
        if isinstance(values, dict):
            for key, value in values.items():
                if value is None and key not in nullable:
                    raise ValueError(f"{key} не может быть null")
        return values


class UserBase(AppModel):
    email: str = Field(index=True, unique=True, max_length=255)
    full_name: str = Field(min_length=1, max_length=100)


class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    hashed_password: str | None = Field(default=None, max_length=255)
    token_version: int = Field(default=0)
    categories: list["Category"] = Relationship(back_populates="user")
    operations: list["Operation"] = Relationship(back_populates="user")


class UserCreate(UserBase):
    email: EmailStr
    password: str = PydanticField(min_length=8, max_length=128)


class UserUpdate(UpdateModel):
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, min_length=1, max_length=100)


class CategoryBase(AppModel):
    name: str = Field(min_length=1, max_length=50)
    monthly_limit: float | None = Field(default=None, ge=0)
    user_id: int | None = Field(default=None, foreign_key="user.id")


class Category(CategoryBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user: User | None = Relationship(back_populates="categories")
    operations: list["Operation"] = Relationship(back_populates="category")


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(UpdateModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    monthly_limit: float | None = Field(default=None, ge=0)
    user_id: int | None = None


class TagBase(AppModel):
    name: str = Field(min_length=1, max_length=30, unique=True)


class OperationTagLink(SQLModel, table=True):
    operation_id: int | None = Field(
        default=None,
        foreign_key="operation.id",
        primary_key=True,
    )
    tag_id: int | None = Field(default=None, foreign_key="tag.id", primary_key=True)
    assigned_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    priority: int | None = Field(default=None, ge=1, le=5)


class Tag(TagBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    operations: list["Operation"] = Relationship(
        back_populates="tags",
        link_model=OperationTagLink,
    )


class TagCreate(TagBase):
    pass


class TagUpdate(UpdateModel):
    name: str | None = Field(default=None, min_length=1, max_length=30)


class OperationBase(AppModel):
    title: str = Field(min_length=1, max_length=100)
    amount: float = Field(gt=0)
    operation_type: OperationType
    operation_date: datetime
    description: str | None = Field(default=None, max_length=255)
    user_id: int | None = Field(default=None, foreign_key="user.id")
    category_id: int | None = Field(default=None, foreign_key="category.id")


class Operation(OperationBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user: User | None = Relationship(back_populates="operations")
    category: Category | None = Relationship(back_populates="operations")
    tags: list[Tag] = Relationship(
        back_populates="operations",
        link_model=OperationTagLink,
    )


class OperationTagAssignment(AppModel):
    tag_id: int
    priority: int | None = Field(default=None, ge=1, le=5)


class OperationCreate(OperationBase):
    @model_validator(mode="after")
    def unique_tags(self):
        ids = [tag.tag_id for tag in self.tags]
        if len(ids) != len(set(ids)):
            raise ValueError("Тег не должен повторяться")
        return self

    tags: list[OperationTagAssignment] = PydanticField(default_factory=list)


class OperationUpdate(UpdateModel):
    @model_validator(mode="after")
    def unique_tags(self):
        ids = [tag.tag_id for tag in (self.tags or [])]
        if len(ids) != len(set(ids)):
            raise ValueError("Тег не должен повторяться")
        return self

    title: str | None = Field(default=None, min_length=1, max_length=100)
    amount: float | None = Field(default=None, gt=0)
    operation_type: OperationType | None = None
    operation_date: datetime | None = None
    description: str | None = Field(default=None, max_length=255)
    user_id: int | None = None
    category_id: int | None = None
    tags: list[OperationTagAssignment] | None = None


class CategoryRead(CategoryBase):
    id: int


class TagRead(TagBase):
    id: int


class UserRead(UserBase):
    id: int


class UserReadWithRelations(UserRead):
    categories: list[CategoryRead] = PydanticField(default_factory=list)


class CategoryReadWithUser(CategoryRead):
    user: UserRead | None = None


class TagReadWithMetadata(TagRead):
    assigned_at: datetime
    priority: int | None = None


class OperationRead(OperationBase):
    id: int


class OperationReadWithRelations(OperationRead):
    user: UserRead | None = None
    category: CategoryRead | None = None
    tags: list[TagReadWithMetadata] = PydanticField(default_factory=list)


class PasswordChange(BaseModel):
    old_password: str = PydanticField(max_length=128)
    new_password: str = PydanticField(min_length=8, max_length=128)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
```

## Lr3/finance_api/app/parser_client.py

```python
import os

import requests

from app.parser_models import ParseRequest

PARSER_SERVICE_URL = os.getenv("PARSER_SERVICE_URL", "http://parser-service:8000")
PARSER_TIMEOUT = int(os.getenv("PARSER_TIMEOUT", "30"))


def parse_via_service(payload: ParseRequest) -> dict:
    response = requests.post(
        f"{PARSER_SERVICE_URL}/parse",
        json=payload.model_dump(mode="json"),
        timeout=PARSER_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()
```

## Lr3/finance_api/app/parser_models.py

```python
from pydantic import BaseModel, Field, HttpUrl


class ParseRequest(BaseModel):
    url: HttpUrl = Field(..., max_length=500)


class ParseResultResponse(BaseModel):
    message: str
    url: str
    title: str
    source_name: str
    status_code: int
    fetch_method: str


class AsyncParseAccepted(BaseModel):
    message: str
    task_id: str
    url: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    ready: bool
    result: dict | None = None
    error: str | None = None
```

## Lr3/finance_api/app/parser_routes.py

```python
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
```

## Lr3/finance_api/app/reports.py

```python
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlmodel import Session, select

from app.db import get_session
from app.models import Category, Operation, OperationType, User
from app.security import get_current_user

router = APIRouter(prefix="/reports", tags=["Отчёты"])


class CategoryReport(BaseModel):
    category_id: int
    name: str
    expense: float
    monthly_limit: float | None
    remaining: float | None
    exceeded: bool


class MonthlyReport(BaseModel):
    year: int
    month: int
    income: float
    expense: float
    balance: float
    categories: list[CategoryReport]


@router.get("/monthly", response_model=MonthlyReport)
def monthly_report(year: int = Query(ge=2000, le=9998), month: int = Query(ge=1, le=12),
                   user: User = Depends(get_current_user), session: Session = Depends(get_session)) -> MonthlyReport:
    start = datetime(year, month, 1)
    end = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)
    operations = session.exec(select(Operation).where(
        Operation.user_id == user.id, Operation.operation_date >= start, Operation.operation_date < end,
    )).all()
    income = Decimal("0")
    expense = Decimal("0")
    spent = {}
    for operation in operations:
        amount = Decimal(str(operation.amount))
        if operation.operation_type == OperationType.income:
            income += amount
        else:
            expense += amount
            spent[operation.category_id] = spent.get(operation.category_id, Decimal("0")) + amount
    categories = []
    for category in session.exec(select(Category).where(Category.user_id == user.id)).all():
        total = spent.get(category.id, Decimal("0"))
        limit = Decimal(str(category.monthly_limit)) if category.monthly_limit is not None else None
        categories.append(CategoryReport(
            category_id=category.id, name=category.name, expense=float(total), monthly_limit=category.monthly_limit,
            remaining=float(limit - total) if limit is not None else None,
            exceeded=limit is not None and total > limit,
        ))
    return MonthlyReport(year=year, month=month, income=float(income), expense=float(expense),
                         balance=float(income - expense), categories=categories)
```

## Lr3/finance_api/app/security.py

```python
"""Пароли и JWT. Регистрация и проверка пользователя реализованы вручную."""
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from app.db import get_session
from app.models import User

SECRET_KEY = os.environ.get("JWT_SECRET", "")
if len(SECRET_KEY) < 32:
    raise RuntimeError("Задайте JWT_SECRET длиной не менее 32 символов в .env")
oauth2 = OAuth2PasswordBearer(tokenUrl="auth/token")


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 600_000)
    return f"pbkdf2_sha256$600000${salt}${digest.hex()}"


def verify_password(password: str, stored: str | None) -> bool:
    if not stored:
        return False  # У записей из старой практики пароля ещё нет.
    try:
        algorithm, iterations, salt, digest = stored.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(iterations))
        return hmac.compare_digest(actual.hex(), digest)
    except (ValueError, TypeError):
        return False


def create_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": str(user.id), "iat": now, "exp": now + timedelta(minutes=30),
         "version": user.token_version}, SECRET_KEY, algorithm="HS256",
    )


def get_current_user(token: str = Depends(oauth2), session: Session = Depends(get_session)) -> User:
    error = HTTPException(401, "Требуется действующий токен", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"],
                             options={"require": ["sub", "exp", "iat", "version"]})
        user = session.get(User, int(payload["sub"]))
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise error
    if user is None or user.token_version != payload["version"]:
        raise error
    return user
```

## Lr3/finance_api/app/tasks.py

```python
from requests import RequestException
from app.celery_app import celery_app
from app.parser_client import parse_via_service
from app.parser_models import ParseRequest


@celery_app.task(name="app.tasks.parse_url_task", autoretry_for=(RequestException,),
                 retry_backoff=2, retry_backoff_max=10, retry_jitter=False,
                 retry_kwargs={"max_retries": 2})
def parse_url_task(url: str) -> dict:
    return parse_via_service(ParseRequest(url=url))
```

## Lr3/finance_api/app/users.py

```python
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.db import get_session
from app.models import User, UserCreate, UserRead, UserReadWithRelations, UserUpdate, PasswordChange, Token
from app.security import create_token, get_current_user, hash_password, verify_password

router = APIRouter(tags=["Пользователи"])


@router.post("/auth/register", response_model=UserRead, status_code=201)
@router.post("/users", response_model=UserRead, status_code=201)
def register(data: UserCreate, session: Session = Depends(get_session)) -> User:
    user = User(email=str(data.email).lower(), full_name=data.full_name,
                hashed_password=hash_password(data.password))
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "Email уже зарегистрирован")
    session.refresh(user)
    return user


@router.post("/auth/token", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)) -> Token:
    user = session.exec(select(User).where(User.email == form.username.lower())).first()
    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(401, "Неверный email или пароль", headers={"WWW-Authenticate": "Bearer"})
    return Token(access_token=create_token(user))


@router.get("/users/me", response_model=UserReadWithRelations)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.post("/users/me/password", status_code=204)
def change_password(data: PasswordChange, user: User = Depends(get_current_user),
                    session: Session = Depends(get_session)) -> Response:
    if not verify_password(data.old_password, user.hashed_password):
        raise HTTPException(400, "Неверный текущий пароль")
    user.hashed_password = hash_password(data.new_password)
    user.token_version += 1  # Старые токены перестают действовать.
    session.add(user)
    session.commit()
    return Response(status_code=204)


@router.get("/users", response_model=list[UserRead])
def users(user: User = Depends(get_current_user), session: Session = Depends(get_session)) -> list[User]:
    return list(session.exec(select(User)).all())


@router.get("/users/{user_id}", response_model=UserRead)
def read_user(user_id: int, user: User = Depends(get_current_user),
              session: Session = Depends(get_session)) -> User:
    found = session.get(User, user_id)
    if found is None:
        raise HTTPException(404, "Пользователь не найден")
    return found


@router.patch("/users/{user_id}", response_model=UserRead)
def update_user(user_id: int, data: UserUpdate, user: User = Depends(get_current_user),
                session: Session = Depends(get_session)) -> User:
    if user_id != user.id:
        raise HTTPException(403, "Можно менять только свой профиль")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(user, key, str(value).lower() if key == "email" else value)
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "Email уже зарегистрирован")
    session.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int, user: User = Depends(get_current_user),
                session: Session = Depends(get_session)) -> Response:
    if user_id != user.id:
        raise HTTPException(403, "Можно удалить только свой профиль")
    if user.operations or user.categories:
        raise HTTPException(409, "Сначала удалите операции и категории")
    session.delete(user)
    session.commit()
    return Response(status_code=204)
```

## Lr3/docker-compose.yml

```yaml
services:
  db:
    image: postgres:16
    container_name: lr3-db
    restart: unless-stopped
    environment:
      POSTGRES_DB: personal_finance_lab3
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
    ports:
      - "127.0.0.1:${DB_PORT:-5434}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d personal_finance_lab3"]
      interval: 5s
      timeout: 3s
      retries: 15

  redis:
    image: redis:7-alpine
    container_name: lr3-redis
    restart: unless-stopped
    ports:
      - "127.0.0.1:${REDIS_PORT:-6379}:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 10

  migrate:
    build: ./finance_api
    command: python migrate.py
    environment:
      DATABASE_URL: postgresql://postgres:${POSTGRES_PASSWORD:-postgres}@db:5432/personal_finance_lab3
    depends_on:
      db:
        condition: service_healthy

  parser-service:
    build: ./parser_service
    container_name: lr3-parser-service
    restart: unless-stopped
    environment:
      DATABASE_URL: postgresql://postgres:${POSTGRES_PASSWORD:-postgres}@db:5432/personal_finance_lab3
      ROOT_PATH: ${PARSER_ROOT_PATH:-}
    depends_on:
      migrate:
        condition: service_completed_successfully
    ports:
      - "127.0.0.1:${PARSER_PORT:-8001}:8000"
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 10s
      timeout: 5s
      retries: 10

  finance-api:
    build: ./finance_api
    container_name: lr3-finance-api
    restart: unless-stopped
    environment: &finance-env
      DATABASE_URL: postgresql://postgres:${POSTGRES_PASSWORD:-postgres}@db:5432/personal_finance_lab3
      JWT_SECRET: ${JWT_SECRET:?Set JWT_SECRET in .env}
      ROOT_PATH: ${LR3_ROOT_PATH:-}
      PARSER_SERVICE_URL: http://parser-service:8000
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/0
      SCHEDULED_PARSE_URL: ${SCHEDULED_PARSE_URL:-https://www.worldbank.org/}
      PARSE_INTERVAL_SECONDS: ${PARSE_INTERVAL_SECONDS:-21600}
    depends_on:
      parser-service:
        condition: service_healthy
      redis:
        condition: service_healthy
    ports:
      - "127.0.0.1:${API_PORT:-8000}:8000"
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 10s
      timeout: 5s
      retries: 10

  lr1-api:
    build: ../Lr1/practice_1_3
    container_name: lr1-finance-api
    restart: unless-stopped
    environment:
      DATABASE_URL: postgresql://postgres:${POSTGRES_PASSWORD:-postgres}@db:5432/personal_finance_lab3
      JWT_SECRET: ${JWT_SECRET:?Set JWT_SECRET in .env}
      ROOT_PATH: ${LR1_ROOT_PATH:-}
    depends_on:
      migrate:
        condition: service_completed_successfully
    ports:
      - "127.0.0.1:${LR1_PORT:-8011}:8000"
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 10s
      timeout: 5s
      retries: 10

  celery-worker:
    build: ./finance_api
    container_name: lr3-celery-worker
    restart: unless-stopped
    command: celery -A app.celery_app:celery_app worker --loglevel=info --concurrency=2
    environment: *finance-env
    depends_on:
      parser-service:
        condition: service_healthy
      redis:
        condition: service_healthy

  celery-beat:
    build: ./finance_api
    container_name: lr3-celery-beat
    restart: unless-stopped
    command: celery -A app.celery_app:celery_app beat --loglevel=info --schedule=/tmp/celerybeat-schedule
    environment: *finance-env
    depends_on:
      parser-service:
        condition: service_healthy
      redis:
        condition: service_healthy

volumes:
  postgres_data:
```

## Lr3/finance_api/Dockerfile

```dockerfile
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY migrations ./migrations
COPY alembic.ini migrate.py .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Lr3/parser_service/Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
