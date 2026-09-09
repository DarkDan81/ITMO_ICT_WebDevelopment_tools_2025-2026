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
