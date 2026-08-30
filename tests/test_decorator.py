from __future__ import annotations

from aiohttp_autodocs.decorator import OPENAPI_META_ATTR, docs
from tests.conftest import SampleItem


def test_docs_decorator_default_attributes():
    @docs()
    async def handler(request):
        pass

    meta = getattr(handler, OPENAPI_META_ATTR, None)
    assert meta is not None
    assert meta["summary"] == ""
    assert meta["description"] == ""
    assert meta["tags"] == []
    assert meta["request_body"] is None
    assert meta["response"] is None
    assert meta["response_list"] is False
    assert meta["responses"] == {}
    assert meta["query_params"] == []
    assert meta["path_params"] == []
    assert meta["security"] is None
    assert meta["deprecated"] is False
    assert meta["include_in_schema"] is True
    assert meta["operation_id"] is None


def test_docs_decorator_custom_attributes():
    @docs(
        summary="Get item",
        description="Detailed description",
        tags=["Items"],
        request_body=SampleItem,
        response=SampleItem,
        response_list=True,
        responses={200: SampleItem, 404: None},
        query_params=[("filter", "string", "Filter item", False)],
        path_params=[("item_id", "integer", "ID")],
        security=["BearerAuth"],
        deprecated=True,
        include_in_schema=False,
        operation_id="customGetItem",
    )
    async def handler(request):
        pass

    meta = getattr(handler, OPENAPI_META_ATTR)
    assert meta["summary"] == "Get item"
    assert meta["description"] == "Detailed description"
    assert meta["tags"] == ["Items"]
    assert meta["request_body"] is SampleItem
    assert meta["response"] is SampleItem
    assert meta["response_list"] is True
    assert meta["responses"] == {200: SampleItem, 404: None}
    assert meta["query_params"] == [("filter", "string", "Filter item", False)]
    assert meta["path_params"] == [("item_id", "integer", "ID")]
    assert meta["security"] == ["BearerAuth"]
    assert meta["deprecated"] is True
    assert meta["include_in_schema"] is False
    assert meta["operation_id"] == "customGetItem"
