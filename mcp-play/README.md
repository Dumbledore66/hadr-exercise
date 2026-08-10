# MCP connection to the HADR engine

This folder holds two equivalent runner setups for the engine's MCP Streamable HTTP endpoint (default `http://localhost:8000/mcp`; edit the URL for a hosted engine): one for Claude Code, one for OpenCode.

## Claude Code

`.mcp.json` connects Claude Code to the engine.

- Run `claude` from this folder; it picks up the project-scoped `.mcp.json`.
- Or copy `.mcp.json` into your own project root.

Equivalent one-liner without the file: `claude mcp add --transport http hadr http://localhost:8000/mcp`.

The Claude runbook is `CLAUDE.md`; `.claude/settings.json` pins the model and allowlists the game tools.

## OpenCode

`opencode.json` connects OpenCode to the same endpoint.

- Run `opencode` from this folder; it picks up the project `opencode.json`.
- Or copy `opencode.json` into your own project root.

Equivalent one-liner without the file: `opencode mcp add hadr --url http://localhost:8000/mcp`.

The OpenCode runbook is `AGENTS.md`. When both exist, OpenCode reads `AGENTS.md` and Claude Code reads `CLAUDE.md`; keep the two in sync.

Model gate: the game should be played with MiniMax M3, DeepSeek V4 Pro, or Qwen3.7 Plus. `opencode.json` pins `opencode-go/minimax-m3` as the default; switch with `/models`. All three models are available on the `opencode-go` provider (add credentials with `opencode auth login`); models.dev lists other providers that carry them. A mismatched model earns a prominent warning, not a refusal: models don't always identify themselves cleanly, so the status bar's model indicator is the source of truth.

Permissions: only the `hadr_*` MCP tools and `curl` to `localhost:8000` run without approval; every other action asks first, and `curl` to anywhere else is denied.

## Either way

The engine grants control to the most recent MCP session (newest wins), so connecting takes over from any other connected client.
