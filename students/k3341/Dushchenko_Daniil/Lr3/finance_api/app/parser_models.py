from pydantic import BaseModel, Field


class ParseRequest(BaseModel):
    url: str = Field(..., max_length=500)


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
