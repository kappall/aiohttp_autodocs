from aiohttp import web
from aiohttp_autodocs import OpenAPIConfig, build_openapi, docs

routes = web.RouteTableDef()


@docs(
    summary="Health check",
    description="Returns service health status.",
    tags=["System"],
    responses={
        200: {
            "type": "object",
            "properties": {"status": {"type": "string", "example": "ok"}},
            "required": ["status"],
        }
    },
)
@routes.get("/health")
async def health(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


@docs(
    summary="Echo message",
    tags=["Echo"],
    request_body={
        "type": "object",
        "properties": {"message": {"type": "string"}},
        "required": ["message"],
    },
    responses={
        200: {
            "type": "object",
            "properties": {"echo": {"type": "string"}},
        }
    },
)
@routes.post("/echo")
async def echo(request: web.Request) -> web.Response:
    data = await request.json()
    return web.json_response({"echo": data.get("message")})


def create_app() -> web.Application:
    app = web.Application()
    app.add_routes(routes)

    build_openapi(
        app,
        OpenAPIConfig(
            title="Basic aiohttp-autodocs API",
            version="1.0.0",
            description="Example app using raw dictionary schemas without Pydantic.",
            license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
        ),
        routes,
    )
    return app


if __name__ == "__main__":
    web.run_app(create_app(), port=8080)