"""Shared LLM plumbing: token accounting, the API client, prompt loading."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import cache
from importlib import resources

from openai import OpenAI
from openai.types.chat import ChatCompletionToolUnionParam


@dataclass
class TokenUse:
    """Provider-reported token totals, shared by intake and dispatch."""

    read: int = 0
    write: int = 0
    cache_read: int = 0

    @property
    def total(self) -> int:
        return self.read + self.write

    def add(self, u) -> None:
        """Accumulate another TokenUse, or an OpenAI-shape response usage
        (prompt_tokens already includes the cached subset, reported separately
        under prompt_tokens_details.cached_tokens - implicit caching)."""
        if isinstance(u, TokenUse):
            self.read += u.read
            self.write += u.write
            self.cache_read += u.cache_read
            return
        self.read += getattr(u, "prompt_tokens", 0) or 0
        self.write += getattr(u, "completion_tokens", 0) or 0
        details = getattr(u, "prompt_tokens_details", None)
        self.cache_read += (getattr(details, "cached_tokens", 0) or 0) if details else 0


def client(role: str = "") -> OpenAI:
    """`role` is an env prefix ("INTAKE_"/"DISPATCH_"); a prefixed variable wins,
    the unprefixed one is the fallback. Set INTAKE_OPENAI_BASE_URL to run intake
    against a local server while dispatch stays remote."""

    def env(name, default=None):
        return os.environ.get(role + name) or os.environ.get(name, default)

    key = env("OPENAI_KEY")
    if not key:
        raise RuntimeError("OPENAI_KEY not set (load .env)")
    # Default is the OpenCode Go endpoint; see .env.example before changing it.
    base = env("OPENAI_BASE_URL", "https://opencode.ai/zen/go/v1")
    return OpenAI(base_url=base, api_key=key)


def print_summary(scenario_id: str, seed, summary: dict) -> None:
    print("\n" + "=" * 56)
    print(f"scenario   : {scenario_id}  seed={seed}")
    print(f"run_id     : {summary.get('run_id')}")
    print(f"terminal   : {summary.get('terminal_reason')} at tick {summary.get('tick')}")
    print(f"casualties : {summary.get('casualties')}")
    print(f"buildings_lost : {summary.get('buildings_lost')}")
    print("-" * 56)
    print("tokens (provider-reported):")
    intake, dispatch = summary["intake_tokens"], summary["dispatch_tokens"]
    for name, u in (("intake  ", intake), ("dispatch", dispatch)):
        print(
            f"  {name}: {u.total:7d}  (read {u.read}, write {u.write}, cache_read {u.cache_read})"
        )
    print(f"  TOTAL   : {intake.total + dispatch.total:7d}")
    print("=" * 56)


@cache
def prompt(fname: str) -> str:
    return resources.files("hadr_agent.prompts").joinpath(fname).read_text()


STR = {"type": "string"}
NUM = {"type": "number"}
OBJ = {"type": "object"}


def tool(
    name: str, desc: str, params: dict, required: list | None = None
) -> ChatCompletionToolUnionParam:
    """OpenAI function-tool schema; all params required unless `required` given."""
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": desc,
            "parameters": {
                "type": "object",
                "properties": params,
                "required": required if required is not None else list(params),
            },
        },
    }
