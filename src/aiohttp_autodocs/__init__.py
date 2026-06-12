from __future__ import annotations

from .config import OpenAPIConfig
from .decorator import docs
from ._builder import build_openapi

__all__ = ["docs", "build_openapi", "OpenAPIConfig"]
__version__ = "0.1.0"
