from __future__ import annotations

import pytest
from aiohttp import web
from pydantic import BaseModel, Field

from aiohttp_autodocs.config import OpenAPIConfig


class SampleItem(BaseModel):
    id: int = Field(..., description="Unique ID")
    name: str = Field(..., description="Item name")


class SampleNested(BaseModel):
    title: str
    item: SampleItem


@pytest.fixture
def default_config() -> OpenAPIConfig:
    return OpenAPIConfig(
        title="Test API",
        version="1.0.0",
        description="A test API instance",
    )


@pytest.fixture
def sample_app() -> web.Application:
    return web.Application()
