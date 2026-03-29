from datetime import datetime

from sqlmodel import Field, SQLModel


class ParsedPage(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    url: str = Field(index=True, max_length=500)
    source_name: str = Field(max_length=100)
    title: str = Field(max_length=500)
    fetch_method: str = Field(max_length=30, index=True)
    status_code: int
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
