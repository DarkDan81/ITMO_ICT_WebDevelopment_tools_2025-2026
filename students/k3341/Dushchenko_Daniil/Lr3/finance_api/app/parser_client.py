import os

import requests

from app.parser_models import ParseRequest

PARSER_SERVICE_URL = os.getenv("PARSER_SERVICE_URL", "http://parser-service:8000")
PARSER_TIMEOUT = int(os.getenv("PARSER_TIMEOUT", "30"))


def parse_via_service(payload: ParseRequest) -> dict:
    response = requests.post(
        f"{PARSER_SERVICE_URL}/parse",
        json=payload.model_dump(),
        timeout=PARSER_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()
