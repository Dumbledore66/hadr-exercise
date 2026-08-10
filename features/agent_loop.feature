@stage1
Feature: The agentic tool loop
  The loop you build in agent.agent_loop, run against a scripted fake model -
  fully deterministic, no live tokens, no engine, no dispatcher. The scripted
  client replays canned model turns and records every request; a recording
  run_tool serves the tool calls. @stage1: red until the loop exists.

  Background:
    Given a scripted agent with system "You are terse." and task "handle tick 1"

  Scenario: LOOP-1 no tool calls means yield: one round, final message captured, think optional
    Given the scripted model yields with content "<think>quiet tick</think>nothing to do"
    When the agent loop runs
    Then the loop ran 1 rounds
    And no tools were called
    And the final message is "nothing to do"
    And the first request begins with the system prompt and the task

  Scenario: LOOP-2 a tool call is executed and answered by tool_call_id
    Given the scripted model calls tool "travel_time", then yields
    When the agent loop runs
    Then the loop ran 2 rounds
    And tool "travel_time" was called
    And every tool call got exactly one tool result with a matching tool_call_id

  Scenario: LOOP-3 the assistant turn is fed back verbatim (cache invariant)
    Given the scripted model calls tool "travel_time", then yields
    When the agent loop runs
    Then the second request replays the first assistant turn verbatim, think block included

  Scenario: LOOP-4 a tool error is fed back to the model and the loop carries on
    Given tool "lookup" returns an error
    And the scripted model calls tool "lookup", then yields
    When the agent loop runs
    Then the loop ran 2 rounds
    And a tool result contains an error mentioning "lookup"

  Scenario: LOOP-5 a model that never yields stops at the round cap
    Given the scripted model always calls tool "travel_time"
    When the agent loop runs with max_rounds 3
    Then the loop ran 3 rounds
