# aiohttp-autodocs

A zero-overhead, non-invasive OpenAPI 3.1.0 documentation generator for `aiohttp`.

It gives you the beautiful Swagger UI and Pydantic integration of modern frameworks (like FastAPI), but preserves the raw, unhindered speed and stability of bare `aiohttp`.

## Design Philosophy

This package was built with a specific set of architectural goals in mind to ensure it remains safe and performant in production environments:

1. **Absolute Zero Runtime Overhead**
   Many OpenAPI solutions intercept every HTTP request at runtime to perform validation and dependency injection, adding CPU overhead to every API call.
   `aiohttp-autodocs` operates entirely at **boot time**. It builds the OpenAPI spec once, freezes it to raw bytes in memory, and steps out of the way. When a user hits an endpoint, the decorator does absolutely nothing.

2. **Native Pydantic v2 Support**
   If your project uses modern `pydantic` (or `sqlmodel`), you shouldn't have to rewrite your schemas into another validation library just to generate documentation. Our package natively understands Pydantic v2 (including nested `$defs`), while degrading gracefully to raw Python dictionaries if Pydantic isn't installed.

3. **Non-Invasive Architecture**
   We don't force you to use Class-Based Views or wrap your handlers so heavily that you lose access to the raw `web.Request` object. Your routes remain pure `aiohttp` async functions.

4. **No YAML-in-Docstrings**
   Older tools rely on writing OpenAPI YAML directly inside your Python function docstrings. This is error-prone, hard to format, and invisible to IDE type-checkers. We use a strongly typed Python decorator (`@docs()`) so your IDE catches mistakes instantly.

## Installation

```bash
# If you want Pydantic support
pip install aiohttp-autodocs[pydantic]

# If you only want raw dictionary schemas
pip install aiohttp-autodocs
```

## Quick Start

### 1. Decorate your routes

The `@docs` decorator attaches metadata to your handler. It **must** be placed above the `aiohttp` route decorator.

```python
from aiohttp import web
from aiohttp_autodocs import docs
from pydantic import BaseModel

class AlarmSchema(BaseModel):
    id: int
    message: str

alarm_routes = web.RouteTableDef()

@docs(
    summary="List all alarms",
    tags=["Alarms"],
    response=AlarmSchema,
    response_list=True,
    security=["BearerAuth"]
)
@alarm_routes.get("/api/v1/alarms")
async def get_alarms(request: web.Request) -> web.Response:
    return web.json_response([{"id": 1, "message": "High CPU"}])
```

### 2. Build the spec at startup

In your application factory (e.g., `create_app()`), call `build_openapi` *after* you've added all your routes.

```python
from aiohttp_autodocs import build_openapi, OpenAPIConfig

app = web.Application()
app.add_routes(alarm_routes)

build_openapi(
    app,
    OpenAPIConfig(
        title="My API",
        version="1.0.0",
        enabled=True,
        security_schemes={
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            }
        }
    ),
    alarm_routes  # Pass all your RouteTableDefs here
)

web.run_app(app)
```

### 3. View your docs

Start your server and visit:
* Interactive Swagger UI: `http://localhost:8080/docs`
* Raw OpenAPI JSON: `http://localhost:8080/openapi.json`

## Contributing

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for development setup (`uv`), testing, and workflow guidelines.