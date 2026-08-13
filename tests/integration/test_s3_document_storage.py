from uuid import uuid4

import pytest
from botocore.exceptions import ClientError
from src.infrastructure.config import settings
from src.infrastructure.storage.s3_document_storage import S3DocumentStorage

pytestmark = pytest.mark.integration


def _build_storage() -> S3DocumentStorage:
    return S3DocumentStorage(
        endpoint_url=settings.s3_endpoint_url,
        access_key=settings.s3_access_key,
        secret_key=settings.s3_secret_key,
        bucket=settings.s3_bucket,
    )


async def test_save_and_load_roundtrip() -> None:
    storage = _build_storage()
    key = f"tests/{uuid4()}.pdf"

    await storage.save(key, b"contenido-de-prueba")
    loaded = await storage.load(key)

    assert loaded == b"contenido-de-prueba"


async def test_load_missing_key_raises() -> None:
    storage = _build_storage()

    with pytest.raises(ClientError):
        await storage.load(f"tests/no-existe-{uuid4()}.pdf")
