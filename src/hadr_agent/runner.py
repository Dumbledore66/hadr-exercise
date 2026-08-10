"""Runner shell: owns the MCP session and the single next_tick per tick.

Ships working. Sequence: start_episode -> loop [intake -> reconcile -> dispatch
-> next_tick] -> terminal, then print the outcome plus token totals. The runner
is the ONLY caller of next_tick. The three steps inside `_process_tick` are the
HOLES you fill in stages 1-4; out of the box the loop ticks cleanly to terminal
(a provable shell) while saving nobody.

You run the engine yourself, with the launcher command from the course site.
"""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass, field

from dotenv import load_dotenv
from openai import OpenAI

# Unused until you fill the holes in _process_tick.
from . import dispatch as dispatch_mod
from . import intake as intake_mod  # noqa: F401
from .engine_client import EngineClient
from .stores.incidents import IncidentStore
from .stores.reports import Report, ReportStore
from .util import TokenUse, print_summary
from .util import client as llm_client

ENGINE_URL = "http://127.0.0.1:8000/mcp"


@dataclass
class Episode:
    """Per-episode state threaded through the tick loop. Doubles as the dispatch
    model's tool backend: run_dispatch takes any object with async
    building_to_coords / travel_time / dispatch, and Episode is that object."""

    client: EngineClient
    use_llm: bool  # If True, connect to the LLM provider.
    tick: int = 0  # current expected_tick for dispatch commands
    incidents: IncidentStore = field(default_factory=IncidentStore)
    reports: ReportStore = field(default_factory=ReportStore)
    seen: set = field(default_factory=set)
    intake_tokens: TokenUse = field(default_factory=TokenUse)
    dispatch_tokens: TokenUse = field(default_factory=TokenUse)
    # Separate clients so INTAKE_/DISPATCH_ env prefixes can point the two roles
    # at different endpoints; unprefixed OPENAI_* still covers both.
    intake_llm: OpenAI | None = None
    dispatch_llm: OpenAI | None = None
    _coords_cache: dict[str, tuple[float, float]] = field(default_factory=dict)

    def __post_init__(self):
        if self.use_llm:
            self.intake_llm = self.intake_llm or llm_client("INTAKE_")
            self.dispatch_llm = self.dispatch_llm or llm_client("DISPATCH_")

    def token_report(self) -> dict:
        """Running totals per role, shaped for next_tick's optional `tokens`."""
        return {
            "intake": {"read": self.intake_tokens.read,
                       "write": self.intake_tokens.write,
                       "cache_read": self.intake_tokens.cache_read},
            "dispatch": {"read": self.dispatch_tokens.read,
                         "write": self.dispatch_tokens.write,
                         "cache_read": self.dispatch_tokens.cache_read},
        }

    async def coords_of(self, building_id: str) -> tuple[float, float]:
        """building_id -> public point, cached. Location plumbing for
        intake/reconcile."""
        if building_id not in self._coords_cache:
            r = await self.client.building_to_coords(building_id)
            p = r["point"]
            self._coords_cache[building_id] = (p["x"], p["y"])
        return self._coords_cache[building_id]

    async def location_coords(self, loc: dict | None) -> tuple[float, float] | None:
        """Resolve a report's reported_location (building_id or coordinates)
        to a point."""
        if not loc:
            return None
        if loc.get("kind") == "building_id":
            return await self.coords_of(loc["building_id"])
        if loc.get("kind") == "coordinates":
            c = loc["coordinates"]
            return (c["x"], c["y"])
        return None

    # -- the dispatch model's tools, backed by the live MCP session -----------

    async def building_to_coords(self, building_id: str) -> dict:
        x, y = await self.coords_of(building_id)
        return {"x": x, "y": y}

    async def travel_time(self, from_spec: dict, to_spec: dict) -> dict:
        r = await self.client.travel_time(from_spec, to_spec)
        return {"eta_ticks": r.get("eta_ticks"), "distance": r.get("distance")}

    async def dispatch(
        self, vehicle_id: str, incident_id: str, x: float, y: float, rationale: str
    ) -> dict:
        r = await self.client.dispatch(
            self.tick, vehicle_id, incident_id, {"x": x, "y": y}, rationale
        )
        return {"accepted": bool(r.get("accepted"))}


async def _process_tick(ep: Episode, obs: dict) -> None:
    """One tick of the inner loop. Sensor passthrough ships working; intake,
    reconcile, and dispatch are HOLES you fill in stages 1-4."""
    tick = obs["tick"]
    ep.tick = tick

    # Typed truck observations bypass intake (they are ground truth); human
    # contacts go to intake. This split ships working.
    new_human: list[dict] = []
    observations: list[dict] = []
    for c in obs.get("contacts", []):
        if c["contact_id"] in ep.seen:
            continue
        ep.seen.add(c["contact_id"])
        if c.get("payload_type") == "truck_observation":
            observations.append(c["payload"])
        else:
            new_human.append(c)

    # ---- HOLE (stage 1-2, intake) ------------------------------------------
    # For each contact in `new_human`: call intake_mod.extract_report(c,
    # client=ep.intake_llm), resolve its reported_location to coords via
    # ep.location_coords(...), build a Report, and ep.intake_tokens.add(usage).
    new_reports: list[Report] = []  # noqa: F841 - consumed once you fill reconcile

    # ---- HOLE (stage 1/3, reconcile) ---------------------------------------
    # Fold `new_reports` into the stores with reconcile_mod.reconcile_reports(...).
    # Resolve each observation building to a point and apply
    # reconcile_mod.reconcile_vision(...). Stage 1 may open one incident per
    # report; deterministic reconciliation arrives in stage 3.

    if ep.use_llm:
        assert ep.dispatch_llm
        result = await dispatch_mod.run_dispatch(
            ep.incidents, obs.get("vehicles", []), tick, tools=ep, client=ep.dispatch_llm
        )
        ep.dispatch_tokens.add(result.usage)



async def run_episode(
    url: str,
    scenario_id: str,
    seed: int | None,
    use_llm: bool = True,
) -> dict:
    """Drive one episode end to end. Ships working: session, start_episode, the
    tick loop with exactly one next_tick per tick, and terminal handling. The
    terminal next_tick response carries the outcome (casualties, buildings lost)."""
    async with EngineClient(url) as client:
        ep = Episode(client, use_llm)
        start = await client.start_episode(scenario_id, seed)
        run_id = start["run_id"]
        obs = start["observation"]
        outcome = None

        while obs["lifecycle"] == "running":
            await _process_tick(ep, obs)
            # Report our own usage to the wall display. Self-reported and
            # display-only: the engine measures no tokens and checks nothing.
            res = await client.next_tick(obs["tick"], tokens=ep.token_report())
            obs = res["observation"]
            outcome = res.get("outcome")

    return {
        "run_id": run_id,
        "terminal_reason": obs.get("terminal_reason"),
        "tick": obs["tick"],
        "casualties": (outcome or {}).get("casualties"),
        "buildings_lost": (outcome or {}).get("buildings_lost"),
        "intake_tokens": ep.intake_tokens,
        "dispatch_tokens": ep.dispatch_tokens,
    }


def main() -> None:
    ap = argparse.ArgumentParser(prog="hadr-runner")
    ap.add_argument("scenario_id")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument(
        "--server",
        default=ENGINE_URL,
        help="engine MCP endpoint, must end in /mcp (default: %(default)s; "
        "start one with the launcher command on the course site)",
    )
    ap.add_argument(
        "--no-llm",
        action="store_true",
        help="run intake+reconcile but skip the dispatch model (plumbing check)",
    )
    args = ap.parse_args()

    url = args.server.rstrip("/")
    if not url.endswith("/mcp"):
        ap.error(f"--server must end in /mcp (got {args.server!r}; try {url}/mcp)")

    load_dotenv()
    summary = asyncio.run(run_episode(url, args.scenario_id, args.seed, use_llm=not args.no_llm))
    print_summary(args.scenario_id, args.seed, summary)


if __name__ == "__main__":
    main()
