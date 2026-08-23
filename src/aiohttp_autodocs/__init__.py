from __future__ import annotations
import importlib

from .config import OpenAPIConfig
from .decorator import docs
from ._builder import build_openapi

__all__ = ["docs", "build_openapi", "OpenAPIConfig"]
__version__ = importlib.metadata.version("aiohttp-autodocs")
