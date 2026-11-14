from __future__ import annotations

from collections.abc import Mapping, Sequence


def query_first(query: Mapping[str, Sequence[str]], key: str) -> str | None:
    """Return the first value of one query parameter, if present."""
    values = query.get(key)
    return values[0] if values else None
