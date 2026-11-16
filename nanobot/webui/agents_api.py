from __future__ import annotations

from collections.abc import Collection
from pathlib import Path
from typing import Any

from nanobot.agent.agents import AGENTS_DIR, inspect_agents


def webui_agents_payload(
    workspace_path: Path,
    *,
    available_tools: Collection[str] | None = None,
) -> dict[str, Any]:
    """Return custom subagent roles without leaking absolute paths."""
    agents, issues = inspect_agents(workspace_path)
    entries: list[dict[str, Any]] = []
    for agent in agents.values():
        tools = list(agent.tools) if agent.tools is not None else None
        missing = (
            []
            if tools is None or available_tools is None
            else [name for name in tools if name not in available_tools]
        )
        entries.append(
            {
                "name": agent.name,
                "description": agent.description,
                "tools": tools,
                "tools_missing": missing,
                "path": f"{AGENTS_DIR}/{agent.path.name}",
            }
        )
    return {
        "agents": entries,
        "issues": [{"name": issue.name, "reason": issue.reason} for issue in issues],
    }
