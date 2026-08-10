"""Default-green plumbing tests: the shipped infrastructure. No holes, no network.

The fill-the-hole acceptance scenarios live in `features/` and run under behave
(`uv run behave --tags=@warmup`), not pytest."""

from hadr_agent.engine_client import EngineClient, EngineError


def test_engine_client_surface():
    for op in (
        "list_scenarios",
        "start_episode",
        "status",
        "building_to_coords",
        "travel_time",
        "dispatch",
        "next_tick",
    ):
        assert callable(getattr(EngineClient, op))
    e = EngineError("BAD", "boom")
    assert e.code == "BAD" and "BAD" in str(e) and e.message == "boom"


def test_client_role_prefix_falls_back(monkeypatch):
    """A role prefix overrides per role; the unprefixed variable is the fallback."""
    from hadr_agent.util import client

    monkeypatch.setenv("OPENAI_KEY", "shared")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://shared/v1")
    monkeypatch.setenv("INTAKE_OPENAI_BASE_URL", "http://localhost:11434/v1")
    monkeypatch.delenv("INTAKE_OPENAI_KEY", raising=False)

    assert str(client("DISPATCH_").base_url).rstrip("/") == "https://shared/v1"
    intake = client("INTAKE_")
    assert str(intake.base_url).rstrip("/") == "http://localhost:11434/v1"
    assert intake.api_key == "shared"  # no INTAKE_OPENAI_KEY, so the shared one
