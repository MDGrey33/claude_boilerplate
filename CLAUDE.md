# [Project Name]

> Brief project description. Replace this with your project's purpose.

## Memory & Knowledge

This project uses **cognee** for persistent semantic memory alongside markdown-based context files.

- **Active memory**: `.claude/memory/MEMORY.md` — accumulated knowledge, stable patterns
- **Session history**: `.claude/memory/sessions/latest-session.md` — last session recap
- **Lessons learned**: `.claude/memory/lessons-learned.md` — mistakes, conventions, discoveries
- **Project context**: `.claude/memory/project-context.md` — domain-specific knowledge
- **Contributions**: `.claude/contributions/` — generalized lessons staged for boilerplate

## Prerequisites

Run `/setup-cognee` for first-time installation and configuration. It detects your environment and walks you through everything.

## Available Skills

| Skill | Purpose |
|-------|---------|
| `/hello` | Start a new session — loads context, checks MCP health, recaps last session |
| `/bye` | End the session — summarize work, capture lessons, persist memory |
| `/lessons` | Capture and integrate lessons learned (auto-invoked by `/bye`, or use manually) |
| `/skills-manager` | Manage skills — add, update, remove, and review (auto-invoked by `/lessons`, or use manually) |
| `/mcp-doctor` | Check health of configured MCP servers |
| `/contribute` | Generalize a lesson and stage it for boilerplate contribution |
| `/pull-contributions` | Pull generalized contributions from a project into the boilerplate |
| `/setup-cognee` | Install and configure cognee-mcp on this machine |
| `/setup-playwright-mcp` | Install and configure Playwright MCP for browser automation |

### Skill chains (automatic)
- `/hello` → `/mcp-doctor`
- `/bye` → `/lessons` → `/skills-manager`
- `/setup-cognee` → `/mcp-doctor`
- `/setup-playwright-mcp` → `/mcp-doctor`

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
