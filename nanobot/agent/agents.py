from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import cast

from loguru import logger

from nanobot.agent.skill_metadata import (
    SKILL_FRONTMATTER,
    parse_skill_metadata,
    valid_skill_metadata,
)

AGENTS_DIR = "agents"

# Claude Code agents name tools the way Claude Code does; map them onto ours so a
# copied definition keeps working.
CLAUDE_TOOL_ALIASES: dict[str, str] = {
    "Bash": "exec",
    "Edit": "edit_file",
    "Glob": "find_files",
    "Grep": "rg",
    "LS": "list_dir",
    "Read": "read_file",
    "WebFetch": "web_fetch",
    "WebSearch": "web_search",
    "Write": "write_file",
}


@dataclass(frozen=True, slots=True)
class AgentDefinition:
    """One custom subagent role loaded from ``<workspace>/agents/<name>.md``."""

    name: str
    description: str
    tools: tuple[str, ...] | None
    prompt: str
    path: Path


@dataclass(frozen=True, slots=True)
class AgentIssue:
    """A role file that could not be loaded, and the reason."""

    name: str
    reason: str


def discover_agents(workspace: Path) -> dict[str, AgentDefinition]:
    """Load the roles defined in ``<workspace>/agents``; invalid files are skipped."""
    return inspect_agents(workspace)[0]


def inspect_agents(workspace: Path) -> tuple[dict[str, AgentDefinition], list[AgentIssue]]:
    """Load the roles and report the files that had to be skipped."""
    root = workspace.expanduser() / AGENTS_DIR
    if not root.is_dir():
        return {}, []
    agents: dict[str, AgentDefinition] = {}
    issues: list[AgentIssue] = []
    for path in sorted(root.glob("*.md")):
        agent, reason = _load_agent(path)
        if agent is not None:
            agents[agent.name] = agent
        elif reason is not None:
            issues.append(AgentIssue(name=path.stem, reason=reason))
    return agents, issues


def _load_agent(path: Path) -> tuple[AgentDefinition | None, str | None]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        logger.warning("Ignoring agent definition '{}': unreadable", path)
        return None, "unreadable"
    metadata = parse_skill_metadata(text)
    if metadata is None or not valid_skill_metadata(metadata, path.stem):
        logger.warning("Ignoring agent definition '{}': invalid metadata", path)
        return None, "invalid metadata"
    try:
        tools = _parse_tools(metadata.get("tools"))
    except ValueError:
        logger.warning("Ignoring agent definition '{}': invalid tools", path)
        return None, "invalid tools"
    match = SKILL_FRONTMATTER.match(text)
    prompt = text[match.end():].strip() if match else text.strip()
    if not prompt:
        logger.warning("Ignoring agent definition '{}': empty prompt", path)
        return None, "empty prompt"
    return (
        AgentDefinition(
            name=path.stem,
            description=cast(str, metadata["description"]).strip(),
            tools=tools,
            prompt=prompt,
            path=path,
        ),
        None,
    )


def _parse_tools(raw: object) -> tuple[str, ...] | None:
    """Return the role's tool allowlist; ``None`` means every tool."""
    if raw is None:
        return None
    if isinstance(raw, str):
        names = [part.strip() for part in raw.split(",")]
    elif isinstance(raw, list):
        values = cast(list[object], raw)
        if not all(isinstance(value, str) for value in values):
            raise ValueError("tools must contain only names")
        names = [cast(str, value).strip() for value in values]
    else:
        raise ValueError("tools must be a string or a list")
    resolved: list[str] = []
    for name in names:
        if not name:
            continue
        name = CLAUDE_TOOL_ALIASES.get(name, name)
        if name not in resolved:
            resolved.append(name)
    return tuple(resolved)
