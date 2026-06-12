from __future__ import annotations
# Internal handlers for /openapi.json and /docs.
# Registered after spec generation so they never appear in the spec itself.

from aiohttp import web

SPEC_KEY = "_aiohttp_autodocs_spec"
HTML_KEY = "_aiohttp_autodocs_html"


def make_spec_handler(spec_key: str = SPEC_KEY):

    async def openapi_json(request: web.Request) -> web.Response:
        spec_bytes: bytes = request.app[spec_key]
        return web.Response(
            body=spec_bytes,
            content_type="application/json",
            charset="utf-8",
            headers={
                # Allow Swagger UI to call this from any origin during dev
                "Access-Control-Allow-Origin": "*",
                # Encourage browsers to not cache a stale spec
                "Cache-Control": "no-cache",
            },
        )

    return openapi_json


def make_ui_handler(html_key: str = HTML_KEY):

    async def swagger_ui(request: web.Request) -> web.Response:
        html: str = request.app[html_key]
        return web.Response(
            text=html,
            content_type="text/html",
            charset="utf-8",
        )

    return swagger_ui


def make_redirect_handler(target: str):

    async def redirect(_request: web.Request) -> web.Response:
        raise web.HTTPMovedPermanently(target)

    return redirect
