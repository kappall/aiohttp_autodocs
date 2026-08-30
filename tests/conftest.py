from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer
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


@pytest.fixture
async def aiohttp_client() -> AsyncIterator[Callable[[web.Application], Awaitable[TestClient]]]:
    clients: list[TestClient] = []
    async def _create_client(app: web.Application) -> TestClient:
        server = TestServer(app)
        client = TestClient(server)
        await client.start_server()
        clients.append(client)
        return client
    yield _create_client
    for client in clients:
        await client.close()
