from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import cast

# Session.metadata is public SDK data, so internal selectors use a reserved namespace.
SESSION_MODEL_PRESET_METADATA_KEY = "_nanobot_model_preset"
SESSION_MODEL_METADATA_KEY = "_nanobot_model"


@dataclass(frozen=True, slots=True)
class SessionModelSelection:
    """One session's explicit model choice, independent of named presets."""

    model: str
    provider: str = "auto"
    context_window_tokens: int | None = None


def model_preset_from_metadata(metadata: object) -> str | None:
    """Read the canonical session preset name from persisted metadata."""
    if not isinstance(metadata, Mapping):
        return None
    typed_metadata = cast(Mapping[object, object], metadata)
    if SESSION_MODEL_PRESET_METADATA_KEY not in typed_metadata:
        return None
    value = typed_metadata[SESSION_MODEL_PRESET_METADATA_KEY]
    if not isinstance(value, str) or not value.strip():
        raise ValueError("session model preset must be a non-empty string")
    return value.strip()


def model_selection_from_metadata(metadata: object) -> SessionModelSelection | None:
    """Read an explicit model selection, ignoring malformed public metadata."""
    if not isinstance(metadata, Mapping):
        return None
    raw = cast(Mapping[object, object], metadata).get(SESSION_MODEL_METADATA_KEY)
    if not isinstance(raw, Mapping):
        return None
    entry = cast(Mapping[object, object], raw)
    model = entry.get("model")
    if not isinstance(model, str) or not model.strip():
        return None
    provider = entry.get("provider")
    if not isinstance(provider, str) or not provider.strip():
        provider = "auto"
    context = entry.get("context_window_tokens")
    if isinstance(context, bool) or not isinstance(context, int) or context <= 0:
        context = None
    return SessionModelSelection(
        model=model.strip(),
        provider=provider.strip(),
        context_window_tokens=context,
    )


def model_selection_metadata(selection: SessionModelSelection) -> dict[str, object]:
    """Serialize a selection for session metadata."""
    payload: dict[str, object] = {"model": selection.model, "provider": selection.provider}
    if selection.context_window_tokens is not None:
        payload["context_window_tokens"] = selection.context_window_tokens
    return payload
