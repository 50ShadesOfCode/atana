from pathlib import Path

from nanobot.agent.agents import discover_agents, inspect_agents


def _write(workspace: Path, name: str, text: str) -> None:
    (workspace / "agents").mkdir(exist_ok=True)
    (workspace / "agents" / f"{name}.md").write_text(text, encoding="utf-8")


def test_discovers_valid_agent(tmp_path):
    _write(
        tmp_path,
        "code-reviewer",
        "---\nname: code-reviewer\ndescription: Reviews diffs.\ntools: read_file, rg\n---\nYou review code.\n",
    )

    agents = discover_agents(tmp_path)

    assert list(agents) == ["code-reviewer"]
    agent = agents["code-reviewer"]
    assert agent.description == "Reviews diffs."
    assert agent.tools == ("read_file", "rg")
    assert agent.prompt == "You review code."


def test_accepts_yaml_list_of_tools(tmp_path):
    _write(
        tmp_path,
        "researcher",
        "---\nname: researcher\ndescription: Researches.\ntools:\n  - web_search\n  - read_file\n---\nResearch.\n",
    )

    assert discover_agents(tmp_path)["researcher"].tools == ("web_search", "read_file")


def test_missing_tools_means_every_tool(tmp_path):
    _write(tmp_path, "helper", "---\nname: helper\ndescription: Helps.\n---\nHelp.\n")

    assert discover_agents(tmp_path)["helper"].tools is None


def test_empty_tools_list_means_no_tools(tmp_path):
    _write(tmp_path, "solo", "---\nname: solo\ndescription: Alone.\ntools: []\n---\nAlone.\n")

    assert discover_agents(tmp_path)["solo"].tools == ()


def test_empty_tools_value_means_every_tool(tmp_path):
    _write(tmp_path, "inherit", "---\nname: inherit\ndescription: Inherits.\ntools:\n---\nInherit.\n")

    assert discover_agents(tmp_path)["inherit"].tools is None


def test_skips_tools_of_the_wrong_type(tmp_path):
    _write(tmp_path, "broken", "---\nname: broken\ndescription: Broken.\ntools: 5\n---\nBroken.\n")

    assert discover_agents(tmp_path) == {}


def test_aliases_claude_tool_names(tmp_path):
    _write(
        tmp_path,
        "portable",
        "---\nname: portable\ndescription: Portable.\ntools: Read, Grep, Bash, Write, Edit, Glob, LS, WebFetch, WebSearch\n---\nWork.\n",
    )

    assert discover_agents(tmp_path)["portable"].tools == (
        "read_file",
        "rg",
        "exec",
        "write_file",
        "edit_file",
        "find_files",
        "list_dir",
        "web_fetch",
        "web_search",
    )


def test_skips_name_that_is_not_the_file_stem(tmp_path):
    _write(tmp_path, "reviewer", "---\nname: other\ndescription: Reviews.\n---\nReview.\n")

    assert discover_agents(tmp_path) == {}


def test_skips_missing_description(tmp_path):
    _write(tmp_path, "reviewer", "---\nname: reviewer\n---\nReview.\n")

    assert discover_agents(tmp_path) == {}


def test_skips_empty_body(tmp_path):
    _write(tmp_path, "reviewer", "---\nname: reviewer\ndescription: Reviews.\n---\n\n")

    assert discover_agents(tmp_path) == {}


def test_skips_broken_yaml_and_keeps_valid_agents(tmp_path):
    _write(tmp_path, "broken", "---\nname: [unclosed\n---\nBody.\n")
    _write(tmp_path, "reviewer", "---\nname: reviewer\ndescription: Reviews.\n---\nReview.\n")

    assert list(discover_agents(tmp_path)) == ["reviewer"]


def test_missing_agents_directory_returns_empty(tmp_path):
    assert discover_agents(tmp_path) == {}


def test_inspect_agents_reports_skipped_files_with_reasons(tmp_path):
    _write(tmp_path, "reviewer", "---\nname: reviewer\ndescription: Reviews.\n---\nReview.\n")
    _write(tmp_path, "broken", "---\nname: [unclosed\n---\nBody.\n")
    _write(tmp_path, "typed", "---\nname: typed\ndescription: Typed.\ntools: 5\n---\nBody.\n")

    agents, issues = inspect_agents(tmp_path)

    assert list(agents) == ["reviewer"]
    assert {(issue.name, issue.reason) for issue in issues} == {
        ("broken", "invalid metadata"),
        ("typed", "invalid tools"),
    }
