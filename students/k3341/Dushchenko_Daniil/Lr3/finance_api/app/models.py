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
