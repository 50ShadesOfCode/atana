from __future__ import annotations

from pathlib import Path
from typing import Any

from nanobot.agent.agents import AGENTS_DIR, inspect_agents


def webui_agents_payload(workspace_path: Path) -> dict[str, Any]:
    """Return custom subagent roles without leaking absolute paths."""
    agents, issues = inspect_agents(workspace_path)
    return {
        "agents": [
            {
                "name": agent.name,
                "description": agent.description,
                "tools": list(agent.tools) if agent.tools is not None else None,
                "path": f"{AGENTS_DIR}/{agent.path.name}",
            }
            for agent in agents.values()
        ],
        "issues": [{"name": issue.name, "reason": issue.reason} for issue in issues],
    }
