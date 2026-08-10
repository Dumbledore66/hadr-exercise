"""Step definitions for reports.feature.

Nothing hidden: every Given/When/Then line in the feature maps to one function
here. The store class under test arrives as context.ReportStore / context.Report
(chosen in environment.py). Read this file top to bottom and you have seen the
entire test machine.
"""

from behave import given, then, when
from common_steps import make_report, parse_val, point


@given("an empty report store")
def step_empty_store(context):
    context.store = context.ReportStore()


@given("a report is added:")
@given("reports are added:")
def step_add_reports(context):
    for row in context.table:
        context.store.add(make_report(context, row))


@when("I add a report:")
def step_add_one(context):
    context.result = context.store.add(make_report(context, context.table[0]))


@when('I get report "{contact_id}"')
def step_get(context, contact_id):
    context.result = context.store.get(contact_id)


@when("I find_reports with:")
def step_find(context):
    row = context.table[0]
    context.result = context.store.find_reports(
        near=point(row["near"]) if row["near"] else None,
        radius=parse_val(row["radius"]),
        start=parse_val(row["start"]),
        end=parse_val(row["end"]),
    )


@then('the report\'s incident_type is "{value}"')
def step_result_incident_type(context, value):
    assert context.result.incident_type == value, context.result


@then("the store holds {n:d} report")
@then("the store holds {n:d} reports")
def step_count(context, n):
    got = len(context.store.all())
    assert got == n, got


@then('report "{contact_id}" has incident_type "{value}"')
def step_get_field(context, contact_id, value):
    got = context.store.get(contact_id).incident_type
    assert got == value, got


# "the result ids are:" / "the result count is" live in common_steps.py.
