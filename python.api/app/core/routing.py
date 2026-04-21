from __future__ import annotations

from fastapi.routing import APIRoute
from fastapi import Request
from fastapi.responses import Response
from typing import Callable


class CamelCaseRoute(APIRoute):
    """Serializes all Pydantic response models using their camelCase aliases."""

    def get_route_handler(self) -> Callable:
        original = super().get_route_handler()

        async def route_handler(request: Request) -> Response:
            response = await original(request)
            return response

        return route_handler

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("response_model_by_alias", True)
        super().__init__(*args, **kwargs)
