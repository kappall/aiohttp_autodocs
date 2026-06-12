from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class OpenAPIConfig:
    """
    Configuration for the OpenAPI documentation module.

    Example::

        OpenAPIConfig(
            title="My API",
            version="1.0.0",
            description="desc.",
            servers=[{"url": "http://localhost:8080", "description": "Dev"}],
            enabled=True,
            security_schemes={
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                }
            },
            tags=[
                {"name": "Alarms", "description": "Alarm management"},
            ],
        )
    """

    title: str
    version: str
    description: str = ""
    """Markdown description displayed below the title in Swagger UI."""

    contact: dict | None = None
    """Contact object, e.g. ``{"name": "Support", "email": "api@example.com"}``."""

    license_info: dict | None = None
    servers: list[dict] = field(default_factory=list)
    tags: list[dict] = field(default_factory=list)
    security_schemes: dict = field(default_factory=dict)
    docs_path: str = "/docs"
    spec_path: str = "/openapi.json"
    enabled: bool = True
    swagger_ui_cdn: str = "https://unpkg.com/swagger-ui-dist@5"
    openapi_version: str = "3.1.0"

    def __post_init__(self) -> None:
        if not self.title:
            raise ValueError("OpenAPIConfig.title must not be empty.")
        if not self.version:
            raise ValueError("OpenAPIConfig.version must not be empty.")
        if not self.docs_path.startswith("/"):
            raise ValueError("OpenAPIConfig.docs_path must start with '/'.")
        if not self.spec_path.startswith("/"):
            raise ValueError("OpenAPIConfig.spec_path must start with '/'.")
        if self.docs_path == self.spec_path:
            raise ValueError(
                "OpenAPIConfig.docs_path and spec_path must be different paths."
            )
