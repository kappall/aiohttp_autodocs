from __future__ import annotations

import inspect
import json
import logging
import re
from typing import Any

from aiohttp import web

from .config import OpenAPIConfig
from .decorator import OPENAPI_META_ATTR
from .schema import extract_schema

logger = logging.getLogger(__name__)

_PATH_PARAM_RE = re.compile(r"\{(\w+)\}")
_WS_PATH_RE = re.compile(r"(^|/)(ws|websocket)(/|$)", re.IGNORECASE)

_STATUS_DESCRIPTIONS: dict[int, str] = {
    200: "Success",
    201: "Created",
    204: "No content",
    400: "Bad request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not found",
    409: "Conflict",
    422: "Unprocessable entity",
    500: "Internal server error",
    503: "Service unavailable",
}

_ERROR_SCHEMA = {
    "type": "object",
    "properties": {"error": {"type": "string"}},
}


def build_spec(config: OpenAPIConfig, route_tables: list[web.RouteTableDef]) -> bytes:
    """Build a frozen OpenAPI spec from *route_tables* and return UTF-8 JSON bytes."""
    components_schemas: dict[str, Any] = {}
    paths: dict[str, Any] = {}

    for route_table in route_tables:
        for route_def in route_table._items:  # noqa: SLF001
            if isinstance(route_def, web.RouteDef):
                _process_route(route_def, paths, components_schemas)

    info: dict[str, Any] = {"title": config.title, "version": config.version}
    if config.description:
        info["description"] = config.description
    if config.contact:
        info["contact"] = config.contact
    if config.license_info:
        info["license"] = config.license_info

    spec: dict[str, Any] = {"openapi": config.openapi_version, "info": info}
    if config.servers:
        spec["servers"] = config.servers
    if config.tags:
        spec["tags"] = config.tags

    components: dict[str, Any] = {}
    if config.security_schemes:
        components["securitySchemes"] = config.security_schemes
    if components_schemas:
        components["schemas"] = components_schemas
    if components:
        spec["components"] = components

    spec["paths"] = paths

    n_ops = sum(len(ops) for ops in paths.values())
    logger.info("aiohttp-autodocs: %d operation(s) across %d path(s).", n_ops, len(paths))

    return json.dumps(spec, indent=2, default=str).encode("utf-8")


def _process_route(
    route_def: Any,
    paths: dict[str, Any],
    components: dict[str, Any],
) -> None:
    handler = route_def.handler
    meta: dict[str, Any] | None = getattr(handler, OPENAPI_META_ATTR, None)

    if meta is None or not meta.get("include_in_schema", True):
        return

    path: str = route_def.path
    method_raw: str = route_def.method
    if method_raw == "*":
        return
    method: str = method_raw.lower()

    if _is_websocket_route(path, handler):
        return

    operation = _build_operation(meta, method, path, components)

    if path not in paths:
        paths[path] = {}
    paths[path][method] = operation

    logger.debug("Registered %s %s → %s", method.upper(), path, handler.__name__)


def _build_operation(
    meta: dict[str, Any],
    method: str,
    path: str,
    components: dict[str, Any],
) -> dict[str, Any]:
    op: dict[str, Any] = {}

    if meta["summary"]:
        op["summary"] = meta["summary"]
    if meta["description"]:
        op["description"] = meta["description"]
    if meta["tags"]:
        op["tags"] = meta["tags"]
    if meta["deprecated"]:
        op["deprecated"] = True

    op["operationId"] = meta.get("operation_id") or _make_operation_id(method, path)

    if meta.get("security") is not None:
        op["security"] = [
            {s: []} if isinstance(s, str) else s for s in meta["security"]
        ]

    parameters = _build_parameters(meta, path)
    if parameters:
        op["parameters"] = parameters

    request_body_model = meta.get("request_body")
    if request_body_model is not None:
        schema = extract_schema(request_body_model, components)
        if schema:
            op["requestBody"] = {
                "required": True,
                "content": {"application/json": {"schema": schema}},
            }

    op["responses"] = _build_responses(meta, method, components)
    return op


def _build_parameters(meta: dict[str, Any], path: str) -> list[dict[str, Any]]:
    parameters: list[dict[str, Any]] = []
    declared = {p[0]: p for p in meta.get("path_params", [])}

    for param_name in _PATH_PARAM_RE.findall(path):
        if param_name in declared:
            decl = declared[param_name]
            entry: dict[str, Any] = {
                "name": decl[0],
                "in": "path",
                "required": True,
                "schema": {"type": decl[1] if len(decl) > 1 else "string"},
            }
            if len(decl) > 2 and decl[2]:
                entry["description"] = decl[2]
        else:
            entry = {
                "name": param_name,
                "in": "path",
                "required": True,
                "schema": {"type": "string"}
            }
        parameters.append(entry)

    for qp in meta.get("query_params", []):
        qp_entry: dict[str, Any] = {
            "name": qp[0],
            "in": "query",
            "required": bool(qp[3]) if len(qp) > 3 else False,
            "schema": {"type": qp[1] if len(qp) > 1 else "string"},
        }
        if len(qp) > 2 and qp[2]:
            qp_entry["description"] = qp[2]
        parameters.append(qp_entry)

    return parameters


def _build_responses(
    meta: dict[str, Any],
    method: str,
    components: dict[str, Any],
) -> dict[str, Any]:
    # Priority: responses dict > response shorthand > bare 200
    responses: dict[str, Any] = {}

    if meta.get("responses"):
        for status_code, response_model in meta["responses"].items():
            desc = _STATUS_DESCRIPTIONS.get(status_code, "Response")
            if response_model is None:
                responses[str(status_code)] = {"description": desc}
            else:
                schema = extract_schema(response_model, components)
                responses[str(status_code)] = (
                    {"description": desc, "content": {"application/json": {"schema": schema}}}
                    if schema else {"description": desc}
                )
    elif meta.get("response") is not None:
        schema = extract_schema(meta["response"], components)
        if schema and meta.get("response_list"):
            schema = {"type": "array", "items": schema}
        default_code = "201" if method == "post" else "200"
        responses[default_code] = {
            "description": "Success",
            "content": {"application/json": {"schema": schema}},
        }
    else:
        responses["200"] = {"description": "Success"}

    if "500" not in responses:
        responses["500"] = {
            "description": "Internal server error",
            "content": {"application/json": {"schema": _ERROR_SCHEMA}},
        }

    return responses


def _is_websocket_route(path: str, handler: Any) -> bool:
    annotations = getattr(handler, "__annotations__", {})
    return_hint = annotations.get("return")
    if return_hint is not None and (
        return_hint is web.WebSocketResponse or "WebSocketResponse" in str(return_hint)
    ):
        return True
    try:
        source = inspect.getsource(handler)
        if "WebSocketResponse" in source:
            return True
    except (TypeError, OSError):
        pass

    return _WS_PATH_RE.search(path) is not None


def _make_operation_id(method: str, path: str) -> str:
    clean = re.sub(r"[{}]", "", path)
    parts = [p for p in re.split(r"[/_\-]+", clean) if p]
    return method + "".join(p.capitalize() for p in parts)
