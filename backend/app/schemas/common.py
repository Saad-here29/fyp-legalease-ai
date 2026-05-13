"""Shared Pydantic schemas used across the API."""

from typing import Generic, TypeVar
from pydantic import BaseModel, Field, ConfigDict

T = TypeVar("T")


class APIModel(BaseModel):
    """Base for all DTOs — enables ORM-mode and trims whitespace."""

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)


class ErrorPayload(BaseModel):
    code: str
    message: str
    hint: str


class ErrorResponse(BaseModel):
    error: ErrorPayload


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def build(cls, items: list[T], total: int, params: PaginationParams) -> "Page[T]":
        pages = (total + params.page_size - 1) // params.page_size if total else 0
        return cls(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
            pages=pages,
        )
