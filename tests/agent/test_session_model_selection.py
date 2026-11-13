from unittest.mock import MagicMock

import pytest

from nanobot.agent.loop import AgentLoop
from nanobot.agent.model_runtime import ModelRuntimeResolver
from nanobot.bus.queue import MessageBus
from nanobot.config.schema import ModelPresetConfig
from nanobot.providers.base import GenerationSettings
from nanobot.providers.factory import ProviderSnapshot
from nanobot.session.model_selection import (
    SESSION_MODEL_METADATA_KEY,
    SESSION_MODEL_PRESET_METADATA_KEY,
    SessionModelSelection,
    model_preset_from_metadata,
    model_selection_from_metadata,
)
from nanobot.utils.llm_runtime import LLMRuntime


def _provider(model: str) -> MagicMock:
    provider = MagicMock()
    provider.get_default_model.return_value = model
    provider.generation = GenerationSettings(temperature=0.1, max_tokens=123)
    return provider


def _snapshot(preset: ModelPresetConfig) -> ProviderSnapshot:
    return ProviderSnapshot(
        provider=_provider(preset.model),
        model=preset.model,
        context_window_tokens=preset.context_window_tokens,
        signature=("selected", preset.model, preset.provider),
        generation=preset.to_generation_settings(),
    )


def _resolver(loader):
    base = LLMRuntime.capture(
        _provider("base-model"),
        "base-model",
        context_window_tokens=8_000,
        snapshot_signature=("base",),
    )
    return ModelRuntimeResolver(base, preset_snapshot_loader=loader)


def test_resolve_model_builds_a_provider_snapshot_and_inherits_generation() -> None:
    seen: list[ModelPresetConfig] = []

    def loader(target):
        seen.append(target)
        return _snapshot(target)

    resolver = _resolver(loader)
    runtime = resolver.resolve_model(
        SessionModelSelection(model="openai/gpt-4.1", provider="openai", context_window_tokens=32_768),
    )

    assert runtime.model == "openai/gpt-4.1"
    assert runtime.model_preset is None
    assert runtime.context_window_tokens == 32_768
    assert runtime.generation == GenerationSettings(0.1, 123, None)
    assert seen[0].provider == "openai"
    assert resolver.model_preset is None


def test_resolve_model_inherits_the_base_context_window() -> None:
    resolver = _resolver(_snapshot)

    runtime = resolver.resolve_model(SessionModelSelection(model="gpt-4.1"))

    assert runtime.context_window_tokens == 8_000


def test_resolve_model_caches_until_invalidated() -> None:
    calls: list[ModelPresetConfig] = []

    def loader(target):
        calls.append(target)
        return _snapshot(target)

    resolver = _resolver(loader)
    selection = SessionModelSelection(model="gpt-4.1")

    first = resolver.resolve_model(selection)
    second = resolver.resolve_model(selection)
    resolver.invalidate()
    third = resolver.resolve_model(selection)

    assert first is second
    assert third is not first
    assert len(calls) == 2


def test_resolve_model_requires_a_loader() -> None:
    resolver = _resolver(None)

    with pytest.raises(ValueError):
        resolver.resolve_model(SessionModelSelection(model="gpt-4.1"))


def _loop(tmp_path, *, loader=None, presets=None) -> AgentLoop:
    configured = presets or {"fast": ModelPresetConfig(model="fast-model")}

    def resolve(target):
        if isinstance(target, str):
            return ProviderSnapshot(
                provider=_provider(configured[target].model),
                model=configured[target].model,
                context_window_tokens=configured[target].context_window_tokens,
                signature=("preset", target),
                generation=configured[target].to_generation_settings(),
                model_preset=target,
            )
        return _snapshot(target)

    return AgentLoop(
        bus=MessageBus(),
        provider=_provider("base-model"),
        workspace=tmp_path,
        model="base-model",
        context_window_tokens=1000,
        model_presets=configured,
        preset_snapshot_loader=loader or resolve,
    )


@pytest.mark.asyncio
async def test_set_session_model_persists_and_clears_the_preset(tmp_path) -> None:
    loop = _loop(tmp_path)
    await loop.set_session_model_preset("cli:direct", "fast")

    runtime = await loop.set_session_model(
        "cli:direct",
        "openai/gpt-4.1",
        provider="openai",
        context_window_tokens=32_768,
    )

    session = loop.sessions.get_or_create("cli:direct")
    selection = model_selection_from_metadata(session.metadata)
    assert runtime.model == "openai/gpt-4.1"
    assert selection == SessionModelSelection(
        model="openai/gpt-4.1",
        provider="openai",
        context_window_tokens=32_768,
    )
    assert model_preset_from_metadata(session.metadata) is None
    assert (await loop.runtime_for_session(session)).model == "openai/gpt-4.1"


@pytest.mark.asyncio
async def test_set_session_model_preset_clears_the_model_selection(tmp_path) -> None:
    loop = _loop(tmp_path)
    await loop.set_session_model("cli:direct", "openai/gpt-4.1")

    await loop.set_session_model_preset("cli:direct", "fast")

    session = loop.sessions.get_or_create("cli:direct")
    assert model_selection_from_metadata(session.metadata) is None
    assert model_preset_from_metadata(session.metadata) == "fast"
    assert (await loop.runtime_for_session(session)).model == "fast-model"


@pytest.mark.asyncio
async def test_session_preset_wins_when_both_keys_are_present(tmp_path) -> None:
    loop = _loop(tmp_path)
    session = loop.sessions.get_or_create("cli:direct")
    session.metadata[SESSION_MODEL_PRESET_METADATA_KEY] = "fast"
    session.metadata[SESSION_MODEL_METADATA_KEY] = {"model": "openai/gpt-4.1"}
    loop.sessions.save(session)

    runtime = await loop.runtime_for_session(loop.sessions.get_or_create("cli:direct"))

    assert runtime.model == "fast-model"


@pytest.mark.asyncio
async def test_unusable_session_model_falls_back_to_the_default(tmp_path) -> None:
    def loader(target):
        raise ValueError("No API key configured for provider 'openai'.")

    loop = _loop(tmp_path, loader=loader)
    session = loop.sessions.get_or_create("cli:direct")
    session.metadata[SESSION_MODEL_METADATA_KEY] = {"model": "openai/gpt-4.1", "provider": "openai"}
    loop.sessions.save(session)

    runtime = await loop.runtime_for_session(loop.sessions.get_or_create("cli:direct"))

    assert runtime.model == "base-model"
    assert model_selection_from_metadata(
        loop.sessions.get_or_create("cli:direct").metadata,
    ) is None


@pytest.mark.asyncio
async def test_set_session_model_rejects_an_empty_model(tmp_path) -> None:
    loop = _loop(tmp_path)

    with pytest.raises(ValueError):
        await loop.set_session_model("cli:direct", "   ")


def test_session_selection_does_not_change_the_loop_default(tmp_path) -> None:
    loop = _loop(tmp_path)
    resolver = loop.runtime_resolver

    resolver.resolve_model(SessionModelSelection(model="openai/gpt-4.1", provider="openai"))

    assert resolver.runtime.model == "base-model"
    assert resolver.runtime.model_preset is None
