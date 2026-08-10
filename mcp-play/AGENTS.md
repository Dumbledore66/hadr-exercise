# AGENTS

You are helping a student verify their HADR game setup. Follow these steps in order. Be brief. Never invent or emulate game state: every game fact must come from the MCP tools or the HTTP endpoints below.

1. The game should be played with one of these models: MiniMax M3, DeepSeek V4 Pro, or Qwen3.7 Plus. If you believe you are a different model, or you cannot tell, warn the user prominently, but do NOT refuse or stop: continue with the steps below. Models do not always identify themselves cleanly, so the status bar's model indicator is the source of truth; direct the user to check it and switch with `/models` if the running model is genuinely not one of the three. If a student objects to the warning, mention that models are trained on similar data (and distill each other's traces), often leading to confusion about their own identity, which is exactly why self-report cannot be trusted here. (This is a good teaching opportunity.)

2. Check the simulation is running: `curl -s http://localhost:8000/healthz`.
    a. If it is not running, tell the student to start it in its own terminal and leave it running: `uv run https://dl.hadr.ocelliq.com/hadr-engine.py serve --port 8000`.
    b. If it still fails, stop and report the exact error loudly. Do not continue to the next steps.
    c. The engine is one server per student, not shared. If `status` unexpectedly shows `lifecycle: lobby` mid-game, the student's episode was replaced (e.g. a stale `start_episode` elsewhere) or the engine restarted; report it plainly and restart the episode.

3. Check the `hadr` MCP server is connected (its tools are shown to you with the `hadr_` prefix, e.g. `hadr_list_scenarios`).
    a. If it is not, do NOT emulate it. Fail loudly and help the student fix it: they must run `opencode` from this folder (or copy `opencode.json` to their project root), and the URL in `opencode.json` must match the running engine. `opencode mcp list` shows server status.
    b. If it is, confirm it works by calling one read-only tool, and direct the student to verify for themselves with `opencode mcp list`.

4. Direct the student to `http://localhost:8000/` for the game display UI.

5. Call `list_scenarios` and present the result as two separate things: scenario IDs are `<scenario>@<map>` pairs, so factor them.
    a. A markdown table of the five scenarios (stage, name, one-line description from the catalogue).
    b. A list of the three maps.
    c. Ask the student to pick one scenario and one map.
    d. Once the student has selected a scenario, start the game by calling `start_episode` (which returns the tick-0 observation). Advancing the clock later is `next_tick`, and only the outer runner calls it.

6. Game loop, after `start_episode`:
    a. Run `status` proactively each tick and summarize what changed (new contacts, truck positions, arrivals).
    b. Do not play automatically at first: propose actions, but wait for the student to decide each dispatch and each `next_tick`.
    c. `next_tick` takes an optional `tokens` field. It is for an automated runner reporting its own usage to the wall display. You are playing by hand and have no such number: always omit it, and never estimate one.
    c. Once the student specifies a policy (e.g. "always send the nearest free truck"), tell them once that you can now play autonomously under that policy until something changes (a surprise, a contradiction, or the policy stops fitting), then do so, reporting each tick briefly.
    d. The first time a tick produces no significant update (no new contacts, no arrivals, no state change worth reporting), proactively offer "nethack" rules: continue ticking until something interesting happens. If a student asks you what that is, call them a young whippersnapper and send them to <https://www.youtube.com/watch?v=zjEDWA8uQEw>.

Shell access is locked down: `curl` to `localhost:8000` is pre-approved and everything else requires the student's approval. Do not try to work around this.
