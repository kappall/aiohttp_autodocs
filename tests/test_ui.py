from __future__ import annotations

from aiohttp_autodocs.ui import render_swagger_ui


def test_render_swagger_ui_basic():
    html = render_swagger_ui(
        spec_url="/openapi.json",
        title="Custom Doc Title",
        cdn_base="https://unpkg.com/swagger-ui-dist@5",
    )
    assert "<title>Custom Doc Title</title>" in html
    assert 'url: "/openapi.json"' in html
    assert "https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" in html
    assert "SwaggerUIBundle" in html


def test_render_swagger_ui_escapes_special_chars():
    html = render_swagger_ui(
        spec_url="/openapi'quote.json",
        title="API <script>alert(1)</script>",
    )
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "<script>alert(1)</script>" not in html
    assert r"/openapi\'quote.json" in html
