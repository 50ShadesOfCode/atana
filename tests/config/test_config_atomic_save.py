from __future__ import annotations

import json
import os
import stat
from pathlib import Path

import pytest

import nanobot.utils.file_io as file_io
from nanobot.config.loader import load_config, resolve_config_env_vars, save_config
from nanobot.config.schema import Config


def test_save_config_round_trips(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    config = Config()
    config.agents.defaults.model = "saved-model"
    save_config(config, path)
    loaded = load_config(path)
    assert loaded.agents.defaults.model == "saved-model"


@pytest.mark.skipif(os.name == "nt", reason="Windows does not expose POSIX file modes")
def test_save_config_preserves_existing_file_mode(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text("{}", encoding="utf-8")
    path.chmod(0o600)

    save_config(Config(), path)

    assert stat.S_IMODE(path.stat().st_mode) == 0o600


@pytest.mark.skipif(os.name == "nt", reason="Windows does not expose POSIX file modes")
def test_save_config_creates_the_file_owner_only(tmp_path: Path) -> None:
    path = tmp_path / "config.json"

    save_config(Config(), path)

    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_save_config_keeps_environment_values_as_placeholders(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("NANOBOT_PROVIDERS__OPENAI__API_KEY", "sk-from-env")
    path = tmp_path / "config.json"
    config = load_config(path)

    save_config(config, path)

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["providers"]["openai"]["apiKey"] == "${NANOBOT_PROVIDERS__OPENAI__API_KEY}"
    assert "sk-from-env" not in path.read_text(encoding="utf-8")
    resolved = resolve_config_env_vars(load_config(path))
    assert resolved.providers.openai.api_key == "sk-from-env"


def test_save_config_preserves_existing_file_when_write_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "config.json"
    save_config(Config(), path)
    before = path.read_text(encoding="utf-8")

    def boom(source: Path, destination: Path) -> None:  # noqa: ARG001
        raise OSError("simulated crash before replace")

    monkeypatch.setattr(file_io, "replace_atomic", boom)
    with pytest.raises(OSError, match="simulated crash"):
        save_config(Config(), path)

    assert path.read_text(encoding="utf-8") == before
    assert json.loads(before)
