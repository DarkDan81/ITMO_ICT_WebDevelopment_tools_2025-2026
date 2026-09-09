# Исходный код LR1

Код соответствует текущим файлам проекта.

## Lr1/practice_1_3/app/db.py

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

## Lr1/practice_1_3/app/finance.py

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

## Lr1/practice_1_3/app/main.py

```python
import os
from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlmodel import Session

from app.db import get_session
from app.users import router as users_router
from app.finance import router as finance_router
from app.reports import router as reports_router

app = FastAPI(title="Личные финансы — ЛР1", version="2.0.0", root_path=os.getenv("ROOT_PATH", ""))
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
```

## Lr1/practice_1_3/app/models.py

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

## Lr1/practice_1_3/app/reports.py

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

## Lr1/practice_1_3/app/security.py

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

## Lr1/practice_1_3/app/users.py

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

## Lr1/practice_1_3/migrations/env.py

```python
from logging.config import fileConfig
import os

from dotenv import load_dotenv
from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
from sqlmodel import SQLModel

from app import models  # noqa: F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
load_dotenv()
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = SQLModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

## Lr1/practice_1_3/migrations/versions/a83973acb777_initial_schema.py

```python
"""initial schema

Revision ID: a83973acb777
Revises:
Create Date: 2026-03-29 22:31:23.402306

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'a83973acb777'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "user",
        sa.Column("email", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("full_name", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_email"), "user", ["email"], unique=True)

    op.create_table(
        "tag",
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=30), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "category",
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column("monthly_limit", sa.Float(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "operation",
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("operation_type", sa.Enum("income", "expense", name="operationtype"), nullable=False),
        sa.Column("operation_date", sa.DateTime(), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["category.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "operationtaglink",
        sa.Column("operation_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.Column("assigned_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["operation_id"], ["operation.id"]),
        sa.ForeignKeyConstraint(["tag_id"], ["tag.id"]),
        sa.PrimaryKeyConstraint("operation_id", "tag_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("operationtaglink")
    op.drop_table("operation")
    op.drop_table("category")
    op.drop_table("tag")
    op.drop_index(op.f("ix_user_email"), table_name="user")
    op.drop_table("user")

    operation_type = sa.Enum("income", "expense", name="operationtype")
    operation_type.drop(op.get_bind(), checkfirst=True)
```

## Lr1/practice_1_3/migrations/versions/b8d18406f516_add_priority_to_operation_tag_link.py

```python
"""add priority to operation tag link

Revision ID: b8d18406f516
Revises: a83973acb777
Create Date: 2026-03-29 22:31:27.271934

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'b8d18406f516'
down_revision: Union[str, Sequence[str], None] = 'a83973acb777'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "operationtaglink",
        sa.Column("priority", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("operationtaglink", "priority")
```

## Lr1/practice_1_3/migrations/versions/c901_auth.py

```python
"""Пароли и отзыв токенов после смены пароля.

Старые учебные пользователи сохраняются без пароля: вход для них закрыт.
Для проверки авторизации нужно зарегистрировать нового пользователя.
"""
from alembic import op
import sqlalchemy as sa

revision = "c901_auth"
down_revision = "b8d18406f516"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("user", sa.Column("hashed_password", sa.String(255), nullable=True))
    op.add_column("user", sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("user", "token_version")
    op.drop_column("user", "hashed_password")
```
