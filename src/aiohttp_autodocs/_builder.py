from __future__ import annotations

import logging

from aiohttp import web

from ._routes import (
    HTML_KEY,
    SPEC_KEY,
    make_redirect_handler,
    make_spec_handler,
    make_ui_handler,
)
from .config import OpenAPIConfig
from .scanner import build_spec
from .ui import render_swagger_ui

logger = logging.getLogger(__name__)

_INITIALIZED_KEY: web.AppKey[bool] = web.AppKey("aiohttp_autodocs_initialized", bool)


def build_openapi(
    app: web.Application,
    config: OpenAPIConfig,
    *route_tables: web.RouteTableDef,
) -> None:
    """
    Build the OpenAPI spec from *route_tables* and register /openapi.json
    and /docs on *app*. Call once in create_app(), after all routes are added.

    When ``config.enabled`` is False this is a no-op — no routes are registered.
    Raises RuntimeError if called more than once on the same app.
    """
    if app.get(_INITIALIZED_KEY):
        raise RuntimeError(
            "build_openapi() has already been called on this application. "
            "It must be called exactly once, after all routes are registered."
        )

    if not config.enabled:
        logger.info(
            "aiohttp-autodocs: documentation is disabled "
            "(OpenAPIConfig.enabled=False). Skipping."
        )
        app[_INITIALIZED_KEY] = True
        return

    spec_bytes = build_spec(config, list(route_tables))
    app[SPEC_KEY] = spec_bytes
    app[_INITIALIZED_KEY] = True

    html = render_swagger_ui(
        spec_url=config.spec_path,
        title=config.title,
        cdn_base=config.swagger_ui_cdn,
    )
    app[HTML_KEY] = html

    app.router.add_get(config.spec_path, make_spec_handler())
    app.router.add_get(config.docs_path, make_ui_handler())

    # Redirect /docs/ to /docs to avoid duplicate content.
    if not config.docs_path.endswith("/"):
        app.router.add_get(
            config.docs_path + "/",
            make_redirect_handler(config.docs_path),
        )

    logger.info(
        "aiohttp-autodocs: docs available at %s  |  spec at %s",
        config.docs_path,
        config.spec_path,
    )
