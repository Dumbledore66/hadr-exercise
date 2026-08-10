# HADR dispatch starter

Student starter template for the HADR fire-dispatch course. The plumbing ships
working; the lessons ship as clearly marked holes you fill across Day 1 and Day 2.
The game API and rules live on the course site (the game API / walking-skeleton
pages); this README is the local map.

## Setup

```bash
uv sync
cp .env.example .env    # then edit; or create .env by hand
```

`.env` needs your OpenCode Go key (runtime model calls bill the Go subscription):

```
OPENAI_KEY=sk-...
```

An `INTAKE_` or `DISPATCH_` prefix overrides any `OPENAI_*` variable for that role
alone, so the two roles can sit on different endpoints; see `.env.example`.

The engine is a pinned wheel you run yourself, launched by the one-line command
on the course site's preflight page. Everything here talks to it over HTTP/MCP.

## Run the engine

In its own terminal, leave the engine serving:

```bash
uv run https://dl.hadr.ocelliq.com/hadr-engine.py serve --port 8000
```

The smoke test drives that engine on `http://127.0.0.1:8000/mcp`; point it
elsewhere with `HADR_ENGINE_URL`, and it skips when no engine is serving.

## Play by hand

`mcp-play/` holds ready-made configs and runbooks that point an agent CLI at the
running engine so you can play the game yourself before automating it; see
`mcp-play/README.md`.

## Run the agent

```bash
# play one episode against the engine on port 8000 (the default --server)
uv run hadr-runner stage1-basic@londone

# --no-llm skips the dispatch model (plumbing check); --seed pins the scenario
uv run hadr-runner stage1-basic@londone --no-llm --seed 777

# an engine elsewhere: --server overrides the default MCP endpoint
uv run hadr-runner stage1-basic@londone --server http://127.0.0.1:9000/mcp
```

The runner prints the terminal outcome (casualties, buildings lost) and
provider-reported token totals by role. Out of the box the inner loop is
empty, so the shell ticks cleanly to terminal while saving nobody - that is the
provable skeleton you build on.

## Where the holes are

Plumbing ships working; these are the lessons you implement.

| File | Hole | Stage |
| --- | --- | --- |
| `stores/reports.py`, `stores/incidents.py` | the store methods (dataclasses ship; contracts in the docstrings) | Day 1 warm-up |
| `runner._process_tick` | the inner loop: wire intake -> reconcile -> dispatch | stages 1-4 |
| `prompts/intake_system.md`, `intake.py` | prompt skeleton; `_finalize` (schema + envelope authority) | stages 1, 2 |
| `reconcile.py` | matching/decision logic + thresholds (decision table in the docstrings) | stage 3 |
| `prompts/dispatch_system.md`, `dispatch._state_message` | prompt skeleton; the coverage/priority state message | stages 1, 4 |

Ships working, do not rebuild: `engine_client.py` (MCP transport), the runner
shell (session, tick loop, single `next_tick`, token totals), the shared LLM
plumbing in `util.py`, the bounded dispatch tool loop, and typed sensor
passthrough.

## Requirements and the warm-up workflow

Requirements arrive as executable Gherkin under `features/` (`reports`,
`incidents`, `reconcile`, `intake`; scenario IDs `STORE-R*`, `STORE-I*`, `REC-*`,
`INT-*` in the scenario titles). Each `.feature` is the spec; `features/steps/`
holds the step definitions and `features/environment.py` the setup - read all
three and you have seen the whole test machine, no interpreter. Each store
method's docstring states its contract and edge cases.

Each hole is tagged by its stage: `@warmup` (the store warm-up), `@stage1` (the
agent loop, dispatch, and the `_finalize` gate the zero-token claim path runs
through), `@stage2` (the intake prompt - you write those scenarios), `@stage3`
(reconcile). Tags sit on scenarios, not features, so one file can span stages.
There is no default exclusion, so a fresh clone runs every scenario and fails -
the requirements are failing tests you turn green.
Select a stage to work on, and gate only the built stages in CI (see the course's
Backpressure Engineering section).

```bash
uv run behave                          # every scenario - RED until you build the holes
uv run behave --tags=@warmup           # the store warm-up (reports + incidents)
```

Failing until implemented is the intended state. The scenarios shipped are a
starting point - grow them as you discover new cases. Your PRs reference the
scenario IDs they satisfy.

Step-def gotcha: a step that owns a data table keeps its trailing `:` as part of
the text behave matches, so the matcher must include it - `@given("a report is
added:")`, not `"a report is added"`. Omit the colon and behave reports the step
as *undefined* rather than failed.

```bash
uv run pytest                     # plumbing + smoke (GREEN out of the box, no holes)
```

`tests/test_runner_smoke.py` spawns a real engine and drives the runner shell end
to end (no models, no key). It is skipped automatically if the engine is not found.

## Evals

Model quality is measured separately from the pytest scenarios, because it spends
real tokens and is not deterministic. Intake extraction is graded offline against
the labeled contact dump (`datasets/contacts_labeled.jsonl`, generated on Day 2
via `hadr-engine gen-datasets --include-labels`); episode outcomes are compared
to the greedy baseline. Build these eval
scripts as the course site's Day-2 rubric directs; keep them out of the default
pytest run.
