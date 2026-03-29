from fastapi import FastAPI, HTTPException, status
from requests import RequestException

from app.db import get_session, init_db
from app.models import ParseRequest, ParseResponse
from app.services import parse_url_and_save

app = FastAPI(
    title="Personal Finance Parser Service",
    description="HTTP parser service for Docker-based laboratory work 3.",
    version="1.0.0",
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def healthcheck() -> dict:
    return {"status": "ok", "service": "parser-service"}


@app.post("/parse", response_model=ParseResponse, status_code=status.HTTP_201_CREATED)
def parse(payload: ParseRequest) -> ParseResponse:
    try:
        with get_session() as session:
            page = parse_url_and_save(payload.url, session)
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
