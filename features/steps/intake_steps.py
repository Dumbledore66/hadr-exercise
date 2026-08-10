"""Step definitions for intake.feature. extract_report arrives as
context.intake (chosen in environment.py) and returns (report_dict, usage).
The contact and the expected reported_location come in as JSON doc-strings.
"""

import json

from behave import then, when


@when("I extract a report from the contact:")
def step_extract(context):
    contact = json.loads(context.text)
    context.report, context.usage = context.intake.extract_report(contact)


@then('the report field "{field}" is "{value}"')
def step_field_str(context, field, value):
    assert context.report[field] == value, context.report.get(field)


@then('the report field "{field}" is null')
def step_field_null(context, field):
    assert context.report[field] is None, context.report.get(field)


@then('the report field "{field}" equals the json:')
def step_field_json(context, field):
    expected = json.loads(context.text)
    assert context.report[field] == expected, context.report.get(field)


@then("extraction spent {n:d} tokens")
def step_tokens(context, n):
    assert context.usage.total == n, context.usage.total
