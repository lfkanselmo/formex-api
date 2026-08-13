from io import BytesIO

import pytest
from docx import Document
from src.infrastructure.config import settings
from src.infrastructure.pdf.gotenberg_pdf_converter import GotenbergPdfConverter

pytestmark = pytest.mark.integration


def _build_docx_bytes() -> bytes:
    document = Document()
    document.add_paragraph("Contrato de arrendamiento — Maria Gonzalez")
    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


async def test_convert_returns_real_pdf_bytes() -> None:
    converter = GotenbergPdfConverter(settings.gotenberg_url)

    pdf_bytes = await converter.convert(_build_docx_bytes())

    assert pdf_bytes.startswith(b"%PDF-")
