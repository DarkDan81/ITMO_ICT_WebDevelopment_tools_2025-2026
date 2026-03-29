from datetime import datetime

from pydantic import BaseModel, Field as PydanticField
from sqlmodel import Field, SQLModel


class ParsedPage(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    url: str = Field(index=True, max_length=500)
    source_name: str = Field(max_length=100)
    title: str = Field(max_length=500)
    fetch_method: str = Field(max_length=30, index=True)
    status_code: int
    fetched_at: datetime = Field(default_factory=datetime.utcnow)


class ParseRequest(BaseModel):
    url: str = PydanticField(..., max_length=500)


class ParseResponse(BaseModel):
    message: str
    url: str
    title: str
    source_name: str
    status_code: int
    fetch_method: str
