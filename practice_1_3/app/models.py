from datetime import datetime
from enum import Enum

from pydantic import Field as PydanticField
from sqlmodel import Field, Relationship, SQLModel


class OperationType(str, Enum):
    income = "income"
    expense = "expense"


class UserBase(SQLModel):
    email: str = Field(index=True, unique=True, max_length=255)
    full_name: str = Field(max_length=100)


class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    categories: list["Category"] = Relationship(back_populates="user")
    operations: list["Operation"] = Relationship(back_populates="user")


class UserCreate(UserBase):
    pass


class UserUpdate(SQLModel):
    email: str | None = Field(default=None, max_length=255)
    full_name: str | None = Field(default=None, max_length=100)


class CategoryBase(SQLModel):
    name: str = Field(max_length=50)
    monthly_limit: float | None = Field(default=None, ge=0)
    user_id: int | None = Field(default=None, foreign_key="user.id")


class Category(CategoryBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user: User | None = Relationship(back_populates="categories")
    operations: list["Operation"] = Relationship(back_populates="category")


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=50)
    monthly_limit: float | None = Field(default=None, ge=0)
    user_id: int | None = None


class TagBase(SQLModel):
    name: str = Field(max_length=30, unique=True)


class OperationTagLink(SQLModel, table=True):
    operation_id: int | None = Field(
        default=None,
        foreign_key="operation.id",
        primary_key=True,
    )
    tag_id: int | None = Field(default=None, foreign_key="tag.id", primary_key=True)
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    priority: int | None = Field(default=None, ge=1, le=5)


class Tag(TagBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    operations: list["Operation"] = Relationship(
        back_populates="tags",
        link_model=OperationTagLink,
    )


class TagCreate(TagBase):
    pass


class TagUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=30)


class OperationBase(SQLModel):
    title: str = Field(max_length=100)
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


class OperationTagAssignment(SQLModel):
    tag_id: int
    priority: int | None = Field(default=None, ge=1, le=5)


class OperationCreate(OperationBase):
    tags: list[OperationTagAssignment] = PydanticField(default_factory=list)


class OperationUpdate(SQLModel):
    title: str | None = Field(default=None, max_length=100)
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
