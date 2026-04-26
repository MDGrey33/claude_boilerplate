# [Project Name]

> Brief project description. Replace this with your project's purpose.

## Memory & Knowledge

This project uses **cognee** for persistent semantic memory alongside markdown-based context files.

Three scopes, each with its own owner and location:

| Scope | Location | Purpose |
|-------|----------|---------|
| Personal | `~/.claude/me/` | Identity, team roster, brag log, growth notes |
| Project | `repo/.claude/memory/` | Lessons, distilled knowledge, workstreams |
| Contributions | `repo/.claude/contributions/` | Generalized lessons staged for boilerplate |

Project memory layout:

```
.claude/memory/
├── MEMORY.md              # Distilled knowledge (curated, always loaded)
├── lessons-learned.md     # Raw lessons (append-only, always loaded)
├── project-context.md     # Domain context for this project (always loaded)
├── sessions/
│   └── latest-session.md  # Last session recap
├── workstreams/           # Per-topic working context (lazy-loaded)
```

## Agent Behavior

See `.claude/docs/agent-guardrails.md` for operational principles.

## Prerequisites

Run `/setup-cognee` for first-time installation and configuration. It detects your environment and walks you through everything.

## Available Skills

| Skill | Purpose |
|-------|---------|
| `/hello` | Start a new session — loads context, checks MCP health, recaps last session |
| `/bye` | End the session — summarize work, capture lessons, persist memory |
| `/lessons` | Capture lessons (default) OR `scan` session files / `scan --deep` JSONL transcripts for skill-change proposals. Auto-invoked by `/bye`. |
| `/skills-manager` | Manage skills — add, update, remove, and review (auto-invoked by `/lessons`, or use manually) |
| `/mcp-doctor` | Check health of configured MCP servers |
| `/log` | Append structured entry to agent log (internal/auto-only, not user-invocable) |
| `/contribute` | Generalize a lesson and stage it for boilerplate contribution |
| `/pull-contributions` | Pull generalized contributions from a project into the boilerplate |
| `/setup-cognee` | Install and configure cognee-mcp on this machine |
| `/setup-playwright-mcp` | Install and configure Playwright MCP for browser automation |
| `/sanitizer` | Scrub a file/dir/glob for secrets, PII, private context, and tone risks before publishing. Auto-invoked by `/contribute` and `/pull-contributions`. Has a `--check` mode for pre-commit/CI gates. |
| `/finance-controller` | Audit CLAUDE.md, skills, MCPs for cost and context efficiency. Produces a prioritized report; delegates execution to `skills-manager` or asks for approval. Use weekly or when sessions feel slow. |
| `/claude-expert` | Reference for Claude Code surfaces — skills vs hooks vs subagents vs MCPs vs memory vs settings. Use when asked "where should this live" or "how does Claude Code X work". Routes to the doer skill; never edits itself. |

### Skill chains (automatic)
- `/hello` → `/mcp-doctor`
- `/bye` → `/lessons` → `/skills-manager`
- `/setup-cognee` → `/mcp-doctor`
- `/setup-playwright-mcp` → `/mcp-doctor`
- `/contribute` → `/sanitizer` (blocks staging on any finding)
- `/pull-contributions` → `/sanitizer --check` (blocks pull on any finding)

## Workflow

1. **Setup** (once): Run `/setup-cognee` on a new machine
2. **Start**: Run `/hello` at the beginning of each session
3. **Work**: Do your thing
4. **End**: Run `/bye` when you're done

## Project Conventions

<!-- Fill in per project -->
- Language:
- Framework:
- Test runner:
- Formatting:

## Detailed Docs

Refer to these files for more detail (use `@` to include them in context):
- `.claude/docs/architecture.md` — project architecture
- `.claude/docs/conventions.md` — code style and patterns
- `.claude/docs/cognee-usage.md` — how to use cognee MCP tools
