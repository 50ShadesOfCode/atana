from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import cast

from loguru import logger

from nanobot.agent.skill_metadata import (
    SKILL_FRONTMATTER,
    SKILL_NAME,
    parse_skill_metadata,
)

AGENTS_DIR = "agents"

# A compact role list keeps the tool description and chat replies small; the full
# text stays in the file.
CATALOG_DESCRIPTION_CHARS = 200

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


def catalog_description(description: str) -> str:
    """Shorten a role description for lists that are budgeted."""
    if len(description) <= CATALOG_DESCRIPTION_CHARS:
        return description
    return description[: CATALOG_DESCRIPTION_CHARS - 1] + "…"


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


def _metadata_reason(metadata: dict[str, object], name: str) -> str | None:
    """Explain why a role's frontmatter is unusable, or return None."""
    if metadata.get("name") != name:
        return "name must match the file name"
    if len(name) > 64 or SKILL_NAME.fullmatch(name) is None:
        return "name must use lowercase letters, digits and dashes"
    description = metadata.get("description")
    if not isinstance(description, str) or not description.strip():
        return "description is required"
    if len(description.strip()) > 1024:
        return "description is at most 1024 characters"
    return None


def _load_agent(path: Path) -> tuple[AgentDefinition | None, str | None]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        logger.warning("Ignoring agent definition '{}': unreadable", path)
        return None, "unreadable"
    metadata = parse_skill_metadata(text)
    if metadata is None:
        logger.warning("Ignoring agent definition '{}': invalid frontmatter", path)
        return None, "frontmatter is not valid YAML"
    reason = _metadata_reason(metadata, path.stem)
    if reason is not None:
        logger.warning("Ignoring agent definition '{}': {}", path, reason)
        return None, reason
    try:
        tools = _parse_tools(metadata.get("tools"))
    except ValueError as exc:
        logger.warning("Ignoring agent definition '{}': invalid tools", path)
        return None, str(exc)
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
            raise ValueError("tools must be a list of tool names or a comma-separated string")
        names = [cast(str, value).strip() for value in values]
    else:
        raise ValueError("tools must be a list of tool names or a comma-separated string")
    resolved: list[str] = []
    for name in names:
        if not name:
            continue
        name = CLAUDE_TOOL_ALIASES.get(name, name)
        if name not in resolved:
            resolved.append(name)
    return tuple(resolved)
