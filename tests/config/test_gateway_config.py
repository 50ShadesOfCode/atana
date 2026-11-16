import pytest

from nanobot.config.schema import AgentDefaults, Config, GatewayConfig


def test_gateway_restart_mode_accepts_camel_alias():
    config = Config.model_validate({"gateway": {"restartMode": "exit"}})

    assert config.gateway.restart_mode == "exit"
    assert config.model_dump(by_alias=True)["gateway"]["restartMode"] == "exit"


def test_gateway_restart_mode_rejects_unknown_value():
    with pytest.raises(ValueError):
        GatewayConfig(restart_mode="service")


def test_max_tool_result_chars_rejects_zero():
    with pytest.raises(ValueError):
        AgentDefaults(max_tool_result_chars=0)
