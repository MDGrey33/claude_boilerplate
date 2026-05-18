# [Project Name]

> Brief project description. Replace this with your project's purpose.

## Memory & Knowledge

Three scopes, each with its own owner and location:

| Scope | Location | Purpose |
|-------|----------|---------|
| Personal | `<workspace>/me/` | Identity, team roster, brag log, growth notes |
| Project | `<project>/.claude/memory/` + project root | Process knowledge, domain context, working state |
| Contributions | `<workspace>/contributions/` | Generalised lessons staged for boilerplate |

Project layout:

```
<project root>/
├── workstreams/           # Per-topic working context (gitignored)
├── sessions/active/       # Active session markers (gitignored)
├── sessions/              # Closed session narratives (gitignored)
├── collected/             # Raw collection outputs from skills (gitignored)
└── artifacts/             # Synthesised skill outputs (gitignored)

.claude/
├── memory/
│   ├── MEMORY.md              # Distilled knowledge (curated, always loaded)
│   ├── lessons-learned.md     # Raw lessons inbox (always loaded)
│   └── project-context.md     # Domain context (always loaded)
├── docs/
│   ├── architecture.md        # Project architecture (on-demand)
│   └── conventions.md         # Code style and patterns (on-demand)
└── settings.json
```

## Agent Behavior

See `.claude/docs/agent-guardrails.md` for operational principles.

## Prerequisites

Run `/setup-workspace init --workspace <path>` to initialise a workspace (see README for the sibling-layout requirement). Cognee is optional — run `/setup-cognee` after the workspace is verified end-to-end.

## Available Skills

| Skill | Purpose |
|-------|---------|
| `/hello` | Start a new session — loads context, checks MCP health, recaps last session |
| `/bye` | End the session — summarize work, capture lessons, persist memory |
| `/lessons` | Capture lessons (default) OR `scan` session files / `scan --deep` JSONL transcripts for skill-change proposals. Auto-invoked by `/bye`. |
| `/skills-manager` | Manage skills — add, update, remove, and review (auto-invoked by `/lessons`, or use manually) |
| `/mcp-doctor` | Check health of configured MCP servers (session mode by default; `--deep` for process-level diagnosis) |
| `/collect-my-activity` | Collect user's daily activity from Slack, Jira, Confluence, GitHub, Drive |
| `/collect-team-activity` | Collect a team member's daily activity (leadership roles) |
| `/one-on-one-prep` | Synthesize a member's activity into 1:1 meeting prep |
| `/log` | Append structured entry to agent log (internal/auto-only, not user-invocable) |
| `/contribute` | Generalize a lesson and stage it for boilerplate contribution |
| `/pull-contributions` | Pull generalized contributions from a project into the boilerplate |
| `/setup-cognee` | Install and configure cognee-mcp on this machine |
| `/setup-auto-memory` | Wire in the optional auto-memory system. See `auto-memory/README.md`. |
| `/setup-playwright-mcp` | Install and configure Playwright MCP for browser automation |
| `/deep-research-orchestrator` | Run a 9-stage deep research pipeline — breadth, depth, synthesis, gap-fill, contradiction detection, theory, fact-check; tiered output with credibility tagging |
| `/sanitizer` | Scrub a file/dir/glob for secrets, PII, private context, and tone risks before publishing. Auto-invoked by `/contribute` and `/pull-contributions`. Has a `--check` mode for pre-commit/CI gates. |
| `/finance-controller` | Audit CLAUDE.md, skills, MCPs for cost and context efficiency. Produces a prioritized report; delegates execution to `skills-manager` or asks for approval. Use weekly or when sessions feel slow. |
| `/claude-expert` | Reference for Claude Code surfaces — skills vs hooks vs subagents vs MCPs vs memory vs settings. Use when asked "where should this live" or "how does Claude Code X work". Routes to the doer skill; never edits itself. |

### Skill chains (automatic)
- `/hello` → `/mcp-doctor` (session mode: enumerates loaded tools, no process spawning)
- `/bye` → `/lessons` → `/skills-manager`
- `/setup-cognee` → `/mcp-doctor`
- `/setup-playwright-mcp` → `/mcp-doctor`
- `/contribute` → `/sanitizer` (blocks staging on any finding)
- `/pull-contributions` → `/sanitizer --check` (blocks pull on any finding)

## Skills Governance

Skills in `.claude/skills/` are **deployed copies** — maintained in the boilerplate source, not in service repos. Do not edit them here directly.

To propose a skill improvement:
1. Use `/contribute` to generalise the lesson and stage it in `<workspace>/contributions/`
2. The boilerplate maintainer runs `/pull-contributions` to apply it
3. Changes land via GitHub PR and maintainer review

`/skills-manager` identifies improvement opportunities during sessions and guides you through step 1.

## Workflow

1. **Setup** (once per machine): `/setup-workspace init --workspace <path>` from the cloned source dir
2. **Start**: `/hello` at the beginning of each session
3. **Work**: use skills, register projects with `/setup-workspace add-project`
4. **End**: `/bye` when done
5. **Sync** (periodic): `/setup-workspace sync` to pull upstream skill updates

## Project Conventions

<!-- Fill in per project -->
- Language:
- Framework:
- Test runner:
- Formatting:

## Detailed Docs

Refer to these files for more detail (use `@` to include them in context):
- `.claude/docs/architecture.md` — project architecture and structure
- `.claude/docs/conventions.md` — code style and patterns
- `.claude/docs/cognee-usage.md` — how to use cognee MCP tools for semantic memory
