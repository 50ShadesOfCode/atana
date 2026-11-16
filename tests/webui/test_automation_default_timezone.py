from __future__ import annotations

from nanobot.webui.ws_http import _parse_automation_update


def test_cron_without_timezone_uses_configured_default() -> None:
    parsed = _parse_automation_update(
        {"schedule": {"kind": "cron", "expr": "0 9 * * *"}},
        default_timezone="Asia/Shanghai",
    )

    assert isinstance(parsed, dict)
    assert parsed["schedule"].tz == "Asia/Shanghai"


def test_cron_keeps_explicit_timezone() -> None:
    parsed = _parse_automation_update(
        {"schedule": {"kind": "cron", "expr": "0 9 * * *", "tz": "UTC"}},
        default_timezone="Asia/Shanghai",
    )

    assert isinstance(parsed, dict)
    assert parsed["schedule"].tz == "UTC"
