from aiohttp import web
from pydantic import BaseModel, Field
from aiohttp_autodocs import OpenAPIConfig, build_openapi, docs


class ItemCreate(BaseModel):
    name: str = Field(..., example="Wireless Mouse", description="Item title")
    price: float = Field(..., gt=0, example=29.99, description="Price in USD")
    category: str = Field(default="electronics", example="electronics")


class ItemOut(BaseModel):
    id: int = Field(..., example=101)
    name: str = Field(..., example="Wireless Mouse")
    price: float = Field(..., example=29.99)
    category: str = Field(..., example="electronics")


class ErrorResponse(BaseModel):
    error: str = Field(..., example="Item not found")
    code: int = Field(..., example=404)

ITEMS: dict[int, dict] = {
    1: {"id": 1, "name": "Mechanical Keyboard", "price": 89.99, "category": "electronics"},
}

routes = web.RouteTableDef()


# Example 1: query_params, response, response_list, tags, summary, description
@docs(
    summary="List all items",
    description="Retrieve a paginated and filtered list of items in the catalog.",
    tags=["Items"],
    query_params=[
        ("category", "string", "Filter items by category", False),
        ("limit", "integer", "Maximum number of items to return", False),
        ("in_stock_only", "boolean", "Only return items currently in stock", False),
    ],
    response=ItemOut,
    response_list=True,
)
@routes.get("/api/v1/items")
async def list_items(request: web.Request) -> web.Response:
    category = request.query.get("category")
    items = list(ITEMS.values())
    if category:
        items = [i for i in items if i["category"] == category]
    return web.json_response(items)


# Example 2: request_body, responses (fine-grained), security, operation_id
@docs(
    summary="Create a new item",
    description="Adds a new item to the catalog. Requires an authenticated Bearer token.",
    tags=["Items"],
    operation_id="createNewCatalogItem",
    request_body=ItemCreate,
    responses={
        201: ItemOut,
        400: ErrorResponse,
        401: None,
    },
    security=["BearerAuth"],
)
@routes.post("/api/v1/items")
async def create_item(request: web.Request) -> web.Response:
    data = await request.json()
    new_id = max(ITEMS.keys(), default=0) + 1
    item = {"id": new_id, **data}
    ITEMS[new_id] = item
    return web.json_response(item, status=201)


# Example 3: path_params, responses (multi-status), security with object scope
@docs(
    summary="Get item by ID",
    description="Fetch full details for a single item by its ID.",
    tags=["Items"],
    path_params=[
        ("item_id", "integer", "The unique integer ID of the item"),
    ],
    responses={
        200: ItemOut,
        404: ErrorResponse,
    },
    security=[{"ApiKeyAuth": []}],
)
@routes.get("/api/v1/items/{item_id}")
async def get_item(request: web.Request) -> web.Response:
    try:
        item_id = int(request.match_info["item_id"])
    except ValueError:
        return web.json_response({"error": "Invalid item ID", "code": 400}, status=400)

    item = ITEMS.get(item_id)
    if not item:
        return web.json_response({"error": "Item not found", "code": 404}, status=404)
    return web.json_response(item)


# Example 4: deprecated=True
@docs(
    summary="Legacy items lookup",
    description="This endpoint is deprecated. Use GET /api/v1/items instead.",
    tags=["Items"],
    deprecated=True,
    response=ItemOut,
    response_list=True,
)
@routes.get("/api/v0/items")
async def legacy_list_items(request: web.Request) -> web.Response:
    return web.json_response(list(ITEMS.values()))


# Example 5: include_in_schema=False (internal / hidden route)
@docs(
    include_in_schema=False,
)
@routes.get("/internal/healthcheck")
async def internal_healthcheck(request: web.Request) -> web.Response:
    return web.json_response({"status": "healthy"})


# Example 6: Plain dict schemas (without Pydantic)
@docs(
    summary="Raw ping test",
    tags=["Utility"],
    request_body={
        "type": "object",
        "properties": {"ping": {"type": "string"}},
        "required": ["ping"],
    },
    responses={
        200: {
            "type": "object",
            "properties": {"pong": {"type": "string"}},
        }
    },
)
@routes.post("/api/v1/ping")
async def ping(request: web.Request) -> web.Response:
    data = await request.json()
    return web.json_response({"pong": data.get("ping", "pong")})


def create_app() -> web.Application:
    app = web.Application()
    app.add_routes(routes)

    config = OpenAPIConfig(
        # 1. Basic Info
        title="Comprehensive Store API",
        version="1.0.0",
        description="""
# Store API Documentation

This API powers the inventory catalog. Built with **aiohttp** and documented with **aiohttp-autodocs**.

### Features:
- Zero runtime overhead
- JWT and API Key Authentication
- Full Pydantic v2 Schema support
        """,
        contact={
            "name": "API Support Team",
            "url": "https://example.com/support",
            "email": "support@example.com",
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
        servers=[
            {"url": "http://localhost:8080", "description": "Local Development"},
            {"url": "https://staging.example.com", "description": "Staging Server"},
            {"url": "https://api.example.com", "description": "Production Server"},
        ],
        tags=[
            {"name": "Items", "description": "Endpoints related to catalog items and stock."},
            {"name": "Utility", "description": "General helper and testing utilities."},
        ],
        security_schemes={
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "Enter your JWT Bearer token",
            },
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "API Key passed in header",
            },
        },
        docs_path="/docs",
        spec_path="/openapi.json",
        enabled=True,
        swagger_ui_cdn="https://unpkg.com/swagger-ui-dist@5",
        openapi_version="3.1.0",
    )

    build_openapi(app, config, routes)
    return app


if __name__ == "__main__":
    web.run_app(create_app(), host="127.0.0.1", port=8080)