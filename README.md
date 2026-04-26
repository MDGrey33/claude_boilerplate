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

1. **Clone** this repo (or merge into an existing project)
2. **Run `/setup-cognee`** — detects your environment, installs dependencies, configures everything
3. **Customize** — fill in `CLAUDE.md`, `.claude/docs/architecture.md`, `.claude/docs/conventions.md`
4. **Start working** — `/hello` to begin, `/bye` to end

**Existing project?** Ask Claude Code: *"Install the cognee boilerplate from /path/to/claude_boilerplate into this project"* — it will merge files carefully, preserving your existing config.

## Requirements

- [Claude Code](https://claude.ai/code) CLI
- An LLM API key (OpenAI recommended; Anthropic and Ollama also supported)

Everything else (Python, uv, Docker, PostgreSQL) is detected and installed by `/setup-cognee`.

## Skills Reference

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `/hello` | Manual | Start a new session — load context, check MCP health, recap last session |
| `/bye` | Manual | End the session — summarize work, capture lessons, persist memory |
| `/lessons` | Auto (via `/bye`) or manual | Capture lessons (default) OR `scan` recent session files / `scan --deep` raw JSONL for skill-change proposals |
| `/skills-manager` | Auto (via `/lessons`) or manual | Manage skills — add, update, remove, and review |
| `/mcp-doctor` | Auto (via `/hello`, `/setup-cognee`) or manual | Health check configured MCP servers |
| `/collect-my-activity` | Manual | Collect user's daily activity from Slack, Jira, Confluence, GitHub, Drive |
| `/collect-team-activity` | Manual | Collect a team member's daily activity (leadership roles) |
| `/one-on-one-prep` | Manual | Synthesize a member's activity into 1:1 meeting prep |
| `/log` | Auto (via skills) | Append structured entry to agent log |
| `/contribute` | Manual | Generalize a lesson and stage it in `.claude/contributions/` |
| `/pull-contributions` | Manual (from boilerplate repo) | Pull staged contributions from a project into the boilerplate |
| `/setup-cognee` | Manual | Install and configure cognee-mcp on this machine |
| `/sanitizer` | Auto (via `/contribute`, `/pull-contributions`) or manual | Scrub files for secrets, PII, private context, tone risks before publish. `--check` mode for CI gates. |
| `/finance-controller` | Manual (weekly sweep) | Audit CLAUDE.md, skills, MCPs for cost and context efficiency. Reports + delegates; never edits directly. |
| `/claude-expert` | Manual | Reference for Claude Code surfaces (skills vs hooks vs subagents vs MCPs vs memory vs settings). Answers "where should this live" and routes to the doer skill. |

### Skill Chains

```
/hello ──> /mcp-doctor
/bye ──> /lessons ──> /skills-manager
/setup-cognee ──> /mcp-doctor
/contribute ──> /sanitizer (blocks staging on any finding)
/pull-contributions ──> /sanitizer --check (blocks pull on any finding)
/sanitizer (manual, on any file/dir/glob)
```

Each skill works independently too. Use `/lessons "always use type hints"` or `/mcp-doctor` anytime.

## Contributing Back to the Boilerplate

Lessons learned in individual projects can flow back to improve the shared boilerplate — without leaking project-specific details.

### Flow

```
Project A                          Boilerplate Repo
─────────                          ────────────────
/lessons "discovery"
  → .claude/memory/lessons-learned.md
/contribute
  → generalizes lesson
  → strips project details
  → writes to .claude/contributions/
                                   /pull-contributions /path/to/project-a
                                     → reads contributions
                                     → flags any leaked details
                                     → applies with user approval
                                     → marks as integrated
```

### How it works

1. **In your project**: Run `/contribute` (or `/contribute "the lesson"`) to generalize a lesson. Claude strips project names, paths, and domain terms, then writes a contribution file to `.claude/contributions/`.

2. **In the boilerplate repo**: Run `/pull-contributions /path/to/your/project` to review and integrate. Each contribution is shown individually for approval. No changes are made without explicit confirmation.

3. **Privacy by design**: The `/contribute` skill rewrites lessons to be project-agnostic before saving. The `/pull-contributions` skill flags any remaining project-specific details. Project-specific knowledge never leaves the project automatically.

## Memory Architecture

Three scopes keep knowledge organized by ownership:

| Scope | Location | Purpose |
|-------|----------|---------|
| Personal | `~/.claude/me/` | Identity, team roster, brag log, growth notes |
| Project | `repo/.claude/memory/` | Lessons, distilled knowledge, workstreams, activity, reports |
| Contributions | `repo/.claude/contributions/` | Generalized lessons staged for boilerplate |

### Personal workspace (`~/.claude/me/`)

Created on first `/hello`, built up organically by `/bye` across all repos. Not in any git repo — personal to the engineer.

```
~/.claude/me/
├── identity.md          # Role, domains, skills, timezone, platform IDs
├── team.md              # Direct reports and their platform IDs (leadership roles)
├── brag-log.md          # Accomplishments across all repos (append-only)
└── growth.md            # Improvement areas, self-assessment notes
```

### Project memory (`repo/.claude/memory/`)

```
.claude/memory/
├── MEMORY.md              # Stable patterns, key decisions (loaded into system prompt)
├── lessons-learned.md     # Categorized lessons (appended over time)
├── project-context.md     # Domain knowledge (manually maintained)
├── sessions/
│   └── latest-session.md  # Last session summary (overwritten each /bye)
├── workstreams/           # Per-topic working context (lazy-loaded from user intent)
├── activity/              # Daily collection outputs (never auto-loaded)
└── reports/               # Synthesis outputs — weekly rollups, 1:1 preps (never auto-loaded)

.claude/contributions/         # Generalized lessons staged for boilerplate (via /contribute)
```

**Markdown** is the primary store — always available, fast, deterministic.
**Cognee** is the enrichment layer — semantic search across all accumulated knowledge.

Skills gracefully degrade if cognee MCP is unavailable.

### Team & leadership features

For engineering managers, directors, and VPs — driven by `~/.claude/me/identity.md` (role) and `~/.claude/me/team.md` (direct reports):

- **`/collect-team-activity`** — collects a team member's daily activity from public Slack, Jira, Confluence, GitHub
- **`/one-on-one-prep`** — synthesizes collected activity into a structured 1:1 meeting agenda
- **`/collect-my-activity`** — works for any role, collects your own activity across all sources

## Customization

### Which files to edit

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Project name, description, conventions — Claude reads this every session |
| `.claude/docs/architecture.md` | Your project's architecture and structure |
| `.claude/docs/conventions.md` | Code style, patterns, and standards |
| `.claude/memory/project-context.md` | Domain-specific knowledge |
| `~/.claude/me/identity.md` | Your role, preferences, writing style (personal, not per-project) |

### Adding a new skill

1. Create `.claude/skills/your-skill/SKILL.md`
2. Follow the SKILL.md format (see existing skills for examples)
3. Add it to the skills table in `CLAUDE.md`

### Modifying memory structure

The memory files are plain markdown. Add new files or sections as needed. Update `/hello` and `/bye` skills if you add files they should read/write.
