from aiohttp import web
from pydantic import BaseModel, Field
from aiohttp_autodocs import OpenAPIConfig, build_openapi, docs


class UserCreate(BaseModel):
    username: str = Field(..., example="alice")
    email: str = Field(..., example="alice@example.com")
    age: int | None = Field(default=None, ge=0, le=150)


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    age: int | None = None


USERS: dict[int, dict] = {
    1: {"id": 1, "username": "alice", "email": "alice@example.com", "age": 30},
}

routes = web.RouteTableDef()


@docs(
    summary="List all users",
    tags=["Users"],
    query_params=[
        ("limit", "integer", "Max number of users to return", False),
    ],
    response=UserOut,
    response_list=True,
)
@routes.get("/users")
async def list_users(request: web.Request) -> web.Response:
    return web.json_response(list(USERS.values()))


@docs(
    summary="Create user",
    tags=["Users"],
    request_body=UserCreate,
    responses={
        201: UserOut,
        400: None,
    },
    security=["BearerAuth"],
)
@routes.post("/users")
async def create_user(request: web.Request) -> web.Response:
    data = await request.json()
    new_id = len(USERS) + 1
    user = {"id": new_id, **data}
    USERS[new_id] = user
    return web.json_response(user, status=201)


@docs(
    summary="Get user by ID",
    tags=["Users"],
    path_params=[("user_id", "integer", "The unique user ID")],
    responses={
        200: UserOut,
        404: None,
    },
)
@routes.get("/users/{user_id}")
async def get_user(request: web.Request) -> web.Response:
    user_id = int(request.match_info["user_id"])
    user = USERS.get(user_id)
    if not user:
        return web.json_response({"error": "User not found"}, status=404)
    return web.json_response(user)


def create_app() -> web.Application:
    app = web.Application()
    app.add_routes(routes)

    build_openapi(
        app,
        OpenAPIConfig(
            title="Users API with Pydantic",
            version="1.0.0",
            description="Complete CRUD example with Pydantic v2 schemas and JWT Bearer security.",
            security_schemes={
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                }
            },
            tags=[{"name": "Users", "description": "Operations on users"}],
        ),
        routes,
    )
    return app


if __name__ == "__main__":
    web.run_app(create_app(), port=8080)