from nanobot.session.model_selection import (
    SESSION_MODEL_METADATA_KEY,
    SessionModelSelection,
    model_selection_from_metadata,
    model_selection_metadata,
)


def test_round_trips_a_selection() -> None:
    selection = SessionModelSelection(
        model="openai/gpt-4.1",
        provider="openai",
        context_window_tokens=32_768,
    )

    payload = model_selection_metadata(selection)

    assert payload == {
        "model": "openai/gpt-4.1",
        "provider": "openai",
        "context_window_tokens": 32_768,
    }
    assert model_selection_from_metadata({SESSION_MODEL_METADATA_KEY: payload}) == selection


def test_omits_unknown_context_window() -> None:
    payload = model_selection_metadata(SessionModelSelection(model="gpt-4.1"))

    assert payload == {"model": "gpt-4.1", "provider": "auto"}


def test_ignores_malformed_public_metadata() -> None:
    assert model_selection_from_metadata(None) is None
    assert model_selection_from_metadata({"other": 1}) is None
    assert model_selection_from_metadata({SESSION_MODEL_METADATA_KEY: "gpt-4.1"}) is None
    assert model_selection_from_metadata({SESSION_MODEL_METADATA_KEY: {"model": ""}}) is None
    assert model_selection_from_metadata({SESSION_MODEL_METADATA_KEY: {"model": 7}}) is None


def test_normalizes_missing_or_invalid_provider_and_window() -> None:
    selection = model_selection_from_metadata({
        SESSION_MODEL_METADATA_KEY: {
            "model": "  gpt-4.1  ",
            "provider": "",
            "context_window_tokens": -1,
        },
    })

    assert selection == SessionModelSelection(model="gpt-4.1", provider="auto")
