from unittest.mock import MagicMock

import pytest

from nanobot.agent.memory import Consolidator
from nanobot.agent.subagent import SubagentManager
from nanobot.agent.tools.subagent import SubagentTool
from nanobot.bus.queue import MessageBus


def _manager(tmp_path, *, agent: str | None = "reviewer") -> SubagentManager:
    if agent is not None:
        (tmp_path / "agents").mkdir()
        (tmp_path / "agents" / f"{agent}.md").write_text(
            f"---\nname: {agent}\ndescription: Reviews code.\n---\nYou review.\n",
            encoding="utf-8",
        )
    return SubagentManager(
        consolidator=MagicMock(spec=Consolidator),
        workspace=tmp_path,
        bus=MessageBus(),
        max_tool_result_chars=16_000,
    )


@pytest.mark.asyncio
async def test_unknown_agent_is_rejected_with_available_names(tmp_path):
    tool = SubagentTool(_manager(tmp_path))

    result = await tool.execute(action="create", task="review this", agent="Reviewer")

    assert result.is_error
    assert "Reviewer" in result
    assert "reviewer" in result


def test_description_lists_custom_agents(tmp_path):
    description = SubagentTool(_manager(tmp_path)).description

    assert "Custom agents (pass agent= to create):" in description
    assert "- reviewer — Reviews code." in description


def test_description_has_no_catalog_without_agents(tmp_path):
    assert "Custom agents" not in SubagentTool(_manager(tmp_path, agent=None)).description
