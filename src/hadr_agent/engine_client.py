"""Thin async MCP client for the HADR engine control surface.

Ships working: MCP transport plumbing is not the lesson. Wraps the official SDK's
Streamable HTTP client + ClientSession behind typed helpers, raising EngineError
on any tool error. The outer runner owns the single session and the single
next_tick call per API.md.
"""

from __future__ import annotations

from contextlib import AsyncExitStack

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


class EngineError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


class EngineClient:
    def __init__(self, url: str):
        self._url = url
        self._stack: AsyncExitStack | None = None
        self._sess: ClientSession | None = None

    async def __aenter__(self) -> EngineClient:
        self._stack = AsyncExitStack()
        read, write, _sid = await self._stack.enter_async_context(
            streamable_http_client(self._url)
        )
        self._sess = await self._stack.enter_async_context(ClientSession(read, write))
        await self._sess.initialize()
        return self

    async def __aexit__(self, *exc) -> None:
        if self._stack:
            await self._stack.aclose()
        self._stack = None
        self._sess = None

    async def _call(self, op: str, args: dict | None = None) -> dict:
        assert self._sess is not None  # connect() populates the session before any call
        res = await self._sess.call_tool(op, args or {})
        if res.isError:
            err = (res.structuredContent or {}).get("error", {})
            raise EngineError(
                err.get("code", "ERROR"), err.get("message", "tool error")
            )
        return res.structuredContent or {}

    async def list_scenarios(self) -> dict:
        return await self._call("list_scenarios")

    async def start_episode(self, scenario_id: str, seed: int | None = None) -> dict:
        args: dict[str, object] = {"scenario_id": scenario_id}
        if seed is not None:
            args["seed"] = seed
        return await self._call("start_episode", args)

    async def status(self) -> dict:
        return await self._call("status")

    async def building_to_coords(self, building_id: str) -> dict:
        return await self._call("building_to_coords", {"building_id": building_id})

    async def travel_time(self, from_spec: dict, to_spec: dict) -> dict:
        return await self._call("travel_time", {"from": from_spec, "to": to_spec})

    async def dispatch(
        self,
        expected_tick: int,
        vehicle_id: str,
        incident_id: str,
        destination: dict,
        rationale: str,
    ) -> dict:
        return await self._call(
            "dispatch",
            {
                "expected_tick": expected_tick,
                "vehicle_id": vehicle_id,
                "incident_id": incident_id,
                "destination": destination,
                "rationale": rationale,
            },
        )

    async def next_tick(self, expected_tick: int, tokens: dict | None = None) -> dict:
        # `tokens` is optional and display-only: omit it and the tick is identical.
        args: dict = {"expected_tick": expected_tick}
        if tokens is not None:
            args["tokens"] = tokens
        return await self._call("next_tick", args)
