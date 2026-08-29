from __future__ import annotations

import pytest
from aiohttp import web

from aiohttp_autodocs import OpenAPIConfig, build_openapi, docs
from tests.conftest import SampleItem


async def test_build_openapi_routes(aiohttp_client, default_config: OpenAPIConfig):
    app = web.Application()
    routes = web.RouteTableDef()

    @docs(summary="Get items", response=SampleItem)
    @routes.get("/items")
    async def get_items(request: web.Request) -> web.Response:
        return web.json_response({"id": 1, "name": "Item"})

    app.add_routes(routes)
    build_openapi(app, default_config, routes)

    client = await aiohttp_client(app)

    resp = await client.get("/openapi.json")
    assert resp.status == 200
    assert resp.content_type == "application/json"
    data = await resp.json()
    assert data["info"]["title"] == "Test API"
    assert "/items" in data["paths"]

    docs_resp = await client.get("/docs")
    assert docs_resp.status == 200
    assert docs_resp.content_type == "text/html"
    html_text = await docs_resp.text()
    assert "SwaggerUIBundle" in html_text
    assert "/openapi.json" in html_text

    redirect_resp = await client.get("/docs/", allow_redirects=False)
    assert redirect_resp.status in (301, 302, 307, 308)
    assert redirect_resp.headers["Location"] == "/docs"


def test_build_openapi_double_call_raises(default_config: OpenAPIConfig):
    app = web.Application()
    routes = web.RouteTableDef()

    build_openapi(app, default_config, routes)
    with pytest.raises(RuntimeError, match="has already been called on this application"):
        build_openapi(app, default_config, routes)


async def test_build_openapi_disabled(aiohttp_client):
    app = web.Application()
    routes = web.RouteTableDef()
    config = OpenAPIConfig(title="Test", version="1.0.0", enabled=False)

    build_openapi(app, config, routes)

    client = await aiohttp_client(app)
    resp_spec = await client.get("/openapi.json")
    assert resp_spec.status == 404

    resp_docs = await client.get("/docs")
    assert resp_docs.status == 404
