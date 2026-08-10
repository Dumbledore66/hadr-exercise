"""Step definitions for agent_loop.feature (LOOP-*). A scripted fake OpenAI
client replays canned model turns and records every request; a recording
run_tool serves the tools. Messages the loop builds may be dicts (as
documented) or SDK-style objects - `_get` reads both.
"""

import asyncio
import json
import re
from types import SimpleNamespace

from behave import given, then, when

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)

TOOL_DEFS = [
    {
        "type": "function",
        "function": {
            "name": "travel_time",
            "description": "toy",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    }
]


def _usage():
    return SimpleNamespace(
        prompt_tokens=10, completion_tokens=5, prompt_tokens_details=None
    )


def _turn(content, tool_calls=None):
    msg = SimpleNamespace(content=content, tool_calls=tool_calls)
    return SimpleNamespace(choices=[SimpleNamespace(message=msg)], usage=_usage())


def _call(call_id, name, args):
    return SimpleNamespace(
        id=call_id,
        type="function",
        function=SimpleNamespace(name=name, arguments=json.dumps(args)),
    )


def _get(m, key, default=None):
    return m.get(key, default) if isinstance(m, dict) else getattr(m, key, default)


class ScriptedClient:
    """Replays turns in order; repeats the last one forever (LOOP-5)."""

    def __init__(self, turns):
        self.turns = turns
        self.requests = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        # Snapshot messages: the loop mutates its list between rounds.
        kwargs["messages"] = list(kwargs.get("messages", []))
        self.requests.append(kwargs)
        return self.turns[min(len(self.requests) - 1, len(self.turns) - 1)]


@given('a scripted agent with system "{system}" and task "{task}"')
def step_agent(context, system, task):
    context.system, context.task = system, task
    context.calls = []
    context.error_tool = None


@given('the scripted model yields with content "{text}"')
def step_yield(context, text):
    context.script = [_turn(text)]


@given('the scripted model calls tool "{name}", then yields')
def step_call_then_yield(context, name):
    context.script = [
        _turn("<think>choosing</think>", [_call("call-1", name, {})]),
        _turn("done"),
    ]


@given('the scripted model always calls tool "{name}"')
def step_always_call(context, name):
    context.script = [_turn("<think>looping</think>", [_call("call-1", name, {})])]


@given('tool "{name}" returns an error')
def step_tool_errors(context, name):
    context.error_tool = name


def _run(context, **kwargs):
    async def run_tool(name, args):
        context.calls.append((name, args))
        if name == context.error_tool:
            return {"error": f"{name} failed"}
        return {"eta_ticks": 3}

    context.client = ScriptedClient(context.script)
    context.result = asyncio.run(
        context.agent.agent_loop(
            client=context.client,
            model="scripted",
            system=context.system,
            user=context.task,
            tool_defs=TOOL_DEFS,
            run_tool=run_tool,
            max_rounds=kwargs.get("max_rounds", 6),
            max_tokens=900,
        )
    )


@when("the agent loop runs")
def step_run(context):
    _run(context)


@when("the agent loop runs with max_rounds {n:d}")
def step_run_capped(context, n):
    _run(context, max_rounds=n)


@then("the loop ran {n:d} rounds")
def step_rounds(context, n):
    assert context.result.rounds == n, context.result.rounds
    assert len(context.client.requests) == n, len(context.client.requests)


@then("no tools were called")
def step_no_tools(context):
    assert context.calls == [], context.calls


@then('tool "{name}" was called')
def step_tool_called(context, name):
    assert name in [c[0] for c in context.calls], context.calls


@then('the final message is "{text}"')
def step_final(context, text):
    # Accept phase-1 (raw, <think> kept) and the full loop (stripped on yield):
    # strip any think block from the actual, then require an exact match.
    got = _THINK_RE.sub("", context.result.final).strip()
    assert got == text, repr(context.result.final)


@then("the first request begins with the system prompt and the task")
def step_first_request(context):
    messages = context.client.requests[0]["messages"]
    assert _get(messages[0], "role") == "system", messages[0]
    assert _get(messages[0], "content") == context.system, messages[0]
    assert _get(messages[1], "role") == "user", messages[1]
    assert _get(messages[1], "content") == context.task, messages[1]


@then("every tool call got exactly one tool result with a matching tool_call_id")
def step_tool_ids_match(context):
    messages = context.client.requests[-1]["messages"]
    issued = [
        _get(tc, "id")
        for m in messages
        if _get(m, "role") == "assistant"
        for tc in (_get(m, "tool_calls") or [])
    ]
    answered = [_get(m, "tool_call_id") for m in messages if _get(m, "role") == "tool"]
    assert issued and sorted(issued) == sorted(answered), (issued, answered)


@then(
    "the second request replays the first assistant turn verbatim, think block included"
)
def step_verbatim(context):
    sent = context.script[0].choices[0].message
    assistants = [
        m
        for m in context.client.requests[1]["messages"]
        if _get(m, "role") == "assistant"
    ]
    assert assistants, "no assistant turn fed back"
    a = assistants[0]
    assert _get(a, "content") == sent.content, _get(a, "content")
    got = [
        (
            _get(tc, "id"),
            _get(_get(tc, "function"), "name"),
            _get(_get(tc, "function"), "arguments"),
        )
        for tc in (_get(a, "tool_calls") or [])
    ]
    want = [(tc.id, tc.function.name, tc.function.arguments) for tc in sent.tool_calls]
    assert got == want, (got, want)


@then('a tool result contains an error mentioning "{text}"')
def step_tool_error(context, text):
    contents = [
        _get(m, "content")
        for m in context.client.requests[-1]["messages"]
        if _get(m, "role") == "tool"
    ]
    assert any("error" in c and text in c for c in contents), contents
