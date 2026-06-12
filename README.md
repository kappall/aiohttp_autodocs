# aiohttp-autodocs

Automatic OpenAPI 3.1 documentation for aiohttp applications.

## Features

- Automatically discovers routes from `RouteTableDef` without manual registration
- `@docs()` decorator for adding summaries, tags, and request/response schemas
- Built-in support for Pydantic and SQLModel via `model_json_schema()`
- Serves a prebuilt `/openapi.json` spec with no runtime overhead
- Swagger UI available at `/docs`, including "Try it out" support
- Supports Bearer, API key, and OAuth2 security schemes
- Documentation can be disabled in production via config or environment variables
- No global state; the spec is attached to the `aiohttp.Application` instance
- WebSocket routes are detected automatically and excluded

## Installation

```bash
pip install aiohttp-autodocs            # base (no Pydantic)
pip install aiohttp-autodocs[pydantic]  # with Pydantic/SQLModel support
```

## Quick Start

```python
from aiohttp import web
from aiohttp_autodocs import docs, build_openapi, OpenAPIConfig

routes = web.RouteTableDef()

@docs(
    summary="List items",
    tags=["Items"],
    response=MyPydanticModel,
    response_list=True,
)
@routes.get("/items")
async def list_items(request: web.Request) -> web.Response:
    ...

@docs(
    summary="Create item",
    tags=["Items"],
    request_body=ItemCreateModel,
    responses={201: MyPydanticModel, 400: None},
    security=["BearerAuth"],
)
@routes.post("/items")
async def create_item(request: web.Request) -> web.Response:
    ...

app = web.Application()
app.add_routes(routes)

build_openapi(
    app,
    OpenAPIConfig(
        title="My API",
        version="1.0.0",
        servers=[{"url": "http://localhost:8080"}],
        security_schemes={
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            }
        },
    ),
    routes,
)

web.run_app(app)
```

Open http://localhost:8080/docs to view the documentation.

## `@docs()` Parameters

- `summary` (`str`): Short description shown in Swagger UI
- `description` (`str`): Longer Markdown description
- `tags` (`list[str]`): Groups endpoints in the UI
- `request_body` (`type | dict`): Pydantic model or raw JSON schema
- `response` (`type | dict`): Pydantic model or raw JSON schema (shorthand)
- `response_list` (`bool`): Wraps the response in an array schema
- `responses` (`dict[int, type | dict | None]`): Per-status responses (overrides `response`)
- `query_params` (`list[tuple]`): `(name, type, description, required)`
- `path_params` (`list[tuple]`): `(name, type, description)`; auto-detected from route
- `security` (`list[str | dict]`): References defined security schemes
- `deprecated` (`bool`): Marks endpoint as deprecated
- `include_in_schema` (`bool`): Set to `False` to exclude from docs
- `operation_id` (`str`): Custom operation ID

## `OpenAPIConfig` Parameters

- `title` (required): API title
- `version` (required): API version
- `description` (`str`): Optional description
- `servers` (`list`): Server definitions
- `docs_path` (`str`): Swagger UI path (default `/docs`)
- `spec_path` (`str`): OpenAPI spec path (default `/openapi.json`)
- `enabled` (`bool`): Enable or disable documentation
- `security_schemes` (`dict`): Security definitions
- `openapi_version` (`str`): OpenAPI version (default `3.1.0`)
- `contact` (`dict | None`): Contact information
- `license_info` (`dict | None`): License details
- `tags` (`list`): Global tag definitions
- `swagger_ui_cdn` (`str`): Swagger UI CDN URL

## Production Notes

- Disable docs with an environment flag:
  ```python
  OpenAPIConfig(enabled=os.getenv("DOCS_ENABLED", "true") == "true")
  ```
- Use a custom or internal CDN if needed
- Multiple apps in the same process remain isolated
- The OpenAPI spec is generated once at startup and served as cached bytes

## License

MIT