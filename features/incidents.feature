@warmup
Feature: Incident store (mutable beliefs)
  Incidents are the agent's revisable beliefs about suspected fires. Unlike
  reports they are updated as evidence accrues: open, update belief fields, link
  supporting reports, close with a reason. find returns open incidents nearest
  first. @warmup: these fail against the starter stubs and pass once you implement
  stores/incidents.py.

  # These scenarios are a starting point, not a finished spec. Grow them as you
  # find new cases - add scenarios, columns, and edge cases as understanding deepens.

  Scenario: STORE-I1 open creates an incident with status open and the fields passed
    Given an empty incident store
    And these incidents are opened:
      | incident_type | x     | y     | tick | severity |
      | fire          | 100.0 | 100.0 | 1    | high     |
    When I get incident "inc-1"
    Then the incident's status is open
    And the incident's severity is high

  Scenario: STORE-I2 find returns fire incidents nearest-first, filtered by type
    Given an empty incident store
    And these incidents are opened:
      | incident_type | x    | y   | tick |
      | fire          | 0.0  | 0.0 | 1    |
      | fire          | 30.0 | 0.0 | 1    |
      | unknown       | 35.0 | 0.0 | 1    |
    When I find incidents with:
      | near        | radius | incident_type | status |
      | (31.0, 0.0) | 100.0  | fire          |        |
    Then the result ids are: inc-2, inc-1

  Scenario: STORE-I3 update changes belief fields and advances updated_tick
    Given an empty incident store
    And these incidents are opened:
      | incident_type | x   | y   | tick |
      | fire          | 0.0 | 0.0 | 1    |
    When I update incident "inc-1" at tick 2:
      | severity |
      | medium   |
    Then incident "inc-1" has severity = medium
    And incident "inc-1" has updated_tick = 2

  Scenario: STORE-I4 link is idempotent (no duplicate report ids)
    Given an empty incident store
    And these incidents are opened:
      | incident_type | x   | y   | tick |
      | fire          | 0.0 | 0.0 | 1    |
    And report "r1" is linked to incident "inc-1"
    And report "r1" is linked to incident "inc-1"
    When I get incident "inc-1"
    Then the incident's report ids are: r1

  Scenario: STORE-I5 close removes an incident from find(status=open)
    Given an empty incident store
    And these incidents are opened:
      | incident_type | x   | y   | tick |
      | fire          | 0.0 | 0.0 | 1    |
    And incident "inc-1" is closed as "resolved-by-vision" at tick 3
    When I find incidents with:
      | near | radius | incident_type | status |
      |      |        |               | open   |
    Then the result is empty
    And incident "inc-1" has status = closed

  Scenario: STORE-I6 find with status=any returns closed incidents too
    Given an empty incident store
    And these incidents are opened:
      | incident_type | x   | y   | tick |
      | fire          | 0.0 | 0.0 | 1    |
    And incident "inc-1" is closed as "resolved-by-vision" at tick 3
    When I find incidents with:
      | near | radius | incident_type | status |
      |      |        |               | any    |
    Then the result count is 1
