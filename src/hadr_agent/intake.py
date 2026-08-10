"""Stateless intake: one human contact in, one schema-conforming report out.

Ships working: the model-call plumbing (client, JSON mode, token budget, parse).
Ships working too: `_project_claim`, the zero-token path for structured claims.
HOLE: `_finalize` (schema + envelope authority). `_project_claim` routes through
it, so INT-2/INT-3 need a minimal `_finalize` at stage 1; the model path needs
the rest of it at stage 2.
"""

from __future__ import annotations

import json
import os

from openai import OpenAI

from .util import TokenUse, prompt
from .util import client as _client

# Completion budget for the JSON, generous on purpose: too small a budget truncates
# to empty content, which defaults to `unknown` and silently wrecks accuracy. Leave
# room for a reasoning model, which spends most of its completion before the JSON.
MAX_TOKENS = 1400


def _finalize(fields: dict, contact: dict) -> dict:
    """HOLE (stage 1 minimally, stage 2 fully): stamp envelope authority onto the
    fields and normalize to datasets/report.schema.json. Required behaviour:

    - contact_id, reported_location: copied from the contact envelope (never the model).
    - incident_type: one of fire/none/unknown; coerce anything else to unknown.
    - notes: "" when absent.
    - a `none` report carries no fire severity/headcount (force both to null).
    """
    raise NotImplementedError("stage 1/2: enforce the report schema and envelope authority")


def _project_claim(contact: dict) -> dict:
    """A structured claim -> report, WITHOUT a model call. Ships working. Note the
    exit: a claim you were handed goes through the same _finalize as anything a
    model made up, because envelope authority is not a question of trust."""
    claim = contact["payload"]["claim"]
    fields = {
        "incident_type": claim.get("incident_type"),
        "severity": claim.get("severity"),
        "headcount": claim.get("headcount"),
        "event_time": claim.get("event_time"),
    }
    return _finalize(fields, contact)


def extract_report(contact: dict, client: OpenAI | None = None) -> tuple[dict, TokenUse]:
    """Return (report, usage). Structured claims skip the model (zero usage);
    human text calls it. Ships WIRED but the raw model output comes back
    UNVALIDATED until you implement _finalize (stage 2)."""
    ptype = contact.get("payload_type")
    if ptype == "structured_report":
        return _project_claim(contact), TokenUse()
    if ptype != "human_text":
        raise ValueError(f"intake handles human contacts only, got {ptype!r}")

    text = contact["payload"].get("text", "")
    client = client or _client("INTAKE_")
    resp = client.chat.completions.create(
        model=os.environ.get("INTAKE_MODEL", "mimo-v2.5"),
        messages=[
            {"role": "system", "content": prompt("intake_system.md")},
            {
                "role": "user",
                "content": f"source_type: {contact.get('source_type', '')}\n"
                f"occurred_at: {contact.get('occurred_at', 0)}\n"
                f"contact text:\n{text}\n\nEmit the report JSON now.",
            },
        ],
        response_format={"type": "json_object"},
        max_tokens=MAX_TOKENS,
        temperature=0,
    )
    fields = _parse(resp.choices[0].message.content)
    usage = TokenUse()
    usage.add(resp.usage)
    # TODO (stage 2): return _finalize(fields, contact), usage
    return fields, usage


def _parse(content: str | None) -> dict:
    """Parse the model's JSON, salvaging an object wrapped in prose. Ships working."""
    if not content:
        return {"incident_type": "unknown"}
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start, end = content.find("{"), content.rfind("}")
        if 0 <= start < end:
            try:
                return json.loads(content[start : end + 1])
            except json.JSONDecodeError:
                pass
    return {"incident_type": "unknown"}
