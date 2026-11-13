# Working on nanobot

The Python gateway owns agent execution, sessions, tools, memory, and security policy. WebUI and TUI share that runtime; keep execution and policy out of the clients.

WebUI/gateway support and test coverage are limited to same-version combinations, including remote gateways. Cross-version combinations may work but have no compatibility guarantee, even when protocol checks pass; align versions first when troubleshooting. Do not reject connections solely because package versions differ, or add compatibility fallbacks or negotiation solely to support older gateways.

## Task-specific guidance

| When working on | Read |
| --- | --- |
| Finding the owning code and focused tests | [`.agent/navigation.md`](.agent/navigation.md) |
| Core boundaries, extensions, or internal types | [`.agent/design.md`](.agent/design.md) |
| Refactoring, fallbacks, or test selection | [`.agent/simplify.md`](.agent/simplify.md) |
| User-facing copy, feature naming, or localization | [`.agent/copywriting.md`](.agent/copywriting.md) |
| Path permissions, HTTP/MCP, or shell isolation | [`.agent/security.md`](.agent/security.md) |
| Dependency setup, WebUI transport, config, Windows, prompts, or persistence | [`.agent/gotchas.md`](.agent/gotchas.md) |
| Reusing verification evidence | [`.agent/workflow.md`](.agent/workflow.md) |
| WebUI/host compatibility | [`.agent/review-guide.md`](.agent/review-guide.md) |
| Contribution or publication | [`CONTRIBUTING.md`](CONTRIBUTING.md), [`docs/releasing.md`](docs/releasing.md) |

## Development constraints

- Analyze the required behavior, state ownership, and root cause before extending existing code. Refactor when the structure causes the problem; a smaller diff does not justify another fallback.
- Do not add defensive tests for hypothetical internal states or unsupported combinations. Each new test needs a reachable path and a meaningful contract to protect.
- Do not add tests merely to prove that nonexistent behavior, removed code, or obsolete symbols are absent. Negative assertions must exercise a concrete, reachable risk and protect an observable behavioral contract; prefer testing supported actions and their results.
- Do not run `ruff format`; mechanical formatting obscures git blame and creates unrelated diffs. This constraint takes precedence over the optional touched-file formatting in `CONTRIBUTING.md`.
- Do not manually wrap prose in Markdown files. Keep each paragraph on one source line; use line breaks only for Markdown structure.

<!-- trail:start -->
## Trail — repo context graph

This repo is indexed in `.trail/cache/`: small linked markdown nodes that explain each
system and carry exact file:line spans, kept in sync with the code through git.

For ANY task here — understanding how something works, finding where code lives,
or scoping a change — get context from the graph before grepping or opening
source files. Re-ask freely (it's cheap) and reuse literal identifiers you
already have (symbol, error string, file name) as the query. New to this repo?
Run `trail map` first — a token-budgeted orientation (dir clusters, hubs,
hotspots), no LLM, no key.

- Run `trail ask "<your question>" --source` → ranked nodes with the relevant
  code spans inlined (each hit's ≤8-line crux by default; `--full` for whole
  definitions when the crux isn't enough). Match the tool to the task shape:
  for understanding or editing, the top node IS the answer — cite its
  `covers:` file:line spans and edit straight from `--source`. For
  exhaustive tasks ("every occurrence / every caller of this pattern"), ranked
  results are top-N, not complete — run `trail grep "<literal>"` instead
  (exhaustive over indexed files, grouped by enclosing symbol), falling back
  to raw `grep -rn` only for unindexed files.
- `trail skeleton <file>` → every definition's signature + span, ~10× cheaper
  than reading the file; use it to skim an API surface.
- `trail callers <symbol>` gives precomputed, exact edges — who calls this.
  Add `--direction out` for what it calls, or `--depth N` to walk
  transitively for the full blast radius. For structural questions, skip
  ranking and use this directly.
- Or browse: `.trail/cache/INDEX.md` lists every node; follow the links.
- Monorepos and folders of multiple repos rank fairly across sub-projects —
  hits carry `[scope/]` labels naming which one they're from. Narrow with
  `trail ask "<task>" --in <scope>/` once you know where you're working.

If a returned span is truncated ("+N more lines"), open the file at that exact
range before finalizing. Only open source files when a node genuinely lacks a
needed detail, and then at the exact file:line the node points to — never
re-read whole files.

After big code changes, refresh the graph with `trail build` (deterministic,
no API key, $0).
<!-- trail:end -->
