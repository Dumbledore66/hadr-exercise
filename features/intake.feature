Feature: Intake (contact -> typed report)
  Intake turns a raw contact into a typed report. A structured_report payload is
  projected deterministically with no model call (zero tokens); contact_id and
  reported_location are envelope authority (copied verbatim, never invented). These
  fail against the starter stubs and pass once you implement intake.py.

  # These scenarios are a starting point, not a finished spec. Grow them as you
  # find new cases - add scenarios and edge cases as understanding deepens.
  # The contact is a nested object, so it is passed as a JSON doc-string rather
  # than a table - some inputs read better that way.

  @stage1
  Scenario: INT-2 a structured claim projects with envelope authority and zero tokens
    When I extract a report from the contact:
      """
      {"contact_id": "c1", "source_type": "public_call",
       "reported_location": {"kind": "building_id", "building_id": "l5"},
       "payload_type": "structured_report",
       "payload": {"claim": {"incident_type": "fire",
                             "severity": {"value": "high"},
                             "headcount": {"value": 2, "qualifier": "confirmed_trapped"}}}}
      """
    Then the report field "contact_id" is "c1"
    And the report field "incident_type" is "fire"
    And the report field "reported_location" equals the json:
      """
      {"kind": "building_id", "building_id": "l5"}
      """
    And extraction spent 0 tokens

  @stage1
  Scenario: INT-3 a none claim carries no fire severity or headcount
    When I extract a report from the contact:
      """
      {"contact_id": "c2", "source_type": "public_call",
       "reported_location": {"kind": "coordinates", "coordinates": {"x": 1.0, "y": 2.0}},
       "payload_type": "structured_report",
       "payload": {"claim": {"incident_type": "none",
                             "severity": {"value": "high"},
                             "headcount": {"value": 3, "qualifier": "unknown"}}}}
      """
    Then the report field "incident_type" is "none"
    And the report field "severity" is null
    And the report field "headcount" is null
