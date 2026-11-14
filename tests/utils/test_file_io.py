from __future__ import annotations

from pathlib import Path

import pytest

from nanobot.utils.file_io import write_bytes_atomic


def test_write_bytes_atomic_replaces_the_file(tmp_path: Path) -> None:
    path = tmp_path / "file.bin"
    path.write_bytes(b"old")

    write_bytes_atomic(path, b"new")

    assert path.read_bytes() == b"new"


def test_write_bytes_atomic_keeps_the_original_when_replace_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "file.bin"
    path.write_bytes(b"old")

    def boom(self: Path, target: Path) -> Path:  # noqa: ARG001
        raise OSError("simulated crash before replace")

    monkeypatch.setattr(Path, "replace", boom)
    with pytest.raises(OSError, match="simulated crash"):
        write_bytes_atomic(path, b"new")

    assert path.read_bytes() == b"old"
    assert [item.name for item in tmp_path.iterdir()] == ["file.bin"]
