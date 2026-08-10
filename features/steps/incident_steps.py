"""Step definitions for incidents.feature. The store under test arrives as
context.IncidentStore (chosen in environment.py).

Specific Then steps (coords, report ids) are registered before the generic
`has {field} = {value}` so behave matches them first.
"""

from behave import given, then, when
from common_steps import parse_val, point

# Columns that are positional args to open(); everything else is a belief field.
CORE = {"incident_type", "x", "y", "tick"}


def _coords(row):
    return (float(row["x"]), float(row["y"]))


def _fields(row, exclude=CORE):
    return {h: parse_val(row[h]) for h in row.headings if h not in exclude and row[h] != ""}


@given("an empty incident store")
def step_empty(context):
    context.store = context.IncidentStore()


@given("these incidents are opened:")
def step_open_many(context):
    for row in context.table:
        context.store.open(row["incident_type"], _coords(row), int(row["tick"]), **_fields(row))


@given('report "{rid}" is linked to incident "{iid}"')
def step_link(context, rid, iid):
    context.store.link(iid, rid)


@given('incident "{iid}" is closed as "{reason}" at tick {tick:d}')
def step_close(context, iid, reason, tick):
    context.store.close(iid, reason, tick)


@when("I open an incident:")
def step_open_one(context):
    row = context.table[0]
    context.result = context.store.open(
        row["incident_type"], _coords(row), int(row["tick"]), **_fields(row)
    )


@when('I get incident "{iid}"')
def step_get(context, iid):
    context.result = context.store.get(iid)


@when('I update incident "{iid}" at tick {tick:d}:')
def step_update(context, iid, tick):
    context.result = context.store.update(
        iid, tick=tick, **_fields(context.table[0], exclude=set()))


@when("I find incidents with:")
def step_find(context):
    row = context.table[0]
    kwargs = {}
    if row["near"]:
        kwargs["near"] = point(row["near"])
    if row["radius"]:
        kwargs["radius"] = float(row["radius"])
    if row["incident_type"]:
        kwargs["incident_type"] = row["incident_type"]
    if row["status"]:
        kwargs["status"] = None if row["status"] == "any" else row["status"]
    context.result = context.store.find(**kwargs)


@then("the incident's report ids are: {ids}")
def step_when_report_ids(context, ids):
    expected = {s.strip() for s in ids.split(",") if s.strip()}
    assert set(context.result.report_ids) == expected, context.result.report_ids


@then("the incident's {field} is {value}")
def step_when_field(context, field, value):
    got = getattr(context.result, field)
    assert got == parse_val(value), got


@then('incident "{iid}" has {field} = {value}')
def step_field(context, iid, field, value):
    got = getattr(context.store.get(iid), field)
    assert got == parse_val(value), got
