# Upstream

This repository is a private fork of [HKUDS/nanobot](https://github.com/HKUDS/nanobot). `upstream` is fetch-only and its push URL is disabled; `origin` is the fork.

## Branches

- `main` — exact mirror of `upstream/main`. Fast-forward only: no commits, no merge commits.
- `dev` — integration branch. All fork-only work lands here.
- `feat/*`, `fix/*` — short-lived branches off `dev`, merged back into `dev`.

## Syncing upstream

```bash
git fetch upstream --prune
git checkout main
git merge --ff-only upstream/main
git push origin main
git checkout dev
git merge main
```

`dev` is long-lived and pushed, so it is merged, never rebased.

## Pushing

Push over SSH (`origin` is `git@github.com:50ShadesOfCode/atana.git`). The `gh` OAuth token has no `workflow` scope, so an HTTPS push that touches `.github/workflows/*` is rejected by GitHub; SSH keys are not subject to that restriction. The first push of the full history is roughly 80 MB, which a single HTTPS request fails with a 408 — SSH handles it, in about 15 minutes.

## Keeping merges cheap

- Prefer new files and narrow seams over rewriting upstream files. Every edited upstream file is a future conflict.
- Keep configuration changes additive: new optional fields, no renames or removals.
- Put fork-only tests in new test files where upstream is unlikely to touch the same path.
- Do not commit local artifacts: `.ua/`, `.trail/`, `opencode.json`, build output.
- Record every upstream file a change edits in the list below, so a conflict is resolved from the list instead of from memory.

## Touched upstream files

### Model selection (ad-hoc models, session and default)

- `nanobot/agent/loop.py` — session runtime resolution, `set_session_model`
- `nanobot/agent/model_presets.py` — preset loader accepts a preset object, ad-hoc preset builder
- `nanobot/agent/model_runtime.py` — `resolve_model` and its cache
- `nanobot/agent/tools/runtime_control.py`, `nanobot/agent/tools/self.py` — session-scoped `model` writes
- `nanobot/command/builtin.py` — `/model <model-id> [--provider] [--context]`
- `nanobot/providers/factory.py` — `load_provider_snapshot(preset=...)`
- `nanobot/session/model_selection.py` — `_nanobot_model` metadata
- `nanobot/webui/session_projection.py`, `nanobot/webui/session_list_index.py` — expose `model`
- `webui/src/lib/{api,types,reload-cache}.ts`, `webui/src/hooks/useSessions.ts` — model on the session summary
- `webui/src/components/thread/{ModelPresetBadge,ThreadComposer,ThreadShell,model-preset}.tsx` — model browser in the composer
- `webui/src/components/settings/**` — editable default model
- `tui/src/{app/app,client/api,client/types}.ts` — show a session model
- `docs/{chat-commands,my-tool}.md`

Fork-only files (no upstream counterpart): `webui/src/components/thread/useModelCatalog.ts`, `tests/agent/test_session_model_selection.py`, `tests/session/test_model_selection_metadata.py`.

## Releases

Upstream tags are kept as they are. Fork releases are tagged `dev-YYYY.MM.DD` from `dev`.
