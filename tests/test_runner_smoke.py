"""No-LLM runner smoke: proves the runner SHELL end to end against a real engine
over MCP with the inner loop still empty (holes unimplemented). Start the engine
first (the launcher command on the course site); the test drives whatever is
serving at HADR_ENGINE_URL and skips when nothing is. use_llm=False means zero
model tokens and no OPENAI_KEY.
"""

from __future__ import annotations

import asyncio
import os

import httpx
import pytest

from hadr_agent.runner import run_episode

ENGINE_URL = os.environ.get("HADR_ENGINE_URL", "http://127.0.0.1:8000/mcp")
SCENARIO = "stage1-basic@londone"


@pytest.fixture(scope="module")
def engine():
    try:
        httpx.get(ENGINE_URL.removesuffix("/mcp") + "/healthz", timeout=2.0).raise_for_status()
    except httpx.HTTPError:
        pytest.skip(f"no engine serving at {ENGINE_URL} (start one, or set HADR_ENGINE_URL)")
    return ENGINE_URL


def test_runner_shell_reaches_terminal(engine):
    summary = asyncio.run(run_episode(engine, SCENARIO, seed=777, use_llm=False))
    assert summary["terminal_reason"] is not None
    assert isinstance(summary["casualties"], int)
    assert isinstance(summary["buildings_lost"], int)
    # no models were called
    assert summary["intake_tokens"].total + summary["dispatch_tokens"].total == 0
