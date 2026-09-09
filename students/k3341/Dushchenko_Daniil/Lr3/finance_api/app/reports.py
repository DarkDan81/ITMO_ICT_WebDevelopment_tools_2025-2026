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
