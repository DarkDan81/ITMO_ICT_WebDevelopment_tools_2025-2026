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
