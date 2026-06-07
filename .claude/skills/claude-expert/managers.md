# The manager registry — one specialist per artifact type

> Companion to [SKILL.md](SKILL.md). This file describes the **pattern**
> claude-expert curates — a single lifecycle "manager" skill per artifact
> **type** — and the artifact-type **taxonomy** that pattern is built on. SKILL.md
> carries the compact router table; this file carries the full taxonomy, the
> discovery step that tells you what YOUR setup actually has, and the
> cross-cutting rules.

claude-expert is the **router**; the intended shape of a mature setup is that each
artifact **type** has a dedicated **manager** skill owning its full lifecycle
(understand-the-neighborhood, prefer-the-reversible-move, calibrate-to-blast-radius).
claude-expert itself never edits — it picks the surface and hands off to whatever
manager owns that type.

**This registry is a taxonomy, not a shipped roster.** The boilerplate does not
install fourteen named manager skills for you. What it ships is (1) the artifact-type
taxonomy below, with a *conventional* manager name per type as an **example** of what
such a manager would be called and own, and (2) a discovery step
([discover-setup.sh](discover-setup.sh)) that inspects *your* environment and reports,
per type, whether you already have a manager for it and which types are **gaps**. Treat
every "Conventional manager skill" cell as a naming convention and a description of
scope — not a promise that the skill exists in your install.

## Populated by discovery — run this first

Before you rely on any row below, find out what your setup actually has:

```bash
bash .claude/skills/claude-expert/discover-setup.sh
```

`discover-setup.sh` is read-only introspection. It reads `$HOME/.claude/` and the
project `./.claude/` and emits a greppable `KEY=VALUE` map. For the manager registry it
reports, **per artifact type**, whether a managing skill is `PRESENT` or `ABSENT` —
detected two ways:

1. **By conventional name** — it checks for a skill matching the conventional manager
   name for that type (the example names in the table below: `skills-manager`,
   `agent-manager`, `hooks-manager`, `loops-manager`, `schedules-manager`,
   `plugins-manager`, `logs-manager`, `memory-hygiene`/`memory-manager`,
   `mcp-doctor`/`mcp-manager`, `update-config`, `keybindings-help`, `key-manager`, a
   files/substrate keeper, a cost/finance auditor, etc.).
2. **By description scan** — it scans every installed skill's `description` for the
   pattern `<type> … (lifecycle )?manager`, so a manager you named differently still
   matches on what it claims to own.

A type with neither match is reported as a **GAP** — a lifecycle the router currently
has nowhere to hand off to. The taxonomy is the menu; discovery tells you which dishes
are on your table and which are missing.

## Artifact-type taxonomy

Columns: the artifact **type**, the **conventional** manager skill name (an example —
adopt it or pick your own), what that manager **would own**, and the trigger phrasing
that should route to it. Conventions, not an installed roster — confirm presence with
`discover-setup.sh`.

| Artifact type | Conventional manager skill (example name) | What it would own | Trigger |
|:--|:--|:--|:--|
| **Skills** (`~/.claude/skills/*/SKILL.md`, project `./.claude/skills/`) | `skills-manager` | Add/update/consolidate/archive skills; non-redundancy; delegate external-catalog search to a skill-researcher | "add/update/remove/review/reorganize a skill" |
| **Subagents** (`~/.claude/agents/*.md`, project `./.claude/agents/`) | `agent-manager` | Agent `.md` lifecycle, frontmatter (tools/model/permissionMode/skills), delegation-description tuning, archive | "add/edit/review an agent", "new subagent" |
| **Hooks** (`settings.json` + plugin `hooks.json` + skill/agent frontmatter) | `hooks-manager` | Hook event/handler design + safety review; delegates the actual settings write to the settings manager | "add a hook", "run X every time", "block Y", "hook review" |
| **Loops** (`/loop`, session-scoped) | `loops-manager` | `/loop` usage, `loop.md`, registry of active session loops, 7-day-expiry watch | "set up a loop", "poll X", "/loop", "what loops are running" |
| **Schedules** (Routines + cron + durable scheduled tasks) | `schedules-manager` | `/schedule` Routines, durable local scheduled tasks, cron registry | "schedule X", "run nightly/weekly", "list my routines/cron jobs" |
| **Plugins** (`.claude-plugin/`, marketplaces) | `plugins-manager` | Plugin packaging, marketplace add/install, namespacing, token-cost review | "package this as a plugin", "install/build a plugin", "marketplace" |
| **Logs / telemetry** (operational log/telemetry streams) | `logs-manager` | Rotation + retention of append-only streams; the schema CONTRACT downstream skills mine | "rotate/prune logs", "this log is huge", "what writes/reads this log", "log retention" |
| **Memory** (`MEMORY.md`, auto-memory topic files) | `memory-hygiene` / `memory-manager` | Classify/prune/promote auto-memory entries | "memory hygiene", "clean/audit/promote memory" |
| **Secrets / credentials** (a single secrets store) | `key-manager` | Store/retrieve/rotate/audit secrets; wire keys into tools; never print/commit/log | "store a key", "rotate token", "wire credential", "audit secrets" |
| **MCP servers** (`.mcp.json`, `~/.mcp.json`, `~/.claude.json`) | `mcp-doctor` (health only — see gap below) / `mcp-manager` | MCP server health checks; (a full manager would add add/remove/scope) | "check MCP", "mcp health", "are my servers up" |
| **Settings / permissions** (`settings.json`) | `update-config` | Write settings.json, permission rules, env vars, hook wiring | "allow X", "add permission", "set env", "from now on when X" |
| **Keybindings** (`~/.claude/keybindings.json`) | `keybindings-help` | Rebind keys, chords | "rebind", "keybinding", "change submit key" |
| **Files / substrate** (working ↔ persistent tiers) | a files/substrate keeper (e.g. `record-keeper`) | Canonical file placement, ledger, archive/dedup | "where does this live", file handoffs |
| **Cost / context** (CLAUDE.md, skills, MCPs) | a cost/finance auditor (e.g. `finance-controller`) | Cost+context audit; reports, delegates execution | "audit cost", "sessions feel slow", "bills spiked" |
| **External catalogs** (online skill/prompt libraries) | a skill-researcher | Find external skill/agent/automation patterns; consulted by the skills manager | invoked by the skills manager, "what's out there for X" |

## Known gaps (the type-level watch-list)

These are observations about the *taxonomy* that hold regardless of which managers a
given setup has installed. Run `discover-setup.sh` to see which gaps are live in yours.

- **MCP server *lifecycle*** — the common MCP-management skill (`mcp-doctor` and its
  kin) typically only checks **health**. Adding/removing/scoping MCP servers (editing
  `.mcp.json` / `~/.mcp.json` / `~/.claude.json`, `claude mcp add --transport http …`)
  often has **no dedicated lifecycle manager**, and gets handled ad hoc via the settings
  manager (the settings side) plus a connector toggle. **Recommendation:** if MCP churn
  increases, either extend the health checker into a full `mcp-manager` or add one. Until
  then, route MCP add/remove through `claude-expert` → the settings manager, then verify
  with the health checker. *(HTTP transport is recommended; SSE is deprecated.)*
- **Slash commands** have no separate manager by design — they were **merged into
  skills**, so the skills manager owns them.
- **Statusline / output-styles / themes / env vars** are configured through the settings
  manager (or `/config` for simple toggles); no dedicated manager is warranted.

## Cross-cutting rules

These sharpen judgment, they aren't a checklist — see [reasoning.md](reasoning.md); when
a case doesn't fit, reason from the tradeoff.

1. **Check claude-expert for surface choice when the type is genuinely ambiguous** —
   confirm the artifact is the right surface (not a sibling) where it's a real call, not
   as a ritual for the obvious case.
2. **Managers that write settings delegate the write to the settings manager** — a hooks
   manager especially doesn't edit `settings.json` directly. (And a destructive guard
   that must survive bypass belongs in a PreToolUse deny hook, not a manager prompt.)
3. **Prefer the reversible move** (invariant 5) — managers archive retired artifacts to a
   dated `_archive/` path with a reason rather than deleting.
4. **Calibrate to reversibility + blast radius** (invariant 4) — act and report on
   low-risk reversible changes; confirm before irreversible or high-stakes ones;
   understand the neighborhood in proportion to the change (a one-line tweak needs no
   census; a new artifact or a consolidation does). Automation never silently rewrites a
   manager's decision logic.
5. **Recurring manager work is itself scheduled** via the schedules manager (e.g. logs
   rotation, the claude-expert freshness pass) — managers don't busy-loop.

## Context-cost note (honest tradeoff)

Each installed manager's `description` loads eagerly into the skill-listing budget (~1%
of the context window; per-skill description capped at 1,536 chars; least-invoked
descriptions drop first). A full set of managers adds real weight. If `/doctor` reports
listing overflow or sessions feel slow, that's a cost/context audit → trim the longest
manager descriptions (front-load the key trigger; truncation cuts from the back).

See [self-update.md](self-update.md) for how this taxonomy + the rest of claude-expert
stays current.
