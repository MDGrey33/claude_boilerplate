# Under-the-hood protocol — verifying Claude Code behavior against open source

This is the claude-expert skill's playbook for verifying claims about how Claude Code works when the public docs are thin, ambiguous, or silent. It uses **only open, publicly available sources**: the official Anthropic SDK repos, an open community Python reimplementation of Claude Code, and live-session reproduction. There is no private or leaked source involved at any step.

## Sources of truth (in escalation order)

| Tier | Source | What it is | What it's good for |
|------|--------|-----------|--------------------|
| 1 | [code.claude.com/docs](https://code.claude.com/docs) | Official documentation | The default answer. `surfaces/*.md` in this skill already distill it. |
| 2 | Official SDK repos (`anthropics/claude-agent-sdk-python`, `anthropics/claude-agent-sdk-typescript`) | Live, versioned, open-source SDKs | Authoritative for SDK-side behavior — agents, tools, hooks, MCP wiring, streaming. |
| 3 | Open community Python reimplementation (discovered as `$PYTHON_PORT`) | A readable Python port of Claude Code's core loop | A pedagogical, inspectable second opinion when docs are silent on internals (compaction triggers, context packing, tool dispatch, memory hierarchy). A **community approximation** — not the shipped CLI. |
| 4 | Live-session reproduction | The actually-installed CLI, reproduced in a scratch session | The ground truth for *current shipped behavior* — bug behavior, exact thresholds, version-specific quirks. |

All four are open. **Never consult or cite any private, internal, or leaked copy of the Claude Code CLI source.** If you only have a question about behavior, the four tiers above are sufficient and authoritative.

## The protocol

Escalate in order. Stop as soon as you have a confident, citable answer.

1. **Docs first.** Always start at [code.claude.com/docs](https://code.claude.com/docs). The `surfaces/*.md` files in this skill summarize the docs by surface (skills, hooks, agents, MCP, settings, etc.). Most questions end here.

2. **Check for a "docs unclear" flag.** Any claim in `surfaces/*.md` tagged "(docs unclear — verify before relying on this)" is an explicit signal to escalate.

3. **Consult the official SDK repos** for anything SDK-shaped — programmatic agents, custom tools, in-process MCP, hooks-as-code, the query loop, streaming. These repos are live and versioned, so they reflect current intent:
   - `anthropics/claude-agent-sdk-python` (package `claude-agent-sdk`)
   - `anthropics/claude-agent-sdk-typescript` (package `@anthropic-ai/claude-agent-sdk`)

   Fetch a specific file with `WebFetch` against `https://github.com/anthropics/<repo>/blob/main/<path>`, or clone for deep greps.

4. **Consult the discovered local Python port** for internal CLI mechanics the SDK doesn't expose and the docs don't spell out — auto-compaction triggers, context-window packing, the CLAUDE.md/memory hierarchy, tool registration order. Resolve its location from discovery (`discover-setup.sh` → `PYTHON_PORT`), never a hardcoded path. Treat it as a clean, readable approximation, not as production behavior.

5. **Reproduce in a live session** when what matters is the *current shipped* CLI — exact thresholds, a bug repro, a version-specific quirk. The snapshots in tier 3 can drift from what's actually installed; a live repro cannot.

6. **Cite the finding, distinctly.** Annotate every fact by its tier so a reader can tell docs from code from repro:

   ```
   Source (official docs):  https://code.claude.com/docs/...
   Source (SDK repo):       anthropics/claude-agent-sdk-python — src/.../hooks.py
   Source (Python port):    $PYTHON_PORT/compaction.py  (community reimplementation — may diverge from shipped CLI)
   Source (live repro):     reproduced in a scratch session on <version>
   ```

   Never present a code- or port-derived fact as if it came from official docs, and always mark the Python port as a community approximation.

## Discovering the local Python port

`discover-setup.sh` reports the port under the key `PYTHON_PORT`. It searches `~/code` and `$CLAUDE_PYTHON_PORT` for a local clone of the open community Python reimplementation (directory names like `nano-claude-code` / `cheetahclaws`).

- **Found** → `PYTHON_PORT=/path/to/clone`. Use `$PYTHON_PORT` in every reference below; never hardcode a path.
- **Not found** → discovery reports `PYTHON_PORT=not found`. To enable tier-4 under-the-hood verification, clone the open SafeRL-Lab Python reimplementation of Claude Code:

  ```bash
  git clone https://github.com/SafeRL-Lab/cheetahclaws "$HOME/code/cheetahclaws"   # formerly nano-claude-code
  # then re-run discover-setup.sh, or export CLAUDE_PYTHON_PORT=$HOME/code/cheetahclaws
  ```

  This is an open, community-maintained reimplementation (also branded *CheetahClaws*) — a readable Python rebuild of Claude Code's core loop with multi-provider support. It is independent of Anthropic and is *not* the shipped CLI; use it as a pedagogical reference, not a behavioral guarantee.

## Python port — typical layout

The open port is usually **flat** (file names vary by version; grep to confirm before relying on any one):

| File | Covers |
|------|--------|
| `agent.py` | Main agent loop — message format, tool dispatch |
| `subagent.py` | Subagent spawn, context isolation |
| `skills.py` | Skill loader |
| `tools.py` / `tool_registry.py` | Tool registration and dispatch |
| `memory.py` | Memory files, CLAUDE.md hierarchy |
| `context.py` | Context-window management / packing |
| `compaction.py` | Auto-compaction logic — useful when docs are silent on exact triggers |
| `providers.py` | Model provider routing |
| `config.py` | Settings loader |
| `nano_claude.py` (entry point) | REPL, slash commands, rendering |
| `tests/` | Unit tests — often the clearest spec |
| `docs/` | The port's own docs |

## Search cookbook

Delegate deep greps to a subagent (the `Explore` agent if available) to protect main context — these trees can be large. Resolve `$PYTHON_PORT` from discovery first; the SDK examples fetch from GitHub directly.

| Question | Where | How |
|----------|-------|-----|
| Programmatic hook contract | SDK repo | `WebFetch https://github.com/anthropics/claude-agent-sdk-python/blob/main/...` for the hooks module |
| Custom in-process MCP tool shape | SDK repo | Browse `anthropics/claude-agent-sdk-typescript` examples/tests |
| Auto-compaction trigger threshold | Python port | `Grep(pattern="compact", path="$PYTHON_PORT/compaction.py", output_mode="content")` |
| CLAUDE.md / memory hierarchy resolution | Python port | `Grep(pattern="CLAUDE.md\|memory", path="$PYTHON_PORT/memory.py", output_mode="content")` |
| Tool registration / dispatch order | Python port | `Read("$PYTHON_PORT/tool_registry.py")` |
| Context-window packing | Python port | `Read("$PYTHON_PORT/context.py")` |
| Exact shipped threshold / bug repro | Live repro | Reproduce in a scratch session; cite the version |

## When NOT to go under the hood

- **Stable, well-documented surfaces** (permissions syntax, basic skill structure, MCP add commands) — the docs are sufficient. Tier 1 only.
- **Current shipped-CLI bug behavior** — the Python port is a community snapshot and the SDK repos are SDK-side; neither guarantees what the installed CLI does today. Prefer a live repro (tier 4).
- **SDK behavior** — go straight to the official SDK repos (tier 2); don't infer SDK behavior from the CLI-shaped Python port.
- **Anything you can answer confidently from docs** — escalating adds cost and risks citing an approximation as fact. Escalate only on a real "docs unclear" flag.

## Cross-references

- Skill entry point: `claude-expert/SKILL.md`
- Surface summaries: `claude-expert/surfaces/*.md`
- Patterns: `claude-expert/patterns.md`
- Pitfalls: `claude-expert/pitfalls.md`
- Discovery script: `claude-expert/discover-setup.sh` (reports `PYTHON_PORT`, `STAGING_DIR`, and the rest of the environment map)
