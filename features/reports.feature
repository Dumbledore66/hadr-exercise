@warmup
Feature: Report store (append-only evidence)
  The report store keeps one immutable row per contact. Re-adding a contact_id is
  ignored (there is no update, no delete), and find_reports selects evidence by a
  spatial radius and a tick window. @warmup: these fail against the starter stubs
  and pass once you implement stores/reports.py.

  # These scenarios are a starting point, not a finished spec. Grow them as you
  # find new cases - add scenarios, columns, and edge cases as understanding deepens.

  # Step-def gotcha: a step that owns a data table keeps its trailing ":" as part
  # of the literal text behave matches. The matcher must include it too -
  # @given("a report is added:"), not "a report is added". Omit it and behave
  # reports the step as "undefined", not failed.

  Scenario: STORE-R1 a report round-trips and the store counts one row
    Given an empty report store
    And a report is added:
      | contact_id | incident_type | x   | y   | tick |
      | c1         | fire          | 0.0 | 0.0 | 1    |
    When I get report "c1"
    Then the report's incident_type is "fire"
    And the store holds 1 report

  Scenario: STORE-R2 re-adding a contact_id is ignored (append-only)
    Given an empty report store
    And a report is added:
      | contact_id | incident_type | x   | y   | tick |
      | c1         | fire          | 0.0 | 0.0 | 1    |
    When I add a report:
      | contact_id | incident_type | x   | y   | tick |
      | c1         | none          | 9.0 | 9.0 | 2    |
    Then the store holds 1 report
    And report "c1" has incident_type "fire"

  Scenario: STORE-R3 find_reports filters by radius
    Given an empty report store
    And reports are added:
      | contact_id | incident_type | x     | y     | tick |
      | near       | fire          | 10.0  | 10.0  | 5    |
      | far        | fire          | 500.0 | 500.0 | 5    |
    When I find_reports with:
      | near       | radius | start | end |
      | (0.0, 0.0) | 50.0   |       |     |
    Then the result ids are: near

  Scenario: STORE-R4 find_reports filters by tick window
    Given an empty report store
    And reports are added:
      | contact_id | incident_type | x     | y     | tick |
      | near       | fire          | 10.0  | 10.0  | 5    |
      | far        | fire          | 500.0 | 500.0 | 5    |
      | late       | fire          | 400.0 | 400.0 | 40   |
    When I find_reports with:
      | near | radius | start | end |
      |      |        | 0     | 10  |
    Then the result ids are: near, far

  Scenario: STORE-R5 radius and tick window apply together
    Given an empty report store
    And reports are added:
      | contact_id | incident_type | x     | y     | tick |
      | near       | fire          | 10.0  | 10.0  | 5    |
      | far        | fire          | 500.0 | 500.0 | 5    |
      | late       | fire          | 400.0 | 400.0 | 40   |
    When I find_reports with:
      | near       | radius | start | end |
      | (0.0, 0.0) | 50.0   | 0     | 10  |
    Then the result ids are: near
