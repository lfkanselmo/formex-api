from __future__ import annotations

from collections.abc import Awaitable, Callable

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from src.infrastructure.api.upload_guards import MAX_UPLOAD_BYTES


async def max_body_size_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    content_length = request.headers.get("content-length")
    if content_length is not None and int(content_length) > MAX_UPLOAD_BYTES:
        max_mb = MAX_UPLOAD_BYTES // (1024 * 1024)
        return JSONResponse(
            {"detail": f"El archivo supera el tamaño máximo permitido ({max_mb} MB)"},
            status_code=413,
        )
    return await call_next(request)
