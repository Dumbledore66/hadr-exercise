@stage3
Feature: Reconciliation (report + vision -> incident beliefs)
  Reconciliation folds each new report into the incident store: open a new
  incident, link/update an existing one, flag a contradiction, or ignore a denial.
  Truck vision is ground truth: a building seen normal closes a co-located
  incident, burning confirms or opens one. @stage3: these fail against the starter
  stubs and pass once you implement reconcile.py (and grow the Report/Incident
  schema the belief fields need).

  # These scenarios are a starting point, not a finished spec. Grow them as you
  # find new cases - add scenarios, columns, and edge cases as understanding deepens.

  Background:
    Given a fresh reconcile world

  Scenario: REC-1 a lone fire report opens a new incident
    When these reports are reconciled at tick 1:
      | contact_id | incident_type | x   | y   | tick |
      | c1         | fire          | 0.0 | 0.0 | 1    |
    Then the action is open
    And there is 1 open incident

  Scenario: REC-2 a nearby higher-severity fire merges and escalates
    Given these reports are reconciled at tick 1:
      | contact_id | incident_type | x   | y   | tick | severity |
      | c1         | fire          | 0.0 | 0.0 | 1    | low      |
    When these reports are reconciled at tick 2:
      | contact_id | incident_type | x   | y   | tick | severity |
      | c2         | fire          | 5.0 | 5.0 | 2    | high     |
    Then the action is one of: link-duplicate, update
    And there is 1 open incident
    And open incident 0 has severity = high
    And open incident 0 has report ids: c1, c2

  Scenario: REC-3 all-out vs confirmed-trapped flags a contradiction, keeps the cautious belief
    Given these reports are reconciled at tick 1:
      | contact_id | incident_type | x   | y   | tick | headcount | qualifier |
      | c1         | fire          | 0.0 | 0.0 | 1    | 0         | all_out   |
    When these reports are reconciled at tick 2:
      | contact_id | incident_type | x   | y   | tick | headcount | qualifier         |
      | c2         | fire          | 2.0 | 2.0 | 2    | 2         | confirmed_trapped |
    Then the action is contradiction-retain
    And open incident 0 has contradiction = true
    And open incident 0 has headcount = 2
    And open incident 0 has headcount_qualifier = confirmed_trapped

  Scenario: REC-4 a nearby denial keeps the incident open (uncertainty retained)
    Given these reports are reconciled at tick 1:
      | contact_id | incident_type | x   | y   | tick |
      | c1         | fire          | 0.0 | 0.0 | 1    |
    When these reports are reconciled at tick 2:
      | contact_id | incident_type | x   | y   | tick |
      | c2         | none          | 3.0 | 3.0 | 2    |
    Then the action is possible-false-alarm
    And there is 1 open incident

  Scenario: REC-5 a lone denial opens nothing
    When these reports are reconciled at tick 1:
      | contact_id | incident_type | x   | y   | tick |
      | c1         | none          | 0.0 | 0.0 | 1    |
    Then the action is ignored
    And there are 0 open incidents

  Scenario: REC-6 vision sees the building normal and closes the incident
    Given these reports are reconciled at tick 1:
      | contact_id | incident_type | x   | y   | tick |
      | c1         | fire          | 0.0 | 0.0 | 1    |
    When truck vision reports at tick 3:
      | building_id | status | x   | y   |
      | l1          | normal | 0.0 | 0.0 |
    Then the action is resolved-by-vision
    And there are 0 open incidents

  Scenario: REC-7 vision sees a building burning and opens a fire incident
    When truck vision reports at tick 2:
      | building_id | status  | x    | y    |
      | l9          | burning | 50.0 | 50.0 |
    Then the action is confirmed-by-vision
    And there is 1 open incident
    And open incident 0 has incident_type = fire

  Scenario: REC-8 a fire report upgrades an unknown belief in place
    Given these reports are reconciled at tick 1:
      | contact_id | incident_type | x   | y   | tick |
      | c1         | unknown       | 0.0 | 0.0 | 1    |
    When these reports are reconciled at tick 2:
      | contact_id | incident_type | x   | y   | tick |
      | c2         | fire          | 4.0 | 4.0 | 2    |
    Then there is 1 open incident
    And open incident 0 has incident_type = fire
