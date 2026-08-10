@stage1
Feature: Dispatch configuration (filed-incident enforcement)
  The engine logs and echoes incident_id without checking it names a real
  incident; the check in dispatch._run_tool is the only enforcement, and these
  scenarios pin it through run_dispatch end to end against a scripted model.
  Needs the warm-up incident store, _state_message, and the agent loop built.

  Background:
    Given an incident store with one open fire "inc-1" at (10.0, 20.0)

  Scenario: DISP-1 a dispatch to a filed incident is recorded
    Given the scripted model dispatches "truck-1" to "inc-1", then yields
    When the dispatch runs
    Then the dispatch of "truck-1" to "inc-1" was recorded

  Scenario: DISP-2 a dispatch to an unfiled incident is rejected and not recorded
    Given the scripted model dispatches "truck-1" to "inc-99", then yields
    When the dispatch runs
    Then no dispatches were recorded
    And a tool result contains an error mentioning "inc-99"

  Scenario: DISP-3 closing via file_incident_update records a close_reason
    Given the scripted model closes "inc-1" with note "put out by truck-1", then yields
    When the dispatch runs
    Then incident "inc-1" is closed with reason "put out by truck-1"
