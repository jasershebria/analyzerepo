from __future__ import annotations

from typing import Generic, TypeVar
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

T = TypeVar("T")


class CamelModel(BaseModel):
    """Base model that serializes to camelCase for the Angular frontend."""
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class PagedResult(CamelModel, Generic[T]):
    total_count: int
    items: list[T]
