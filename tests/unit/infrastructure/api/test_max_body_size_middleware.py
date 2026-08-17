from src.infrastructure.api.max_body_size_middleware import max_body_size_middleware
from src.infrastructure.api.upload_guards import MAX_UPLOAD_BYTES
from starlette.requests import Request
from starlette.responses import Response


def _request(content_length: int | None) -> Request:
    headers = [] if content_length is None else [(b"content-length", str(content_length).encode())]
    scope = {"type": "http", "method": "POST", "path": "/api/v1/templates", "headers": headers}
    return Request(scope)


async def test_rejects_a_request_declaring_a_body_larger_than_the_limit() -> None:
    async def call_next(request: Request) -> Response:
        raise AssertionError("call_next should not run for an oversized body")

    response = await max_body_size_middleware(_request(MAX_UPLOAD_BYTES + 1), call_next)

    assert response.status_code == 413


async def test_passes_through_a_request_within_the_limit() -> None:
    async def call_next(request: Request) -> Response:
        return Response(status_code=200)

    response = await max_body_size_middleware(_request(MAX_UPLOAD_BYTES), call_next)

    assert response.status_code == 200


async def test_passes_through_a_request_without_a_content_length_header() -> None:
    async def call_next(request: Request) -> Response:
        return Response(status_code=200)

    response = await max_body_size_middleware(_request(None), call_next)

    assert response.status_code == 200
