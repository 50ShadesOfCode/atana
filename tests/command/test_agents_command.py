from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from nanobot.agent.loop import AgentLoop
from nanobot.bus.events import InboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.command.application import builtin_command_palette, register_builtin_commands
from nanobot.command.builtin import build_help_text, cmd_agents
from nanobot.command.router import CommandContext, CommandRouter
from nanobot.config.schema import ModelPresetConfig


def _provider(default_model: str = "test-model") -> MagicMock:
    provider = MagicMock()
    provider.get_default_model.return_value = default_model
    provider.generation = MagicMock()
    provider.generation.max_tokens = 4096
    provider.generation.temperature = 0.1
    provider.generation.reasoning_effort = None
    return provider


def _loop(tmp_path: Path) -> AgentLoop:
    return AgentLoop(
        bus=MessageBus(),
        provider=_provider(),
        workspace=tmp_path,
        model="test-model",
        context_window_tokens=8000,
        model_presets={
            "default": ModelPresetConfig(
                model="test-model",
                max_tokens=4096,
                context_window_tokens=8000,
            ),
        },
    )


def _ctx(loop: AgentLoop, raw: str = "/agents", *, args: str = "") -> CommandContext:
    msg = InboundMessage(channel="cli", sender_id="user", chat_id="direct", content=raw)
    return CommandContext(
        msg=msg, session=None, key=msg.session_key, raw=raw, args=args, loop=loop,
        runtime=MagicMock(),
    )


def _write_agent(base: Path, name: str, *, description: str = "Does work.", tools: str = "") -> None:
    (base / "agents").mkdir(parents=True, exist_ok=True)
    limit = f"tools: {tools}\n" if tools else ""
    (base / "agents" / f"{name}.md").write_text(
        f"---\nname: {name}\ndescription: {description}\n{limit}---\nYou work.\n",
        encoding="utf-8",
    )


@pytest.mark.asyncio
async def test_agents_command_without_roles(tmp_path: Path) -> None:
    out = await cmd_agents(_ctx(_loop(tmp_path)))

    assert "No custom agents" in out.content


@pytest.mark.asyncio
async def test_agents_command_lists_roles_and_skipped_files(tmp_path: Path) -> None:
    _write_agent(tmp_path, "reviewer", description="Reviews diffs.", tools="read_file, rg")
    _write_agent(tmp_path, "researcher", description="Researches.")
    (tmp_path / "agents" / "broken.md").write_text("---\nname: [unclosed\n---\nBody.\n", encoding="utf-8")

    out = await cmd_agents(_ctx(_loop(tmp_path)))

    assert "Custom agents (2):" in out.content
    assert "**reviewer** — Reviews diffs. (tools: read_file, rg)" in out.content
    assert "**researcher** — Researches. (tools: all subagent tools)" in out.content
    assert "Skipped files:" in out.content
    assert "**broken** — invalid metadata" in out.content


@pytest.mark.asyncio
async def test_agents_command_rejects_unknown_role(tmp_path: Path) -> None:
    _write_agent(tmp_path, "reviewer")

    out = await cmd_agents(_ctx(_loop(tmp_path), args="run missing review this"))

    assert "Unknown agent 'missing'" in out.content
    assert "reviewer" in out.content


@pytest.mark.asyncio
async def test_agents_command_requires_a_task(tmp_path: Path) -> None:
    _write_agent(tmp_path, "reviewer")

    out = await cmd_agents(_ctx(_loop(tmp_path), args="run reviewer"))

    assert "Usage: /agents run <role> <task>" in out.content


@pytest.mark.asyncio
async def test_agents_command_starts_the_role_in_this_session(tmp_path: Path) -> None:
    _write_agent(tmp_path, "reviewer", tools="read_file")
    loop = _loop(tmp_path)
    loop.subagents.spawn = AsyncMock(return_value="Subagent [reviewer: review this] started (id: t1).")

    out = await cmd_agents(_ctx(loop, args="run reviewer review this"))

    assert "started (id: t1)" in out.content
    loop.subagents.spawn.assert_awaited_once()
    kwargs = loop.subagents.spawn.await_args.kwargs
    assert kwargs["task"] == "review this"
    assert kwargs["agent"].name == "reviewer"
    assert kwargs["agent"].tools == ("read_file",)
    assert kwargs["session_key"] == "cli:direct"


@pytest.mark.asyncio
async def test_agents_command_registered_on_router(tmp_path: Path) -> None:
    router = CommandRouter()
    register_builtin_commands(router)
    _write_agent(tmp_path, "reviewer")

    out = await router.dispatch(_ctx(_loop(tmp_path)))

    assert out is not None
    assert "**reviewer**" in out.content


def test_agents_command_in_help_and_palette() -> None:
    palette = builtin_command_palette()
    entry = next(item for item in palette if item["command"] == "/agents")

    assert entry["arg_hint"] == "[run <role> <task>]"
    assert entry["lifecycle"] == "side_channel"
    assert entry["accepts_args"] is True
    assert "/agents [run <role> <task>]" in build_help_text()
