# Boilerplate v2 — Design Principles

**Status:** Drafted 2026-05-05 from the v2 redesign discussion. Read this for the *what* and *why* of the v2 architecture.

## Setup

- A user installs the boilerplate into a folder of their choice (their *workspace*): `~/`, `~/my-space`, `~/workspace`, etc.
- The chosen folder hosts everything reusable: skills, agents, identity, brag log, MCP server configs, and the project registry.
- `/setup-workspace` handles initialisation and syncs upstream updates. It creates the bare-minimum scaffolding only; other folders are created on first use by the skills that need them.
- **Sibling layout:** the user clones the boilerplate source to a folder OUTSIDE the intended workspace (e.g., `~/src/claude_boilerplate/` as a sibling of `~/workspace/`). Source and workspace must never be nested. `/setup-workspace init` validates this and refuses if the layout is wrong. The sibling layout is what makes each setup self-contained against Claude Code's CLAUDE.md traversal-up behaviour.
- **Why sibling, not config-based isolation.** Claude Code traverses UP from cwd at session start, loading every `CLAUDE.md` it finds along the way (root-to-cwd order, no automatic stop). A `claudeMdExcludes` setting exists and can suppress specific parent files, but it requires each setup to enumerate the parent CLAUDE.mds it doesn't want — drift-prone, easy to forget, breaks when paths change. Sibling layout solves the same problem at the layout layer: if no parent path contains a CLAUDE.md, there's nothing to exclude. Decided 2026-05-09 after rejecting `claudeMdExcludes` as the primary mechanism. Reconsider only if multiple co-located setups become an unavoidable constraint.
- The workspace coexists with Claude Code's harness state at `~/.claude/` (auto-memory dirs, base settings). It complements `~/.claude/`, not replaces it.

## Working from the workspace

- The workspace is the canonical session root: identity, brag log, skills, agents, docs, the project registry, and workspace-level memory all live under it. The user runs Claude from any cwd under `<workspace>/` — most commonly the workspace root or a project subdirectory. Sessions started outside the workspace are out of scope; `/hello` refuses with a hint to cd into the workspace.
- Claude Code's harness walks up the directory tree at session start, loading every CLAUDE.md it finds and resolving skills from the workspace's `.claude/skills/`. The workspace does not have to be the literal cwd; it must be an ancestor of the cwd for the boilerplate to be available.
- **Active project context is logical state, not filesystem-driven.** `/hello` writes the active project (with workstream and open item) to the session marker; every other skill reads from the marker, not from cwd. `/hello` may use cwd at session start as a confirmation hint — e.g., suggesting a likely project when cwd is under `<workspace>/projects/<slug>/` — but the user always confirms; no skill, including /hello, derives the active project from cwd at any other moment.
- The **project registry** (`<workspace>/.claude/projects-index.json`) is an index file mapping human-readable slugs (e.g., `my-work`, `ehr-backend-core`) to project paths and metadata. The `/project-registry` skill owns mutations; other skills read it directly.
- `/hello` triggers inline registration of new projects via `/setup-workspace add-project` (full scaffold + registry write) — the user doesn't need to know either skill exists. `/project-registry add` alone only writes to the index; it doesn't scaffold the project's memory or session-marker dirs, so /hello can't use it directly.

## Projects

- Projects live under `<workspace>/projects/<slug>/` — physical dirs or symlinks; the boilerplate doesn't care which.
- The boilerplate treats every registered project **identically**. There's no `topic` vs `repo` switch in the runtime. "Topic" (personal cross-cutting work) and "repo" (team-shared codebase) are useful conceptual framings for users when deciding what to register, but the boilerplate doesn't model the distinction.
- Whether a project is committed to a git remote is a normal git workflow concern, separate from the registry. Per-engineer state (`workstreams/`, `sessions/`, `collected/`, `artifacts/`, `contributions/`) is gitignored regardless. Team-shared content (`CLAUDE.md`, `MEMORY.md`, `lessons-learned.md`, `docs/`, `settings.json`) is committed when the user wants it shared.
- All projects use the same layout. **Memory** lives under `.claude/memory/`: `MEMORY.md` (curated process knowledge, lessons promoted across sessions), `lessons-learned.md` (raw lessons, append-only), and `project-context.md` (domain knowledge — business problem, users, constraints, what "done" looks like). All three are scaffolded at registration. Process knowledge (MEMORY.md / lessons-learned.md) and domain knowledge (project-context.md) are deliberately separate: process knowledge accumulates from doing the work; domain knowledge is the briefing about *why* the work exists. **Working state and skill outputs** sit at the project root: `workstreams/`, `sessions/active/`, and `artifacts/` are scaffolded at registration; `collected/` and `contributions/` are created by their owning skills on first use.

## Workspace-level memory and random tasks

- The workspace itself supports random tasks that don't warrant a project entry. Workspace-level `workstreams/`, `sessions/active/`, `collected/`, `artifacts/`, and `contributions/` exist at the workspace root for this — same layout as projects, just at the level above.
- `<workspace>/.claude/memory/MEMORY.md`, `lessons-learned.md`, and `project-context.md` always exist (the third holds workspace-level domain context — overarching focus areas of this workspace, distinct from `me/identity.md` which is user-scoped: identity is "who I am", project-context is "what this workspace is for"). Without auto-memory, MEMORY.md and lessons-learned.md are the user's primary personal memory store. With auto-memory enabled, they become a curated layer above the typed atom files; `project-context.md` remains user-curated either way.
- Workspace-level skills (e.g., `/collect-team-activity`, `/one-on-one-prep`, `/collect-my-activity`, and `/my-digest` — *planned, not yet shipped*) write to `<workspace>/{collected,artifacts}/`. Project-scoped skills write under `<workspace>/projects/<slug>/{collected,artifacts}/`.
- Identity, brag log, growth, and team files live at `<workspace>/me/`: `identity.md`, `brag-log.md`, `growth.md`, optionally `team.md`.

## Memory loading architecture

Three memory layers coexist; each follows the same pattern (index loaded at session start, topic files on-demand) and never overlaps with the others mechanically.

| Layer | Owner | Location | Load mechanism |
|---|---|---|---|
| Harness auto-memory | Claude Code (Anthropic) | `~/.claude/projects/<harness-slug>/memory/MEMORY.md` | Auto-loaded by the harness at session start (first 200 lines / 25 KB). Topic files read on demand when relevant. |
| Workspace memory | Boilerplate | `<workspace>/.claude/memory/MEMORY.md` | Loaded via `@.claude/memory/MEMORY.md` import in `<workspace>/CLAUDE.md`, picked up by Claude Code's ancestor walk on every workspace-rooted session. Topic files referenced inside MEMORY.md as markdown links — read on demand. |
| Project memory | Boilerplate | `<workspace>/projects/<slug>/.claude/memory/MEMORY.md` | Same shape: `@.claude/memory/MEMORY.md` in the project's `CLAUDE.md`. For cd-in engineers (entering the project repo without `/hello`), the project CLAUDE.md auto-loads via ancestor walk; the `@`-include then loads the index. For workspace-rooted users, `/hello` step 9 reads project memory directly. |

### Parallel-systems contract

The boilerplate is a **parallel system** to the harness, not a replacement. Anthropic owns the harness mechanism (`autoMemoryEnabled`, `autoMemoryDirectory`, the 200-line cap, realpath project keying); the boilerplate adds workspace- and project-scope memory layers via committed files and `@`-includes in CLAUDE.md. Both layers follow the harness's documented design: **the index loads at session start; topic files load on demand when Claude judges them relevant.**

Consequences:

- **No `@`-lines for topic files inside MEMORY.md.** The index references topic files via markdown links (e.g., `- [Title](feedback_X.md) — hook`). Adding `@`-lines for each would force always-load, deviating from the documented pattern, costing context for content that may never be relevant this session, and creating an asymmetry with the harness layer.
- **The boilerplate never redirects, disables, or wraps the harness auto-memory.** They coexist.
- **Workspace MEMORY.md and harness MEMORY.md may carry related content** (cross-cutting personal feedback can graduate from the harness layer to the workspace layer via `/bye` curation), but there is no mechanism-level overlap.

### What does NOT auto-load

- `lessons-learned.md` — raw inbox; can grow unboundedly. Written by `/lessons` capture; read by `/bye` for promotion candidates; never `@`-included.
- `.claude/docs/architecture.md`, `conventions.md`, `cognee-usage.md` — reference layer; read on demand, never `@`-included.
- `workstreams/`, `sessions/`, `artifacts/`, `collected/`, `contributions/` — per-session or derived; never included.

The inclusion list is deliberately narrow. Memory entries are short and high-signal per byte; reference docs are long and low-signal per session — the cost/benefit per byte differs, hence the split.

### Reference

- Anthropic memory docs: https://code.claude.com/docs/en/memory
- `@`-import syntax in CLAUDE.md: nested imports recurse up to 5 hops; only resolved in CLAUDE.md (and `@`-chained files), not in auto-memory MEMORY.md.

## Single-workspace recommended

- Each user maintains one workspace by default. Multiple workspaces are supported but each is self-contained — auto-memory pools at each workspace's harness slug; the project registry is per-workspace.

## Session lifecycle

- `/hello` loads workspace memory (`<workspace>/.claude/memory/{MEMORY,lessons-learned}.md`) at every session start. When a project is selected, project memory (`<workspace>/projects/<slug>/.claude/memory/{MEMORY,lessons-learned}.md`) layers on top — project knowledge augments workspace knowledge, never replaces it.
- `/hello` writes an advisory session marker at `<workspace>/projects/<slug>/sessions/active/<id>.md` (project context) or `<workspace>/sessions/active/<id>.md` (workspace-level task). The marker records the workstream and the open item the session is bound to.
- **Multiple concurrent sessions are supported, with the open item as the conflict unit.** Two sessions on the same workstream working on different open items are valid; two sessions on the same open item are not. `/hello` scans active markers before writing its own and warns on conflict (matching workstream + open item), with the existing marker's age, and asks the user whether to proceed or stand down.
- **Concurrency is enforced via optimistic concurrency (mtime-check + retry), not locks.** A crashed session leaves a stale lock that blocks every future write until manually cleared; mtime-check has no persistent state to recover. `/bye` edits workstream files surgically (open-item status changes, additions to context/decisions/notes) — never rewrites them from scratch — with mtime-check guarding the targeted edits. `latest-session.md` is overwritten in full with a mtime-check guard; on conflict, `/bye` prompts the user to overwrite, append, or skip rather than silently clobbering.
- `/bye` writes lessons to the active context (repo `.claude/memory/` for repo work; workspace memory or auto-memory for personal work), updates the brag log if warranted, and removes its own session marker.
- `/memory-hygiene` (the opt-in auto-memory package) manages the auto-memory lifecycle when enabled — typed atom hygiene, graduation into curated long-form, archival.

## Agent-guardrails layering

- **Workspace owns universal rules.** `<workspace>/.claude/docs/agent-guardrails.md` carries the canonical universal/session-agent/autonomous-agent rules. The workspace `CLAUDE.md` `@import`s it inline. Every workspace-rooted session and every project sub-session inherits the universals via Claude Code's traversal-up.
- **Projects own overlays only, optional.** A project may add `.claude/docs/agent-guardrails.md` containing only project-specific additions and the project `CLAUDE.md` may `@import` it. Projects MUST NOT re-declare the universal rules — the workspace already loads them. `/setup-workspace add-project` deliberately does NOT scaffold a project agent-guardrails file or `@import`; the user adds them when (and only when) the project needs an overlay.
- **No cross-import across setups.** A separate legacy setup carries its own self-contained `.claude/docs/agent-guardrails.md`; it does not reach into the workspace and the workspace does not reach into it. Each self-contained setup owns its full guardrails surface (universals + any overlays).
- **Why layering, not full duplication.** Duplicating universals into every project creates drift (`/setup-workspace sync` would have to push to N copies; manual edits in one don't propagate). Single source + traversal-based inheritance keeps universals consistent without sync ceremony, while still leaving room for project-specific additions.

## Skill authoring principles

1. **Write the *what*, not the *how* — let the agent figure things out.** Trust the agent on mechanics (tmp filenames, error parsing, output structure, cleanup). Numbered algorithms with exact commands age out as upstream changes and inflate every invocation's prompt for no behavioural gain.
2. **If the skill relies on external services, don't be deterministic about them.** Never prescribe API response shapes, exact JSON structures, or service-specific failure modes — the service tells the agent what it returned. Encoding those details creates drift the moment the service changes.
3. **Nudge on issues the agent always faces.** Non-obvious problems that cost round-trips and tokens to work out (sandbox quirks, tool corner cases, surprising semantics) belong in the skill. Insight plus minimum action, nothing more.
4. **Exception: be deterministic about stable, mechanical work.** If a skill does the same thing every invocation against a stable surface, and a deterministic prescription removes ongoing cognitive load even for a weaker model — be deterministic.

`/skills-manager` applies these principles when adding, updating, or reviewing skills, and flags conflicts between principles and current best practices for explicit resolution rather than silent override.

## Update and contribution flow

- `/setup-workspace sync` pulls upstream changes for content the boilerplate genuinely owns: skills, agents, and `agent-guardrails.md`. Local edits to these are flagged at sync time; the user consents before overwrite.
- Other docs in `.claude/docs/` (`architecture.md`, `conventions.md`, `cognee-usage.md`, etc.) are **templates** copied at init. The team or user evolves them over time; sync does NOT overwrite them.
- The user's own `CLAUDE.md`, workstreams, sessions, and any user-authored content are not touched by sync.
- Edits intended for upstream go through `/contribute`, which stages changes in the source repo for a PR.

## First-time experience without setup

- An engineer who clones a repo without the boilerplate sees a setup tip in the repo's `CLAUDE.md` prose, auto-loaded by Claude Code at session start. The tip recommends installation but doesn't block work.
- Repos that ship with `.claude/skills/` committed remain functional standalone.

## What's committed where

| Surface | Committed | Gitignored |
|---------|-----------|------------|
| Repo | `CLAUDE.md`, `.claude/memory/MEMORY.md`, `.claude/memory/lessons-learned.md`, `.claude/docs/`, `.claude/settings.json` (optionally `.claude/skills/`) | `workstreams/`, `sessions/`, `collected/`, `artifacts/`, `contributions/` (all at repo root) |
| Workspace | boilerplate scaffolding, identity, brag log, skills, agents, docs, `.claude/memory/MEMORY.md`, `.claude/memory/lessons-learned.md` | `projects/`, `workstreams/`, `sessions/`, `collected/`, `artifacts/`, `contributions/` (all at workspace root) |

The user decides their own workspace backup strategy — git remote, dotfiles tool, or none at all. The boilerplate doesn't dictate.

## Naming

- `collected/` — raw collection outputs from skills (was `activity/`).
- `artifacts/` — synthesised outputs from skills (was `reports/`).
