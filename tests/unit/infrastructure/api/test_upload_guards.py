import zipfile
from io import BytesIO

import pytest
from src.infrastructure.api.upload_guards import MAX_ZIP_MEMBERS, UnsafeZipError, ensure_safe_zip


def _zip_bytes(member_count: int) -> bytes:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for index in range(member_count):
            archive.writestr(f"f{index}.txt", "x")
    return buffer.getvalue()


def test_ensure_safe_zip_accepts_a_well_formed_archive() -> None:
    ensure_safe_zip(_zip_bytes(3))


def test_ensure_safe_zip_rejects_content_that_is_not_a_zip() -> None:
    with pytest.raises(UnsafeZipError):
        ensure_safe_zip(b"esto no es un archivo zip")


def test_ensure_safe_zip_rejects_too_many_members() -> None:
    with pytest.raises(UnsafeZipError):
        ensure_safe_zip(_zip_bytes(MAX_ZIP_MEMBERS + 1))
