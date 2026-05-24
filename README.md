# Cognee-Powered Claude Code Boilerplate

Persistent memory and session management for Claude Code, powered by [cognee](https://github.com/topoteretes/cognee) knowledge graphs.

## What This Does

- **Dual memory**: Markdown files for fast, deterministic access + Cognee knowledge graph for semantic retrieval
- **Session management**: `/hello` loads context at start, `/bye` persists it at end
- **Lessons learned**: Captures mistakes, conventions, and patterns during session wrap-up
- **Skills lifecycle**: `/skills-manager` adds, updates, removes, and reviews skills based on lessons or requests
- **MCP health monitoring**: `/mcp-doctor` checks connectivity
- **Boilerplate contributions**: `/contribute` generalizes project lessons; `/pull-contributions` integrates them back into the boilerplate

## Quick Start

```bash
git clone https://github.com/MDGrey33/claude_boilerplate.git ~/src/claude_boilerplate
mkdir -p ~/workspace
cd ~/src/claude_boilerplate
claude
# in the session: /setup-workspace init --workspace ~/workspace
# exit, then start all future sessions from ~/workspace
```

1. **Clone** to a path outside your workspace (sibling layout — see Skills Reference)
2. **Init** — `/setup-workspace init --workspace <path>` deploys skills, generates `CLAUDE.md`, bootstraps identity
3. **Add projects** — `/setup-workspace add-project <slug>` from the workspace root
4. **Start working** — `/hello` to begin each session, `/bye` to end
5. **Cognee (optional)** — `/setup-cognee` for semantic memory, after the workspace is verified end-to-end

## Requirements

- [Claude Code](https://claude.ai/code) CLI

Cognee (optional): `/setup-cognee` detects your environment and installs Python, uv, Docker, and PostgreSQL as needed. Supports OpenAI, Anthropic, and Ollama as the LLM backend.

## Skills Reference


| Skill | Trigger | Purpose |
|-------|---------|---------|
| `/setup-workspace` | Manual | (v2) Workspace lifecycle: `init` (first-time setup, deploys skills/agents/docs, generates `CLAUDE.md`), `add-project <slug> [description]` (scaffolds a project under `<workspace>/projects/<slug>/`, registers it — includes `CLAUDE.md`, memory files, and `docs/architecture.md` + `docs/conventions.md`), `sync` (re-copies skills/agents from source clone, flags conflicts before overwrite). |
| `/project-registry` | Auto (via `/setup-workspace`) or manual | (v2) Manage the workspace project registry — `add` / `remove` / `update` / `list`. Single mutation point; other skills read the index file directly. |
| `/hello` | Manual | Start a new session — load context, check MCP health, recap last session |
| `/bye` | Manual | End the session — summarize work, capture lessons, persist memory |
| `/lessons` | Auto (via `/bye`) or manual | Capture lessons (default) OR `scan` recent session files / `scan --deep` raw JSONL for skill-change proposals |
| `/skills-manager` | Auto (via `/lessons`) or manual | Manage skills — add, update, remove, and review |
| `/mcp-doctor` | Auto (via `/hello`, `/setup-cognee`) or manual | Health check configured MCP servers — session mode by default; `--deep` for process-level diagnosis |
| `/collect-my-activity` | Manual | Collect user's daily activity from Slack, Jira, Confluence, GitHub, Drive |
| `/collect-team-activity` | Manual | Collect a team member's daily activity (leadership roles) |
| `/one-on-one-prep` | Manual | Synthesize a member's activity into 1:1 meeting prep |
| `/log` | Auto (via skills) | Append structured entry to agent log |
| `/contribute` | Manual | Generalize a lesson and stage it in `<workspace>/contributions/` |
| `/pull-contributions` | Manual (from boilerplate repo) | Pull staged contributions from a project into the boilerplate |
| `/setup-cognee` | Manual | Install and configure cognee-mcp on this machine |
| `/sanitizer` | Auto (via `/contribute`, `/pull-contributions`) or manual | Scrub files for secrets, PII, private context, tone risks before publish. `--check` mode for CI gates. |
| `/finance-controller` | Manual (weekly sweep) | Audit CLAUDE.md, skills, MCPs for cost and context efficiency. Reports + delegates; never edits directly. |
| `/claude-expert` | Manual | Reference for Claude Code surfaces (skills vs hooks vs subagents vs MCPs vs memory vs settings). Answers "where should this live" and routes to the doer skill. |
| `/setup-auto-memory` | Manual | Wire in the optional auto-memory system (typed atomic files in `~/.claude/projects/<slug>/memory/`). See `auto-memory/README.md`. |
| `/setup-playwright-mcp` | Manual | Install and configure Playwright MCP for browser automation |
| `/setup-nemoclaw` | Manual | Install and configure NVIDIA NemoClaw (secure agent runtime) |
| `/deep-research-orchestrator` | Manual | Run a 9-stage deep research pipeline — breadth, depth, synthesis, gap-fill, contradiction detection, theory, fact-check; tiered output with credibility tagging |

### Skill Chains

```text
/hello ──> /mcp-doctor (session mode)
/bye ──> /lessons ──> /skills-manager
/setup-cognee ──> /mcp-doctor
/setup-playwright-mcp ──> /mcp-doctor
/contribute ──> /sanitizer (blocks staging on any finding)
/pull-contributions ──> /sanitizer --check (blocks pull on any finding)
/sanitizer (manual, on any file/dir/glob)
```

Each skill works independently too. Use `/lessons "always use type hints"` or `/mcp-doctor` anytime.

## Contributing Back to the Boilerplate

Lessons learned in individual projects can flow back to improve the shared boilerplate — without leaking project-specific details.

### Flow

```text
Project A                          Boilerplate Repo
─────────                          ────────────────
/lessons "discovery"
  → .claude/memory/lessons-learned.md
/contribute
  → generalizes lesson
  → strips project details
  → writes to <workspace>/contributions/
                                   /pull-contributions <workspace>/contributions/
                                     → reads contributions
                                     → flags any leaked details
                                     → applies with user approval
                                     → marks as integrated
```

### How it works

1. **In your project**: Run `/contribute` (or `/contribute "the lesson"`) to generalize a lesson. Claude strips project names, paths, and domain terms, then writes a contribution file to `<workspace>/contributions/`.

2. **In the boilerplate repo**: Run `/pull-contributions /path/to/your/project` to review and integrate. Each contribution is shown individually for approval. No changes are made without explicit confirmation.

3. **Privacy by design**: The `/contribute` skill rewrites lessons to be project-agnostic before saving. The `/pull-contributions` skill flags any remaining project-specific details. Project-specific knowledge never leaves the project automatically.

## Memory Architecture

Three scopes keep knowledge organised by ownership:

| Scope | Location | Purpose |
|-------|----------|---------|
| Personal | `<workspace>/me/` | Identity, team roster, brag log, growth notes |
| Project | `<project>/.claude/memory/` + project root | Process knowledge, domain context, working state |
| Contributions | `<workspace>/contributions/` | Generalised lessons staged for boilerplate |

### Personal workspace (`<workspace>/me/`)

Bootstrapped by `/setup-workspace init`, built up organically by `/bye`. Not in any git repo — personal to the engineer. `<workspace>` is wherever the user installed the boilerplate (e.g., `~/workspace/`).

```text
<workspace>/me/
├── identity.md          # Role, domains, skills, timezone, platform IDs
├── team.md              # Direct reports and their platform IDs (leadership roles)
├── brag-log.md          # Accomplishments across all projects (append-only)
└── growth.md            # Improvement areas, self-assessment notes
```

### Project layout

Working state and skill outputs sit at the **project root** (gitignored). Committed knowledge lives under `.claude/`.

```text
<project root>/
├── workstreams/           # Per-topic working context (gitignored)
├── sessions/active/       # Active session markers (gitignored)
├── sessions/              # Closed session narratives (gitignored)
├── collected/             # Raw collection outputs from skills (gitignored)
├── artifacts/             # Synthesised skill outputs (gitignored)
└── contributions/         # Staged boilerplate contributions (gitignored)

.claude/
├── memory/
│   ├── MEMORY.md              # Stable patterns, key decisions (always loaded)
│   ├── lessons-learned.md     # Raw lessons inbox (always loaded)
│   └── project-context.md     # Domain knowledge (always loaded)
├── docs/
│   ├── architecture.md        # Project architecture (on-demand)
│   └── conventions.md         # Code style and patterns (on-demand)
└── settings.json
```

**Markdown** is the primary store — always available, fast, deterministic.
**Cognee** is the optional enrichment layer — semantic search across accumulated knowledge. Skills degrade gracefully if unavailable.

### How memory loads

Claude Code reads memory in two passes at session start:

1. **CLAUDE.md ancestor walk.** Every `CLAUDE.md` from cwd up to the filesystem root is loaded in full. `@<path>` imports inside any of those files expand recursively (up to 5 hops).

2. **Auto-memory.** The harness's own MEMORY.md at `~/.claude/projects/<slug>/memory/MEMORY.md` is loaded as text (first 200 lines or 25 KB, whichever is smaller). Topic files referenced inside it are NOT auto-loaded — Claude reads them on demand when relevant. See [Anthropic's memory docs](https://code.claude.com/docs/en/memory) for the full mechanism.

Workspace and project memory follow the same pattern as the harness: the workspace `CLAUDE.md` `@`-includes `<workspace>/.claude/memory/MEMORY.md`; each project's `CLAUDE.md` does the same at project scope. The index loads at session start; topic files referenced inside (`feedback_*.md`, `convention_*.md`, etc.) are read on demand. Engineers entering a project repo directly — without setting up the workspace — still get the project's curated memory index loaded automatically via the project's `CLAUDE.md` `@`-include.

The boilerplate never redirects, wraps, or overrides the harness auto-memory. Two parallel layers: the harness carries per-user notes the harness writes; workspace and project memory carry curated patterns written by `/bye`. See [Optional: Auto-Memory System](#optional-auto-memory-system) below for the auto-memory layer's curation discipline and the `setup-auto-memory` skill that wires it in.

### Team & leadership features

For engineering managers, directors, and VPs — driven by `<workspace>/me/identity.md` (role) and `<workspace>/me/team.md` (direct reports):

- **`/collect-team-activity`** — collects a team member's daily activity from public Slack, Jira, Confluence, GitHub
- **`/one-on-one-prep`** — synthesizes collected activity into a structured 1:1 meeting agenda
- **`/collect-my-activity`** — works for any role, collects your own activity across all sources

## Optional: Auto-Memory System

For how the auto-memory layer loads alongside workspace and project memory, see [How memory loads](#how-memory-loads) above. This section covers the curation discipline and the `setup-auto-memory` skill that wires the opt-in package in.

This boilerplate also ships an opt-in **auto-memory** package at `auto-memory/`. It complements the project-scope memory above with a user-scope, typed-atomic-file system that lives under `~/.claude/projects/<slug>/memory/` — the directory Claude Code's harness already manages per project.

The two layers serve different purposes: project memory holds curated repo knowledge shared with collaborators; auto-memory holds personal preferences and behavioral feedback that follow the user across projects.

To wire it in, run `/setup-auto-memory` from any project. It is gated, idempotent, and never touches the project-scope memory.

See `auto-memory/README.md` for the full description.

## Customization

### Which files to edit

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Project name, description, conventions — Claude reads this every session |
| `.claude/docs/architecture.md` | Your project's architecture and structure |
| `.claude/docs/conventions.md` | Code style, patterns, and standards |
| `.claude/memory/project-context.md` | Domain-specific knowledge |
| `<workspace>/me/identity.md` | Your role, preferences, writing style (personal, not per-project) |

### Adding a new skill

1. Create `.claude/skills/your-skill/SKILL.md`
2. Follow the SKILL.md format (see existing skills for examples)
3. Add it to the skills table in `CLAUDE.md`

### Modifying memory structure

The memory files are plain markdown. Add new files or sections as needed. Update `/hello` and `/bye` skills if you add files they should read/write.
