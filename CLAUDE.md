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

Cognee MCP requires `LLM_API_KEY` set in your shell environment. Add to `~/.zshrc` or `~/.bashrc`:
```bash
export LLM_API_KEY="your-openai-api-key"
```
Run `/setup-cognee` for full guided installation (includes PostgreSQL, uv, etc.).

## Available Skills

| Skill | Purpose |
|-------|---------|
| `/hello` | Start a session — loads context, checks MCP health, recaps last session |
| `/bye` | End a session — summarizes work, captures lessons, persists memory |
| `/lessons` | Capture a lesson learned (auto-invoked by `/bye`, or use manually) |
| `/skills-manager` | Propose skill improvements (auto-invoked by `/lessons`, or use manually) |
| `/mcp-doctor` | Check health of configured MCP servers |
| `/contribute` | Generalize a lesson and stage it for boilerplate contribution |
| `/pull-contributions` | Pull generalized contributions from a project into the boilerplate |
| `/setup-cognee` | Install and configure cognee-mcp on a new machine |

### Skill chains (automatic)
- `/hello` → `/mcp-doctor`
- `/bye` → `/lessons` → `/skills-manager`
- `/setup-cognee` → `/mcp-doctor`

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
