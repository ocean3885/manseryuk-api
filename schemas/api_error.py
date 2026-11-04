from typing import Any, Literal
from pydantic import BaseModel, Field


class ErrorItem(BaseModel):
    field: str | None = None
    location: list[str | int] = Field(default_factory=list)
    code: str
    message: str
    constraints: dict[str, Any] = Field(default_factory=dict)


class ApiErrorResponse(BaseModel):
    status: Literal['error'] = 'error'
    code: str
    message: str
    errors: list[ErrorItem]
    detail: Any
    correct_usage: str
    example: str
    required_fields: dict[str, str]
