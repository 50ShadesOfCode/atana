# Custom Subagents

A custom subagent is a markdown file that gives a delegated task its own instructions and, optionally, its own tools. When you keep asking for the same kind of worker — a reviewer, a researcher, a build fixer — write it down once and let the main agent dispatch it by name.

## Write a role

Create `agents/<name>.md` in your agent workspace (`~/.nanobot/workspace/agents/` by default):

```md
---
name: code-reviewer
description: Reviews diffs for bugs, security and missing tests. Use after code changes.
tools: read_file, rg, exec
---
You are a senior reviewer. Read only the diff and the code it touches. Report
findings by severity, each with the file, the problem and the fix. Do not edit
files.
```

- `name` is required and must equal the file name without `.md`: lowercase letters, digits and hyphens, at most 64 characters, no double hyphen.
- `description` is required, up to 1024 characters. This is what the main agent sees when deciding whether to delegate, so say when to use the role.
- `tools` is optional. Omit it, or leave it without a value, to give the role every tool a subagent can use; list names to restrict it; an explicit empty list means the role gets no tools and any task it starts fails.
- Everything after the frontmatter is the role's system prompt. It is added to the standard subagent prompt, not substituted for it, so the workspace, skills summary and untrusted-content rules stay in place.

## Dispatch a role

Ask the agent in words, or call the tool directly:

```
subagent(action="create", agent="code-reviewer", task="review the current diff")
```

The role's name and description appear in the `subagent` tool description, so the main agent knows which roles exist. Each role task is labelled with the role name, which is what the WebUI and TUI show in the task list. Without `agent=` the tool behaves as before: a general-purpose subagent with every subagent tool.

To see the roles, open **Settings → Subagents** in the WebUI or ask for `/agents` in any chat. To start one by hand, send `/agents run <role> <task>`; the task runs in the current conversation and reports back there.

## Tool names

Use nanobot's names inside `tools`:

`read_file`, `write_file`, `edit_file`, `apply_patch`, `list_dir`, `find_files`, `rg`, `exec`, `exec_session`, `list_exec_sessions`, `run_cli_app`, `web_search`, `web_fetch`.

Definitions written for Claude Code are accepted with their tool names mapped: `Read`→`read_file`, `Write`→`write_file`, `Edit`→`edit_file`, `Glob`→`find_files`, `Grep`→`rg`, `Bash`→`exec`, `LS`→`list_dir`, `WebSearch`→`web_search`, `WebFetch`→`web_fetch`. A name that nanobot does not offer is ignored with a warning, and the role runs with the rest of its list, so a copied definition that also names MCP tools still works. The task fails only when nothing in the list is available.

One trap: when `rg` is installed, nanobot drops `grep` and `find_files` in favour of it. Listing `grep` alone then leaves the role with no tools and the task fails. Use `rg` for searching.

## Copy a role from another harness

Files from Claude Code or ECC mostly work as they are: the frontmatter and the body carry over, and the tool names are mapped for you. Copy the file into `agents/`, then adjust what nanobot does not have:

- Remove fields nanobot ignores: `model`, `hooks`, `permissionMode`, `mcpServers`, `skills`, `isolation`, `maxTurns`, `color`.
- Check the body for instructions that assume Claude Code tools or slash commands (`Task`, `TodoWrite`, `/plan`), and rewrite them for nanobot's tools.
- Keep `description` short: every role's description sits in the main agent's tool description on every turn.

## Not supported yet

A role cannot choose its own model, cannot carry its own MCP servers or hooks, and cannot spawn further subagents. Roles are read from the agent workspace only; `.claude/agents/` and per-project role directories are not scanned.

A role file is read when a task starts with that role, so edits to its prompt or tools apply to the next task. The list of roles the main agent is shown lives in the `subagent` tool description, which nanobot rebuilds only when its tool set changes — in practice, after a restart. Calling a new role by name works without a restart. Descriptions longer than 200 characters are shortened in that list; the full text stays in the file.
