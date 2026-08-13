from __future__ import annotations

import httpx

_DOCX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)


class GotenbergPdfConverter:
    def __init__(self, base_url: str, timeout_seconds: float = 60.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    async def convert(self, document: bytes) -> bytes:
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.post(
                f"{self._base_url}/forms/libreoffice/convert",
                files={"file": ("document.docx", document, _DOCX_CONTENT_TYPE)},
            )
            response.raise_for_status()
            return response.content
