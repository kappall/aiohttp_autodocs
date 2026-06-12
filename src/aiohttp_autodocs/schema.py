from __future__ import annotations

import copy
from typing import Any


try:
    from pydantic import BaseModel as _PydanticBase
    _PYDANTIC_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PydanticBase = None  # type: ignore[assignment,misc]
    _PYDANTIC_AVAILABLE = False


# Public helpers

def is_pydantic_model(obj: Any) -> bool:
    if not _PYDANTIC_AVAILABLE or _PydanticBase is None:
        return False
    try:
        return isinstance(obj, type) and issubclass(obj, _PydanticBase)
    except TypeError:
        return False


def extract_schema(
    model: type | dict | None,
    components: dict[str, Any],
) -> dict[str, Any] | None:
    """
    Convert *model* to an OpenAPI schema dict.

    Nested / referenced component schemas are registered in *components*
    (the ``components/schemas`` section of the spec) as a side effect.

    Parameters
    ----------
    model:
        - ``None`` -> returns ``None`` (no body / no schema).
        - ``dict`` -> treated as a raw JSON Schema object, returned as-is.
        - Pydantic ``BaseModel`` subclass -> ``model_json_schema()`` is called
          and the result is normalised for OpenAPI.

    components:
        A mutable dict that accumulates component schemas during spec building.
        Pass the same object for every call within one spec-building session.

    Raises
    ------
    TypeError
        If *model* is not ``None``, a ``dict``, or a Pydantic model class.
    ImportError
        If *model* is a Pydantic model class but Pydantic is not installed.
    """
    if model is None:
        return None

    if isinstance(model, dict):
        # use as-is (deep-copy to prevent accidental mutation)
        return copy.deepcopy(model)

    if is_pydantic_model(model):
        return _pydantic_to_schema(model, components)

    if not _PYDANTIC_AVAILABLE and isinstance(model, type):
        raise ImportError(
            f"Cannot extract schema from {model!r}: Pydantic is not installed. "
            "Install it with: pip install aiohttp-autodocs[pydantic]"
        )

    raise TypeError(
        f"Cannot extract schema from {model!r}. "
        "Expected a Pydantic BaseModel subclass (or SQLModel) or a plain dict."
    )


def _pydantic_to_schema(model: type, components: dict[str, Any]) -> dict[str, Any]:
    """
    Generate an OpenAPI-compatible ``$ref`` for a Pydantic model, registering
    the model (and all nested models from ``$defs``) in *components*.
    """
    raw: dict[str, Any] = model.model_json_schema()  # type: ignore[attr-defined]
    defs: dict[str, Any] = raw.pop("$defs", {})

    for def_name, def_schema in defs.items():
        if def_name not in components:
            components[def_name] = _fix_refs(def_schema)

    name = model.__name__
    if name not in components:
        components[name] = _fix_refs(raw)

    return {"$ref": f"#/components/schemas/{name}"}


def _fix_refs(schema: Any) -> Any:
    """
    Recursively rewrite Pydantic's internal ``#/$defs/Foo`` references to
    the OpenAPI-standard ``#/components/schemas/Foo`` form.
    """
    if isinstance(schema, dict):
        return {
            k: (
                f"#/components/schemas/{v[len('#/$defs/'):]}"
                if k == "$ref" and isinstance(v, str) and v.startswith("#/$defs/")
                else _fix_refs(v)
            )
            for k, v in schema.items()
        }
    if isinstance(schema, list):
        return [_fix_refs(item) for item in schema]
    return schema
