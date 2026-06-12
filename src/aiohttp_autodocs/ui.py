from __future__ import annotations


def render_swagger_ui(
    spec_url: str,
    title: str = "API Documentation",
    cdn_base: str = "https://unpkg.com/swagger-ui-dist@5",
) -> str:
    # Escape any single quotes or braces that might break the inline JS
    safe_spec_url = spec_url.replace("'", "\\'")
    safe_title = title.replace("<", "&lt;").replace(">", "&gt;")

    return f"""\
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{safe_title}</title>
    <link rel="stylesheet" href="{cdn_base}/swagger-ui.css" crossorigin="anonymous" />
    <style>
      *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
      html, body {{ height: 100%; margin: 0; padding: 0; }}
      #swagger-ui .topbar-wrapper .link {{ display: none; /* hide the default Swagger "Explore" link */ }}
    </style>
  </head>
  <body>
    <div id="swagger-ui"></div>

    <script src="{cdn_base}/swagger-ui-bundle.js" crossorigin="anonymous"></script>
    <script src="{cdn_base}/swagger-ui-standalone-preset.js" crossorigin="anonymous"></script>
    <script>
      window.addEventListener("load", function () {{
        window.ui = SwaggerUIBundle({{
          url: "{safe_spec_url}",
          dom_id: "#swagger-ui",
          deepLinking: true,
          tryItOutEnabled: true,
          persistAuthorization: true,
          displayRequestDuration: true,
          filter: true,
          presets: [
            SwaggerUIBundle.presets.apis,
            SwaggerUIStandalonePreset,
          ],
          plugins: [SwaggerUIBundle.plugins.DownloadUrl],
          layout: "StandaloneLayout",
          defaultModelsExpandDepth: 1,
          defaultModelExpandDepth: 2,
          docExpansion: "list",
        }});
      }});
    </script>
  </body>
</html>"""
