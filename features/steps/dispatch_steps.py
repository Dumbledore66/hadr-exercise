"""Step definitions for dispatch.feature (DISP-*): run_dispatch end to end with
a scripted model and a fake tool backend. The scripted client and the error
Then-step are shared with agent_loop_steps."""

import asyncio

from agent_loop_steps import ScriptedClient, _call, _turn
from behave import given, then, when

# Shaped exactly like the engine's VehiclePublic, so a state message that reads
# a flat t["x"] or an unconditional t["route"]["eta_ticks"] fails here rather
# than on the first live tick. truck-1 keeps the incident_id of a fire it has
# already put out: the engine never clears it, so coverage needs status too.
TRUCKS = [
    {
        "vehicle_id": "truck-1",
        "label": "Engine 1",
        "position": {"x": 0.0, "y": 0.0},
        "status": "idle",
        "route": None,
        "destination": None,
        "incident_id": "inc-9",
        "last_rationale": "put it out",
    },
    {
        "vehicle_id": "truck-2",
        "label": "Engine 2",
        "position": {"x": 30.0, "y": 40.0},
        "status": "moving",
        "route": {"remaining": 12.0, "total": 50.0, "eta_ticks": 3, "edges": ["e1"]},
        "destination": {
            "requested": {"x": 10.0, "y": 20.0},
            "snapped": {"x": 10.0, "y": 20.0},
        },
        "incident_id": "inc-1",
        "last_rationale": "nearest truck",
    },
]


class FakeBackend:
    async def building_to_coords(self, building_id):
        return {"x": 0.0, "y": 0.0}

    async def travel_time(self, from_spec, to_spec):
        return {"eta_ticks": 3, "distance": 42.0}

    async def dispatch(self, vehicle_id, incident_id, x, y, rationale):
        return {"accepted": True}


@given('an incident store with one open fire "{iid}" at ({x:g}, {y:g})')
def step_store(context, iid, x, y):
    context.store = context.IncidentStore()
    inc = context.store.open("fire", (x, y), tick=1)
    assert inc.incident_id == iid, inc.incident_id


@given('the scripted model dispatches "{vid}" to "{iid}", then yields')
def step_script(context, vid, iid):
    args = {
        "vehicle_id": vid,
        "incident_id": iid,
        "x": 10.0,
        "y": 20.0,
        "rationale": "scripted",
    }
    context.script = [
        _turn("<think>choosing</think>", [_call("call-1", "dispatch", args)]),
        _turn("done"),
    ]


@given('the scripted model closes "{iid}" with note "{note}", then yields')
def step_script_close(context, iid, note):
    args = {"incident_id": iid, "status": "closed", "notes": note}
    context.script = [
        _turn("<think>closing</think>", [_call("call-1", "file_incident_update", args)]),
        _turn("done"),
    ]


@when("the dispatch runs")
def step_run(context):
    context.client = ScriptedClient(context.script)
    context.result = asyncio.run(
        context.dispatch.run_dispatch(
            context.store, TRUCKS, 1, tools=FakeBackend(), client=context.client
        )
    )


@then("no dispatches were recorded")
def step_none(context):
    assert context.result.dispatches == [], context.result.dispatches


@then('the dispatch of "{vid}" to "{iid}" was recorded')
def step_recorded(context, vid, iid):
    got = [(d["vehicle_id"], d["incident_id"]) for d in context.result.dispatches]
    assert (vid, iid) in got, got


@then('incident "{iid}" is closed with reason "{reason}"')
def step_closed(context, iid, reason):
    inc = context.store.get(iid)
    assert inc is not None and inc.status == "closed", inc
    assert inc.close_reason == reason, inc.close_reason
