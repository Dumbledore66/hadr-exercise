"""Step definitions for reconcile.feature. reconcile_reports/reconcile_vision
arrive as context.reconcile (chosen in environment.py); the incident and report
stores live on context.incidents / context.report_store.

reconcile_reports returns one Outcome per report; the scenarios reconcile a single
report at a time, so the checks read context.outcome[0]. The "is one of" and
"has ... = ..." steps are registered before their plainer siblings so behave
matches the specific text first.
"""

from behave import given, then, when
from common_steps import make_report, parse_val


def _open(context):
    return context.incidents.find(status="open")


@given("a fresh reconcile world")
def step_world(context):
    context.incidents = context.IncidentStore()
    context.report_store = context.ReportStore()


@given("these reports are reconciled at tick {tick:d}:")
@when("these reports are reconciled at tick {tick:d}:")
def step_reconcile_reports(context, tick):
    reports = [make_report(context, row) for row in context.table]
    context.outcome = context.reconcile.reconcile_reports(
        reports, context.incidents, context.report_store, tick
    )


@when("truck vision reports at tick {tick:d}:")
def step_vision(context, tick):
    buildings = [{"building_id": r["building_id"], "status": r["status"]} for r in context.table]
    coords_of = {r["building_id"]: (float(r["x"]), float(r["y"])) for r in context.table}
    context.outcome = context.reconcile.reconcile_vision(
        [{"buildings": buildings}], context.incidents, tick, coords_of
    )


@then("the action is one of: {actions}")
def step_action_in(context, actions):
    allowed = {a.strip() for a in actions.split(",")}
    assert context.outcome[0].action in allowed, context.outcome[0].action


@then("the action is {action}")
def step_action(context, action):
    assert context.outcome[0].action == action, context.outcome[0].action


@then("there is {n:d} open incident")
@then("there are {n:d} open incidents")
def step_open_count(context, n):
    assert len(_open(context)) == n, len(_open(context))


@then("open incident {index:d} has report ids: {ids}")
def step_report_ids(context, index, ids):
    expected = {s.strip() for s in ids.split(",") if s.strip()}
    assert set(_open(context)[index].report_ids) == expected, _open(context)[index].report_ids


@then("open incident {index:d} has {field} = {value}")
def step_field(context, index, field, value):
    got = getattr(_open(context)[index], field)
    assert got == parse_val(value), got
