from __future__ import annotations

import json
import time
import uuid
from contextlib import suppress
from pathlib import Path
from typing import Any

from nanobot.utils.helpers import atomic_write_text

# Each run keeps its rendered prompt and response, so the directory needs a cap.
MAX_RUN_RECORDS = 5_000


def safe_run_record_name(run_id: str) -> str:
    """Return a filesystem-safe filename stem for a run ID."""
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in run_id)


def write_run_record(runs_dir: Path, run_id: str, record: dict[str, Any]) -> Path:
    """Write or replace one durable automation run audit record."""
    name = safe_run_record_name(run_id) or str(uuid.uuid4())
    path = runs_dir / f"{name}.json"
    payload = {
        **record,
        "run_id": run_id,
        "updated_at_ms": _now_ms(),
    }
    atomic_write_text(path, json.dumps(payload, indent=2, ensure_ascii=False))
    _prune_run_records(runs_dir)
    return path


def _prune_run_records(runs_dir: Path) -> None:
    """Drop the oldest records once the directory exceeds its cap."""
    try:
        paths = list(runs_dir.glob("*.json"))
        if len(paths) <= MAX_RUN_RECORDS:
            return
        paths.sort(key=lambda item: (item.stat().st_mtime_ns, item.name))
        for stale in paths[: len(paths) - MAX_RUN_RECORDS]:
            with suppress(OSError):
                stale.unlink()
    except OSError:
        return


def _now_ms() -> int:
    return int(time.time() * 1000)
