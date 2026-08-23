from __future__ import annotations
"""
@docs() : non-invasive decorator for attaching OpenAPI metadata to handlers.
"""

from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

#: Attribute name used to store metadata on the handler function.
#: Prefixed with the package name to avoid collisions with other libraries.
OPENAPI_META_ATTR = "__aiohttp_autodocs__"


def docs(
    *,
    summary: str = "",
    description: str = "",
    tags: list[str] | None = None,
    request_body: type | dict[str, Any] | None = None,
    response: type | dict[str, Any] | None = None,
    response_list: bool = False,
    responses: dict[int, type | dict[str, Any] | None] | None = None,
    query_params: list[tuple[str | bool, ...]] | None = None,
    path_params: list[tuple[str, ...]] | None = None,
    security: list[str | dict[str, Any]] | None = None,
    deprecated: bool = False,
    include_in_schema: bool = True,
    operation_id: str | None = None,
) -> Callable[[F], F]:
    """
    Decorator that attaches OpenAPI metadata to an aiohttp route handler.

    **Must be placed ABOVE** the ``@route_table.method()`` decorator so that
    the metadata is visible on the function object that ends up stored in the
    route table.

    Example::

        @docs(
            summary="Create alarm",
            description="Creates a new alarm and broadcasts it via WebSocket.",
            tags=["Alarms"],
            request_body=AlarmCreateSchema,
            responses={
                201: Alarm,
                400: None,
                500: None,
            },
            security=["BearerAuth"],
        )
        @alarm_routes.post(f"{PREFIX}/alarms")
        async def create_alarm(request: web.Request) -> web.Response:
            ...

    Parameters
    ----------
    summary:
        Short, one-line description shown as the route title in Swagger UI.
    description:
        Longer Markdown description shown in the expanded route panel.
    tags:
        Tag names used to group routes in the UI, e.g. ``["Alarms"]``.
    request_body:
        A Pydantic ``BaseModel`` subclass (or SQLModel) whose
        ``model_json_schema()`` will be used, **or** a plain dict containing
        a raw JSON Schema object.
    response:
        Shorthand for a single success response model (Pydantic class or
        dict schema).  The status code defaults to ``200`` for non-POST
        methods and ``201`` for POST.  Use ``responses`` for multiple codes.
    response_list:
        When ``True``, wraps the ``response`` schema in
        ``{"type": "array", "items": <schema>}``.
    responses:
        Fine-grained per-status-code responses.  Keys are HTTP status code
        integers; values are Pydantic model classes, raw dicts, or ``None``
        (for responses with no body).  Takes precedence over ``response``.
    query_params:
        List of tuples describing query parameters::

            query_params=[
                ("severity", "string",  "Filter by severity", False),
                ("limit",    "integer", "Max results",        False),
            ]

        Each tuple: ``(name, openapi_type, description, required)``.
        ``description`` and ``required`` are optional (default ``""`` / ``False``).
    path_params:
        Explicit path parameter declarations::

            path_params=[("alarm_id", "integer", "The alarm's primary key")]

        Each tuple: ``(name, openapi_type, description)``.
        If omitted, path params are auto-detected from the route path pattern
        (``{param_name}``) and typed as ``string``.
    security:
        List of security scheme names (strings) or full security requirement
        objects (dicts).  Names must match keys in
        :attr:`OpenAPIConfig.security_schemes`::

            security=["BearerAuth"]
    deprecated:
        When ``True``, marks the operation as deprecated in the spec.
    include_in_schema:
        When ``False``, this route is silently excluded from the spec.
        Useful for internal or diagnostic routes.
    operation_id:
        Explicit ``operationId`` string.  Auto-generated from method + path
        if not provided (e.g. ``getApiV1AlarmsAlarmId``).
    """

    def decorator(func: F) -> F:
        setattr(func, OPENAPI_META_ATTR, {
            "summary": summary,
            "description": description,
            "tags": list(tags) if tags else [],
            "request_body": request_body,
            "response": response,
            "response_list": response_list,
            "responses": dict(responses) if responses else {},
            "query_params": list(query_params) if query_params else [],
            "path_params": list(path_params) if path_params else [],
            "security": list(security) if security is not None else None,
            "deprecated": deprecated,
            "include_in_schema": include_in_schema,
            "operation_id": operation_id,
        })
        return func

    return decorator
