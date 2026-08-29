from __future__ import annotations

import json

from aiohttp import web

from aiohttp_autodocs.config import OpenAPIConfig
from aiohttp_autodocs.decorator import docs
from aiohttp_autodocs.scanner import _is_websocket_route, _make_operation_id, build_spec
from tests.conftest import SampleItem


def test_make_operation_id():
    assert _make_operation_id("get", "/api/v1/users") == "getApiV1Users"
    assert _make_operation_id("post", "/users/{user_id}/items") == "postUsersUserIdItems"
    assert _make_operation_id("delete", "/item_name") == "deleteItemName"


def test_is_websocket_route():
    async def ws_handler_annotated(request: web.Request) -> web.WebSocketResponse:
        return web.WebSocketResponse()

    async def normal_handler(request: web.Request) -> web.Response:
        return web.Response(text="ok")

    assert _is_websocket_route("/ws", normal_handler) is True
    assert _is_websocket_route("/api/ws", normal_handler) is True
    assert _is_websocket_route("/ws/feed", normal_handler) is True
    assert _is_websocket_route("/websocket", normal_handler) is True
    assert _is_websocket_route("/api/websocket/chat", normal_handler) is True

    assert _is_websocket_route("/news", normal_handler) is False
    assert _is_websocket_route("/api/v1/news", normal_handler) is False
    assert _is_websocket_route("/password/reset", normal_handler) is False

    assert _is_websocket_route("/chat", ws_handler_annotated) is True


def test_build_spec_basic(default_config: OpenAPIConfig):
    routes = web.RouteTableDef()

    @docs(
        summary="List items",
        tags=["Items"],
        response=SampleItem,
        response_list=True,
    )
    @routes.get("/items")
    async def list_items(request: web.Request) -> web.Response:
        return web.json_response([])

    @docs(
        summary="Create item",
        tags=["Items"],
        request_body=SampleItem,
        responses={201: SampleItem, 400: None},
    )
    @routes.post("/items")
    async def create_item(request: web.Request) -> web.Response:
        return web.json_response({}, status=201)

    spec_bytes = build_spec(default_config, [routes])
    spec = json.loads(spec_bytes.decode("utf-8"))

    assert spec["openapi"] == "3.1.0"
    assert spec["info"]["title"] == "Test API"
    assert "/items" in spec["paths"]
    assert "get" in spec["paths"]["/items"]
    assert "post" in spec["paths"]["/items"]
    assert spec["paths"]["/items"]["get"]["summary"] == "List items"
    assert spec["paths"]["/items"]["get"]["tags"] == ["Items"]
    assert "SampleItem" in spec["components"]["schemas"]


def test_build_spec_skips_static_and_wildcard(default_config: OpenAPIConfig, tmp_path):
    routes = web.RouteTableDef()

    static_dir = tmp_path / "static"
    static_dir.mkdir()
    routes.static("/static", str(static_dir))

    @docs(summary="Catch all")
    @routes.route("*", "/catchall")
    async def catchall(request: web.Request) -> web.Response:
        return web.Response(text="catchall")

    @docs(summary="Health")
    @routes.get("/health")
    async def health(request: web.Request) -> web.Response:
        return web.Response(text="ok")

    spec_bytes = build_spec(default_config, [routes])
    spec = json.loads(spec_bytes.decode("utf-8"))

    assert "/static" not in spec["paths"]
    assert "/catchall" not in spec["paths"]
    assert "/health" in spec["paths"]


def test_build_spec_parameters_and_security(default_config: OpenAPIConfig):
    routes = web.RouteTableDef()

    @docs(
        summary="Get item",
        path_params=[("item_id", "integer", "The item identifier")],
        query_params=[
            ("include_details", "boolean", "Include detailed specs", False),
        ],
        security=["BearerAuth", {"ApiKey": []}],
    )
    @routes.get("/items/{item_id}")
    async def get_item(request: web.Request) -> web.Response:
        return web.Response(text="ok")

    spec_bytes = build_spec(default_config, [routes])
    spec = json.loads(spec_bytes.decode("utf-8"))

    op = spec["paths"]["/items/{item_id}"]["get"]
    assert len(op["parameters"]) == 2

    path_p = next(p for p in op["parameters"] if p["in"] == "path")
    assert path_p["name"] == "item_id"
    assert path_p["schema"]["type"] == "integer"
    assert path_p["description"] == "The item identifier"
    assert path_p["required"] is True

    query_p = next(p for p in op["parameters"] if p["in"] == "query")
    assert query_p["name"] == "include_details"
    assert query_p["schema"]["type"] == "boolean"
    assert query_p["required"] is False

    assert op["security"] == [{"BearerAuth": []}, {"ApiKey": []}]
