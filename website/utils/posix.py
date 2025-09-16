import posixpath
from pathlib import PurePosixPath


def posix_join(*parts: str) -> str:
    """S3-ключи всегда POSIX-совместимы (слэши вперед)."""
    return str(PurePosixPath(posixpath.join(*parts)))
