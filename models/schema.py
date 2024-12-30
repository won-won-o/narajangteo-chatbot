from pydantic import BaseModel
from typing import Any, Optional


class QueryResult(BaseModel):
    content: str
    metadata: dict[str, Any]
    score: Optional[float] = None


class ProcessedResult(BaseModel):
    results: list[QueryResult]
    source_type: str
    raw_response: Optional[Any] = None
