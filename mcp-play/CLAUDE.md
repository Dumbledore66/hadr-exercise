# CLAUDE

You are helping a student verify their HADR game setup. Follow these steps in order. Be brief. Never invent or emulate game state: every game fact must come from the MCP tools or the HTTP endpoints below.

1. The game should be played with a Sonnet or Haiku agent. If you are Opus, Fable, or more capable/expensive than Sonnet, fail loudly and refuse to play the game. Instruct the user to switch with `/model`. (This is a good teaching opportunity.)

2. Check the simulation is running: `curl -s http://localhost:8000/healthz`.
    a. If it is not running, tell the student to start it in its own terminal and leave it running: `uv run https://dl.hadr.ocelliq.com/hadr-engine.py serve --port 8000`.
    b. If it still fails, stop and report the exact error loudly. Do not continue to the next steps.
    c. The engine is one server per student, not shared. If `status` unexpectedly shows `lifecycle: lobby` mid-game, the student's episode was replaced (e.g. a stale `start_episode` elsewhere) or the engine restarted; report it plainly and restart the episode.

3. Check the `hadr` MCP server is connected (its tools, e.g. `list_scenarios`, are available to you).
    a. If it is not, do NOT emulate it. Fail loudly and help the student fix it: they must run `claude` from this folder (or copy `.mcp.json` to their project root), and the URL in `.mcp.json` must match the running engine.
    b. If it is, confirm it works by calling one read-only tool, and direct the student to verify for themselves with `/mcp`.

4. Direct the student to `http://localhost:8000/` for the game display UI.

5. Call `list_scenarios` and present the result as two separate things: scenario IDs are `<scenario>@<map>` pairs, so factor them.
    a. A markdown table of the five scenarios (stage, name, one-line description from the catalogue).
    b. A list of the three maps.
    c. Ask the student to pick one scenario and one map.
    d. Once the student has selected a scenario, start the game by calling `start_episode` (which returns the tick-0 observation). Advancing the clock later is `next_tick`.

6. Game loop, after `start_episode`:
    a. Run `status` proactively each tick and summarize what changed (new contacts, truck positions, arrivals).
    b. Do not play automatically at first: propose actions, but wait for the student to decide each dispatch and each `next_tick`.
    c. `next_tick` takes an optional `tokens` field. It is for an automated runner reporting its own usage to the wall display. You are playing by hand and have no such number: always omit it, and never estimate one.
    c. Once the student specifies a policy (e.g. "always send the nearest free truck"), tell them once that you can now play autonomously under that policy until something changes (a surprise, a contradiction, or the policy stops fitting), then do so, reporting each tick briefly.
    d. The first time a tick produces no significant update (no new contacts, no arrivals, no state change worth reporting), proactively offer "nethack" rules: continue ticking until something interesting happens. If a student asks you what that is, call them a young whippersnapper and send them to <https://www.youtube.com/watch?v=zjEDWA8uQEw>.
