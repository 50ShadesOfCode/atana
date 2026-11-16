from pathlib import Path

from nanobot.webui.agents_api import webui_agents_payload


def _write_agent(base: Path, name: str, *, tools: str = "") -> None:
    (base / "agents").mkdir(parents=True, exist_ok=True)
    limit = f"tools: {tools}\n" if tools else ""
    (base / "agents" / f"{name}.md").write_text(
        f"---\nname: {name}\ndescription: {name} description.\n{limit}---\nBody.\n",
        encoding="utf-8",
    )


def test_payload_lists_roles_and_skipped_files(tmp_path: Path) -> None:
    _write_agent(tmp_path, "reviewer", tools="read_file, rg")
    _write_agent(tmp_path, "researcher")
    (tmp_path / "agents" / "broken.md").write_text("---\nname: [unclosed\n---\nBody.\n", encoding="utf-8")

    payload = webui_agents_payload(tmp_path, available_tools=("read_file", "rg"))

    assert payload["agents"] == [
        {
            "name": "researcher",
            "description": "researcher description.",
            "tools": None,
            "tools_missing": [],
            "path": "agents/researcher.md",
        },
        {
            "name": "reviewer",
            "description": "reviewer description.",
            "tools": ["read_file", "rg"],
            "tools_missing": [],
            "path": "agents/reviewer.md",
        },
    ]
    assert payload["issues"] == [{"name": "broken", "reason": "frontmatter is not valid YAML"}]


def test_payload_marks_unavailable_tools(tmp_path: Path) -> None:
    _write_agent(tmp_path, "reviewer", tools="read_file, grep")

    payload = webui_agents_payload(tmp_path, available_tools=("read_file", "rg"))

    assert payload["agents"][0]["tools_missing"] == ["grep"]


def test_payload_without_agents(tmp_path: Path) -> None:
    assert webui_agents_payload(tmp_path) == {"agents": [], "issues": []}
