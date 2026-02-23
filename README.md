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

### 1. Add boilerplate to your project

**New project:**
```bash
git clone https://github.com/MDGrey33/claude_boilerplate.git my-project
cd my-project
```
Then update the git remote to point to your own repository.

**Existing project — let Claude Code handle it:**

The safest way to add this boilerplate to an existing project is to ask Claude Code directly:

> "Install the cognee boilerplate from /path/to/claude_boilerplate into this project"

Claude Code will merge files carefully — preserving your existing `.mcp.json` entries, `.gitignore` rules, and other config rather than overwriting them.

**Existing project — manual (advanced):**

If you prefer to do it yourself, copy these files into your project. **Do not** use `cp -r` blindly — it can overwrite your existing config.

| Source | Notes |
|--------|-------|
| `.claude/` directory | Copy the entire directory. If you already have `.claude/`, merge the contents. |
| `CLAUDE.md` | If you have an existing `CLAUDE.md`, merge the sections rather than replacing it. |
| `.mcp.json` | **Merge, don't overwrite.** If you have existing MCP servers configured, add the `cognee` entry to your existing file. |
| `.gitignore` | Append any missing entries to your existing `.gitignore`. |

### 2. Set up Cognee

The easiest way: run `/setup-cognee` from Claude Code and it will detect your environment and walk you through everything.

**Or manually — the recommended setup (uvx + PostgreSQL/PGVector):**

```bash
# 1. Set your API key (add to ~/.zshrc or ~/.bashrc for persistence)
export LLM_API_KEY="your-openai-api-key"

# 2. Start PostgreSQL + PGVector (one container, handles relational + vector)
docker run -d --name cognee-postgres \
  -e POSTGRES_USER=cognee -e POSTGRES_PASSWORD=cognee -e POSTGRES_DB=cognee_db \
  -p 5432:5432 --restart unless-stopped pgvector/pgvector:pg17

# 3. Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh
```

The default `.mcp.json` is pre-configured for this setup (uvx + Postgres). Graph uses Kuzu (embedded, zero config).

**How config works**: The `.mcp.json` file passes environment variables to cognee-mcp when Claude Code starts it. `${LLM_API_KEY}` is interpolated from your shell environment by Claude Code. The database settings (Postgres host, port, credentials) are hardcoded in `.mcp.json` for the recommended setup. No `.env` file is needed unless you're running cognee-mcp standalone outside of Claude Code.

**Alternative setups** (minimal/file-based, Docker full-stack, local clone, Ollama) are covered by `/setup-cognee`.

### 3. Customize for your project

1. Edit `CLAUDE.md` — fill in project name, description, and conventions
2. Edit `.claude/docs/architecture.md` — describe your project structure
3. Edit `.claude/docs/conventions.md` — document your code style
4. Edit `.claude/memory/project-context.md` — add domain knowledge

### 4. Start working

```
/hello          # Start session, load context
... do work ... # Claude Code remembers context
/bye            # End session, persist memory
```

## Skills Reference

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `/hello` | Manual | Start a session — load context, check MCP health, recap last session |
| `/bye` | Manual | Summarize session, capture lessons, persist to memory + cognee |
| `/lessons` | Auto (via `/bye`) or manual | Categorize and store lessons learned |
| `/skills-manager` | Auto (via `/lessons`) or manual | Add, update, remove, and review skills |
| `/mcp-doctor` | Auto (via `/hello`, `/setup-cognee`) or manual | Health check configured MCP servers |
| `/contribute` | Manual | Generalize a lesson and stage it in `.claude/contributions/` |
| `/pull-contributions` | Manual (from boilerplate repo) | Pull staged contributions from a project into the boilerplate |
| `/setup-cognee` | Manual | Install and configure cognee-mcp on this machine |

### Skill Chains

```
/hello ──> /mcp-doctor
/bye ──> /lessons ──> /skills-manager
/setup-cognee ──> /mcp-doctor
/contribute (manual, from any project)
/pull-contributions (manual, from boilerplate repo)
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

```
.claude/memory/
├── MEMORY.md              # Stable patterns, key decisions (loaded into system prompt)
├── sessions/
│   └── latest-session.md  # Last session summary (overwritten each /bye)
├── lessons-learned.md     # Categorized lessons (appended over time)
└── project-context.md     # Domain knowledge (manually maintained)

.claude/contributions/         # Generalized lessons staged for boilerplate (via /contribute)
```

**Markdown** is the primary store — always available, fast, deterministic.
**Cognee** is the enrichment layer — semantic search across all accumulated knowledge.

Skills gracefully degrade if cognee MCP is unavailable.

## Customization

### Adding a new skill

1. Create `.claude/skills/your-skill/SKILL.md`
2. Follow the SKILL.md format (see existing skills for examples)
3. Add it to the skills table in `CLAUDE.md`

### Modifying memory structure

The memory files are plain markdown. Add new files or sections as needed. Update `/hello` and `/bye` skills if you add files they should read/write.

## Requirements

- [Claude Code](https://claude.ai/code) CLI
- An LLM API key (OpenAI recommended for cognee)
- Docker (recommended, for PostgreSQL + PGVector) — or use the minimal file-based setup with no Docker
