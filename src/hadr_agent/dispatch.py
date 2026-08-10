"""Dispatch: the general agent loop (agent.py) configured for truck dispatch.

Ships working: `run_dispatch` (the configuration - prompt, state message, tool
schemas, tool execution incl. the "dispatch must reference a filed incident"
check). HOLES: the loop itself (agent.agent_loop), `_state_message`, and the
system prompt (prompts/dispatch_system.md).

The model issues dispatches through tools backed by the runner's live MCP
session (`tools: DispatchTools`). It never calls next_tick. Tool rounds are
bounded per tick to cap tokens and prevent loops.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Protocol

from openai import OpenAI
from openai.types.chat import ChatCompletionToolUnionParam

from .agent import agent_loop
from .stores.incidents import IncidentStore
from .util import NUM, OBJ, STR, TokenUse, prompt
from .util import tool as _tool

MAX_TOOL_ROUNDS = 6
MAX_TOKENS = 900


class DispatchTools(Protocol):
    """What the dispatch loop needs from its backend (Episode in the runner;
    tests pass a fake). Structural - no inheritance required."""

    async def building_to_coords(self, building_id: str) -> dict: ...

    async def travel_time(self, from_spec: dict, to_spec: dict) -> dict: ...

    async def dispatch(
        self, vehicle_id: str, incident_id: str, x: float, y: float, rationale: str
    ) -> dict: ...


@dataclass
class DispatchResult:
    usage: TokenUse = field(default_factory=TokenUse)
    dispatches: list[dict] = field(default_factory=list)
    # Debug hooks: rounds shows when the model hits MAX_TOOL_ROUNDS; plan is the
    # model's final free-text rationale (<think> stripped).
    rounds: int = 0
    plan: str = ""


def _tool_defs() -> list[ChatCompletionToolUnionParam]:
    return [
        _tool(
            "building_to_coords",
            "Convert a building ID (l<int>) to its exact world point.",
            {"building_id": STR},
        ),
        _tool(
            "travel_time",
            "ETA in ticks and distance between two endpoints. Each of `from`/`to` "
            'is either {"vehicle_id": "truck-1"} or {"point": {"x":.., "y":..}}.',
            {"from": OBJ, "to": OBJ},
        ),
        _tool(
            "file_incident_update",
            "Record a belief change on an incident before/without dispatching "
            "(e.g. mark it covered, note a contradiction). Fields: status, notes.",
            {"incident_id": STR, "status": STR, "notes": STR},
            required=["incident_id"],
        ),
        _tool(
            "dispatch",
            "Send a truck to a world point to serve an incident. incident_id MUST "
            "be a real filed incident and rationale MUST be a one-sentence "
            "justification. Retargets a moving/firefighting truck.",
            {
                "vehicle_id": STR,
                "incident_id": STR,
                "x": NUM,
                "y": NUM,
                "rationale": STR,
            },
        ),
    ]


def _state_message(incidents: IncidentStore, trucks: list[dict], tick: int) -> str:
    """HOLE (stage 1/stage 4): build the user message the model reasons over from
    the open incidents and truck states. A raw dump makes the weak dispatch model
    stack both trucks on one fire; pre-reconcile the state (COVERED/UNCOVERED,
    people-first priority, FREE vs committed trucks) so the model only has to
    choose, and end with a clear instruction.

    Each `trucks` entry is a live engine vehicle observation:
    `{vehicle_id, status (idle/moving/firefighting), position: {x, y}, incident_id
    (the incident of this truck's most recent dispatch - the engine never clears
    it, so it only means "serving" while status is moving or firefighting; that
    pairing is the COVERED/UNCOVERED signal), route: {eta_ticks}}`. Coordinates
    are nested under `position`, NOT flat top-level x/y. The DISP-* fixture
    mirrors this shape, down to an idle truck holding the incident_id of a fire
    it already put out, so `t["x"]` fails there rather than on the first live
    tick."""
    raise NotImplementedError("stage 1/4: build the dispatch state message")


async def run_dispatch(
    incidents: IncidentStore,
    trucks: list[dict],
    tick: int,
    tools: DispatchTools,
    client: OpenAI,
    max_rounds: int = MAX_TOOL_ROUNDS,
) -> DispatchResult:
    """Configure agent.agent_loop for dispatch. Ships working: everything
    dispatch-specific is in the arguments; the loop is the general machine."""
    result = DispatchResult()

    async def run_tool(name: str, args: dict) -> dict:
        return await _run_tool(name, args, incidents, tools, result, tick)

    loop = await agent_loop(
        client=client,
        model=os.environ.get("DISPATCH_MODEL", "minimax-m3"),
        system=prompt("dispatch_system.md"),
        user=_state_message(incidents, trucks, tick),
        tool_defs=_tool_defs(),
        run_tool=run_tool,
        max_rounds=max_rounds,
        max_tokens=MAX_TOKENS,
    )
    result.usage, result.rounds, result.plan = loop.usage, loop.rounds, loop.final
    return result


async def _run_tool(
    name: str,
    args: dict,
    incidents: IncidentStore,
    tools: DispatchTools,
    result: DispatchResult,
    tick: int,
) -> dict:
    """Execute one tool call. Ships working. The filed-incident check on dispatch
    is the only enforcement (the engine logs incident_id without validating it)."""
    try:
        if name == "building_to_coords":
            return await tools.building_to_coords(args["building_id"])
        if name == "travel_time":
            return await tools.travel_time(args.get("from", {}), args.get("to", {}))
        if name == "file_incident_update":
            iid = args.get("incident_id", "")
            if incidents.get(iid) is None:
                return {"error": f"no such incident {iid}"}
            fields = {k: v for k, v in args.items() if k in ("status", "notes") and v is not None}
            # Close through the store's close() so close_reason is recorded; a
            # bare update(status="closed") would flip status and leave it None.
            if fields.get("status") == "closed":
                incidents.close(iid, fields.get("notes") or "closed by dispatch", tick)
            else:
                incidents.update(iid, tick=tick, **fields)
            return {"ok": True}
        if name == "dispatch":
            iid = args.get("incident_id", "")
            if incidents.get(iid) is None:
                return {
                    "error": f"incident_id {iid!r} is not a filed incident; "
                    "open/reference a real incident before dispatching"
                }
            out = await tools.dispatch(
                args["vehicle_id"],
                iid,
                float(args["x"]),
                float(args["y"]),
                args.get("rationale", ""),
            )
            if out.get("accepted"):
                result.dispatches.append(
                    {
                        "vehicle_id": args["vehicle_id"],
                        "incident_id": iid,
                        "rationale": args.get("rationale", ""),
                    }
                )
            return out
        return {"error": f"unknown tool {name}"}
    except KeyError as e:
        return {"error": f"missing argument {e}"}
    except Exception as e:  # surface tool failure to the model, do not crash the tick
        return {"error": str(e)[:200]}
