from __future__ import annotations

import zipfile
from io import BytesIO

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_UNCOMPRESSED_BYTES = 50 * 1024 * 1024
MAX_ZIP_MEMBERS = 1000


class UnsafeZipError(Exception):
    pass


def ensure_safe_zip(content: bytes) -> None:
    try:
        with zipfile.ZipFile(BytesIO(content)) as archive:
            infos = archive.infolist()
            if len(infos) > MAX_ZIP_MEMBERS:
                raise UnsafeZipError("El archivo contiene demasiados elementos internos")
            if sum(info.file_size for info in infos) > MAX_UNCOMPRESSED_BYTES:
                raise UnsafeZipError("El archivo se expande a un tamaño no permitido")
    except zipfile.BadZipFile as error:
        raise UnsafeZipError("El archivo no es un paquete válido") from error
