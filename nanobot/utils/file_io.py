import os
import stat
import uuid
from contextlib import suppress
from pathlib import Path

from nanobot.utils.atomic_file import io_path, replace_atomic


def ensure_dir(path: Path) -> Path:
    """Ensure directory exists, return it."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_bytes_atomic(path: Path, content: bytes) -> None:
    """Replace *path* with *content* without ever exposing a partial file."""
    path = io_path(path)
    tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    existing_mode: int | None = None
    with suppress(OSError):
        existing_mode = stat.S_IMODE(path.stat().st_mode)
    try:
        with open(tmp, "wb") as f:
            if existing_mode is not None:
                os.chmod(tmp, existing_mode)
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        replace_atomic(tmp, path)
        with suppress(OSError, NotImplementedError):
            dfd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(dfd)
            finally:
                os.close(dfd)
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)


def write_text_atomic(path: Path, content: str) -> None:
    write_bytes_atomic(path, content.encode("utf-8"))
