from datetime import date
from enum import Enum

from pydantic import BaseModel, Field


class OperationType(str, Enum):
    income = "income"
    expense = "expense"


class Category(BaseModel):
    id: int
    name: str = Field(..., min_length=2, max_length=50)
    monthly_limit: float | None = Field(default=None, ge=0)


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    monthly_limit: float | None = Field(default=None, ge=0)


class Tag(BaseModel):
    id: int
    name: str = Field(..., min_length=2, max_length=30)


class TagCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=30)


class Operation(BaseModel):
    id: int
    title: str = Field(..., min_length=2, max_length=100)
    amount: float = Field(..., gt=0)
    operation_type: OperationType
    operation_date: date
    category: Category
    tags: list[Tag] = Field(default_factory=list)
    description: str | None = Field(default=None, max_length=255)


class OperationCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=100)
    amount: float = Field(..., gt=0)
    operation_type: OperationType
    operation_date: date
    category: Category
    tags: list[TagCreate] = Field(default_factory=list)
    description: str | None = Field(default=None, max_length=255)
