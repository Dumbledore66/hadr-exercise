"""Helpers and assertions shared across units. Each Then line in a feature maps
to one function; behave loads every steps/*.py together, so a step text is
defined once here and reused by any feature that says it.
"""

from behave import then


def parse_val(s):
    """A table/step cell -> bool, int, float, or str (blank -> None)."""
    if s == "":
        return None
    if s in ("true", "false"):
        return s == "true"
    for cast in (int, float):
        try:
            return cast(s)
        except ValueError:
            pass
    return s


def point(text):
    """'(x, y)' -> (float, float)."""
    x, y = text.strip("() ").split(",")
    return (float(x), float(y))


def make_report(context, row):
    """A table row -> context.Report. severity/headcount/qualifier columns are
    optional (stage-3 tables; they need the fields your Report grows then)."""
    x, y = float(row["x"]), float(row["y"])
    d = {
        "contact_id": row["contact_id"],
        # Raw reported location; the store filters on the resolved coords, so
        # the raw shape is a placeholder here.
        "reported_location": {"kind": "coordinates", "coordinates": {"x": x, "y": y}},
        "incident_type": row["incident_type"],
        "coords": (x, y),
        "tick": int(row["tick"]),
    }
    if row.get("severity"):
        d["severity"] = {"value": row["severity"]}
    if row.get("headcount"):
        d["headcount"] = {
            "value": int(row["headcount"]),
            "qualifier": row.get("qualifier") or None,
        }
    return context.Report(**d)


def _id(item):
    """Reports carry contact_id, incidents carry incident_id."""
    return getattr(item, "contact_id", None) or item.incident_id


@then("the result ids are: {ids}")
def step_result_ids(context, ids):
    expected = [s.strip() for s in ids.split(",") if s.strip()]
    got = [_id(r) for r in context.result]
    assert got == expected, got


@then("the result count is {n:d}")
def step_result_count(context, n):
    assert len(context.result) == n, len(context.result)


@then("the result is empty")
def step_result_empty(context):
    assert len(context.result) == 0, context.result
