# decision-tree.md — which Claude Code surface?

A longer form of the table in `SKILL.md`. Use as a lookup when picking a
surface for a new capability, and read the "commonly confused" section for
the subtle cases.

## The four-way: skill vs subagent vs hook vs md-file

The most common disambiguation. Use this first.

| Surface | Pick when | Enforcement | Context cost | Runs | Example |
|:--|:--|:--|:--|:--|:--|
| **Hook** (`settings.json`) | You need a behavior to happen **deterministically** on a lifecycle event (tool call, prompt submit, session start, compaction, stop). Non-negotiable. | Harness runs it; Claude can't skip. | Zero (runs outside the LLM). Can inject context into it. | Automatic, on event | "Run linter after every Edit/Write"; "Block writes to `.env`"; "Log every Bash call" |
| **Skill** (`.claude/skills/<name>/SKILL.md`) | A **reusable procedure** with instructions, sibling files, or a slash-command entry point. Body loads only when Claude (or the user) invokes it. | Advisory — Claude reads the body and tries to follow. | Description always loaded (~1% of window budget); body on-demand. | On `/skill-name` or when description matches | "Tailor resume to JD"; "Research X and produce report"; "Simplify code changes" |
| **Subagent** (`.claude/agents/<name>.md`) | The work needs **its own context window** — verbose output, different tool scope, different model, parallelism. | Advisory — like a skill but in isolation. | Zero to the main context; the subagent has its own. | Explicit delegation (`Agent(...)`) or automatic by description match | "Explore a huge codebase"; "Produce a 20k-word research report"; "Run tests and return summary only" |
| **md-file update** (`CLAUDE.md`, auto-memory, `.claude/rules/*.md`) | A **fact, preference, or rule** Claude should *know* across sessions. Not a trigger, not enforcement. | Context, not enforcement. Compliance isn't guaranteed. | Project `CLAUDE.md` always loaded; auto-memory first 200 lines / 25 KB; rules loaded when their `paths:` match. | At session start | "This project uses pnpm, not npm"; "GitHub username is acme-user"; "Never commit to main" |

### The trap

**If the user says "from now on, every time X, do Y" — it is a hook, not a
memory addition.** CLAUDE.md cannot enforce automation. Only hooks can.

Three more quick rules:

- **Procedure with branching logic** → Skill, not CLAUDE.md.
- **Work that would blow up the main context** → Subagent, not skill.
- **Personal fact vs project fact** → `~/.claude/CLAUDE.md` vs `./CLAUDE.md`.

For each of the four, there's a corresponding **doer skill** for actually
making the change:

| Surface | Doer |
|:--|:--|
| Hook | `update-config` (edits `settings.json`) |
| Skill | `skills-manager` (author, update, archive) |
| Subagent | no dedicated doer — ask claude-expert, then Write the `.claude/agents/<name>.md` file |
| md-file | Write directly, or let auto-memory self-manage |

## Primary table — what are you trying to do?

| Goal | Surface | Why | Deep dive |
|:--|:--|:--|:--|
| Run code before every tool call | Hook `PreToolUse` | Only hooks can fire deterministically on tool events | surfaces/hooks.md |
| Run code after every tool call | Hook `PostToolUse` | Same reason; `PostToolUseFailure` for failures | surfaces/hooks.md |
| Validate/reject a specific Bash command | Hook `PreToolUse` with `if: "Bash(rm *)"` + exit 2, OR `permissions.deny` rule | Deny rule is simpler for static cases; hook for dynamic validation | surfaces/permissions.md, surfaces/hooks.md |
| Rate-limit or block dangerous commands | Hook `PreToolUse` exit 2, OR `permissions.deny` rule | Prose/pattern preference | surfaces/permissions.md |
| Inject context when a session starts | Hook `SessionStart` with `additionalContext` | Only runs deterministically at start | surfaces/hooks.md |
| Inject context when user submits a prompt | Hook `UserPromptSubmit` | Can also block/rewrite prompts | surfaces/hooks.md |
| Set an env var on every session | `settings.json` → `env` | Declarative, no code | surfaces/settings.md |
| Auto-format after every edit | Hook `PostToolUse` matcher `"Edit\|Write"` | Tool-event-driven | surfaces/hooks.md |
| React to `/compact` | Hook `PreCompact` (block/log) or `PostCompact` (post-hoc) | — | surfaces/hooks.md |
| React to session end | Hook `SessionEnd` | — | surfaces/hooks.md |
| User types `/foo` to run a prompt | Skill at `.claude/skills/foo/SKILL.md` (or `.claude/commands/foo.md` legacy) | Custom commands merged into skills | surfaces/skills.md, surfaces/slash-commands.md |
| User types `/foo arg1 arg2` | Skill with `$ARGUMENTS` / `$0` / `$1` substitutions | Positional indexing supported | surfaces/skills.md |
| Reusable multi-step workflow with branching logic | Skill (not plain slash command) | Skills carry richer instructions | surfaces/skills.md |
| Reusable prompt template, no branching | Skill with `disable-model-invocation: true` | Keeps from triggering automatically | surfaces/skills.md |
| Domain knowledge Claude should apply when relevant | Skill with good `description`, no `disable-model-invocation` | Claude decides from description | surfaces/skills.md |
| Background reference material only Claude should know | Skill with `user-invocable: false` | Hidden from user menu | surfaces/skills.md |
| Specialist worker with isolated context window | Subagent | Context isolation is the whole point | surfaces/subagents.md |
| Worker that produces lots of output you don't want in main context | Subagent | Summary returns to main, not the bulk | surfaces/subagents.md |
| Worker with fewer/more tools than the main thread | Subagent with `tools:` or `disallowedTools:` | Per-agent restriction | surfaces/subagents.md |
| Worker using a different (cheaper) model | Subagent with `model: haiku` | Cost control | surfaces/subagents.md |
| Run same kind of work in parallel multiple times | Agent Team (or `spawn-team`) | Subagents serial unless backgrounded | surfaces/subagents.md, docs /en/agent-teams |
| Run a skill in isolation as a one-shot task | Skill with `context: fork` | Forks into subagent with skill body as prompt | surfaces/skills.md |
| External API/service Claude talks to | MCP server | Reusable across agents/sessions | surfaces/mcp.md |
| Database query access | MCP server (e.g. `dbhub`) | Tool-level, secure, reusable | surfaces/mcp.md |
| OAuth-protected SaaS integration | MCP server with HTTP transport + OAuth | Built-in OAuth support | surfaces/mcp.md |
| MCP server only in one subagent | Declare inline under subagent `mcpServers:` | Keeps it out of main conversation context | surfaces/subagents.md, surfaces/mcp.md |
| Persistent project fact (build cmd, architecture note) | `CLAUDE.md` at project root | Loaded at session start | surfaces/memory.md |
| Persistent user fact (personal style, workflow prefs) | `~/.claude/CLAUDE.md` | Applies everywhere | surfaces/memory.md |
| Personal project preferences not in VCS | `./CLAUDE.local.md` | Gitignored | surfaces/memory.md |
| Fact scoped to specific file paths | `.claude/rules/*.md` with `paths:` frontmatter | Loads only when matching files open | surfaces/memory.md |
| Organization-wide policy | Managed `CLAUDE.md` + managed `settings.json` | Can't be overridden | surfaces/memory.md, surfaces/settings.md |
| Learnings Claude accumulates itself | Auto-memory (`~/.claude/projects/<p>/memory/MEMORY.md`) | Claude decides what to save | surfaces/memory.md |
| Project permission allowlist | `.claude/settings.json` → `permissions.allow` | Shared via VCS | surfaces/settings.md |
| Personal permission allowlist | `.claude/settings.local.json` | Gitignored | surfaces/settings.md |
| User-wide permission allowlist | `~/.claude/settings.json` | Every project | surfaces/settings.md |
| Enterprise-enforced permissions | Managed settings (MDM, file-based, or server-managed) | Can't be overridden | surfaces/settings.md |
| Ship skills+agents+hooks+MCP as a bundle to a team | Plugin (`.claude-plugin/plugin.json`) | Marketplace distribution, versioned | surfaces/plugins.md |
| Ship a single custom prompt to a team | Plugin with just a `skills/` directory | Namespaces prevent conflicts | surfaces/plugins.md |
| Build a standalone agent in Python/TS | Agent SDK | Same tools/loop as CLI | surfaces/agent-sdk.md |
| Run Claude Code in CI/CD | Agent SDK (non-interactive) | Programmable, scripted | surfaces/agent-sdk.md |
| Interactive coding session at desk | Terminal CLI or VS Code extension | Session history shared | surfaces/ide-integrations.md |
| Visual diff review | VS Code / JetBrains extension | Native diff viewer | surfaces/ide-integrations.md |
| Customize keyboard shortcuts | `~/.claude/keybindings.json` | Hot-reloaded | surfaces/keybindings.md |
| Re-bind Ctrl+C | Can't — reserved | — | surfaces/keybindings.md |
| Run a prompt every 5 minutes while session open | `/loop 5m <prompt>` | Session-scoped, 7-day expiry | surfaces/background-tasks.md |
| Run a prompt on cron even when session closed | `/schedule` (Routines, cloud) or Desktop scheduled tasks | Durable | surfaces/background-tasks.md |
| Remind myself at 3pm to push branch | Natural language one-shot (Claude creates a `CronCreate` job) | Session-scoped | surfaces/background-tasks.md |
| Poll for dynamic status (e.g. build finishing) | `/loop <prompt>` with no interval | Claude self-paces | surfaces/background-tasks.md |
| Watch a background script | `Monitor` tool or `FileChanged` hook | Event-driven, token-efficient | surfaces/background-tasks.md |

## Commonly confused pairs

### Skill vs slash command

**Claim:** "Slash commands and skills are different things."
**Reality:** Custom slash commands have been merged into skills. A
`.claude/commands/deploy.md` still works, but a skill at
`.claude/skills/deploy/SKILL.md` is the modern equivalent with richer
features. Built-in slash commands (`/help`, `/compact`, `/doctor`, etc.)
are different — those are hard-coded CLI behavior. Bundled skills like
`/simplify`, `/batch`, `/debug`, `/loop`, `/claude-api` are ordinary skills
that ship with Claude Code.

Pick a skill over a legacy command file unless you have a reason not to.

### Skill vs memory (CLAUDE.md)

**Claim:** "CLAUDE.md is for long instructions; skills are for short ones."
**Reality:** The split is about **when it loads**:

- CLAUDE.md: **always** in context. Use for facts Claude must always know
  (build commands, coding standards, architectural rules).
- Skills: description always in context; body loads only when relevant.
  Use for **procedures** and **workflows** that matter only sometimes.

Rule of thumb from the docs: "If an entry is a multi-step procedure or only
matters for one part of the codebase, move it to a skill or a path-scoped
rule instead" of CLAUDE.md.

### Hook vs memory (the classic trap)

**Claim:** "Add this to CLAUDE.md so Claude always does X."
**Reality:** CLAUDE.md is **context**, not enforcement. Claude reads it and
tries to follow it, but compliance isn't guaranteed. For anything that must
happen deterministically ("always run the linter after every edit", "block
writes to `.env`"), use a hook. The `update-config` skill is the doer for
this.

If the user asks for "from now on, every time X, do Y", the correct surface is
a hook in `settings.json`, not a memory addition. Memory cannot fulfill
that contract.

### Subagent vs skill

**Claim:** "I want to delegate X, so I need a subagent."
**Reality:** Ask first: does X need its own context window? If yes, subagent.
If no, skill. Subagents help when the work produces verbose output you don't
need back (tests, logs, file contents), or when tool restrictions must be
tighter than the main conversation. Skills are better when the work needs
back-and-forth with the main context.

A skill with `context: fork` is a skill that runs like a subagent for a
one-shot task — useful when you've written a deterministic procedure and
just want to offload its execution.

A subagent with `skills:` preloads skill content into the agent's context at
startup — useful when the agent needs domain references to do its work.

### MCP tool vs subagent

**Claim:** "I need Claude to search my company wiki — should I build a
subagent or an MCP server?"
**Reality:**

- MCP server — if the capability is **reusable** (any agent or session can
  use the same search tool) and the integration is about **accessing
  external data**. Tools are atomic and composable.
- Subagent — if the capability is **a pattern of Claude behavior** (e.g.,
  a search-synthesize-report pipeline with specific prompting). Subagents
  are about behavioral specialization; MCPs are about tool access.

Often you want both: an MCP server that exposes the tool, and a subagent
whose system prompt tells Claude how to use that tool.

### Settings.json vs CLAUDE.md

**Claim:** "Both configure Claude Code, so they overlap."
**Reality:** They don't overlap — each handles distinct concerns:

- `settings.json` — **technical enforcement**: permissions, env vars, hooks,
  model, sandbox, attribution. Applied by the harness, non-negotiable.
- `CLAUDE.md` — **behavioral guidance**: instructions, rules, conventions.
  Delivered as a user message; Claude may still drift.

The docs explicitly say "Use settings for technical enforcement and
CLAUDE.md for behavioral guidance."

### Permission rule vs PreToolUse hook

**Claim:** "Use a permission rule for simple blocks, a hook for complex ones."
**Reality:** Largely correct, with two nuances:

- A `permissions.deny` rule **always** blocks, regardless of what a hook
  returns. Start here for static policy.
- A `PreToolUse` hook can decide dynamically (look at the command, the cwd,
  recent history) and can also transform the tool input before execution.
- A hook exit code 2 blocks the call **before** permission rules are
  evaluated, so a hook can preempt an allow rule.

Use permission rules for static include/exclude lists. Use hooks for
validation that needs to read the tool input at runtime.

### Plugin vs standalone skill

**Claim:** "My skill is useful — should I package it as a plugin?"
**Reality:** Package as a plugin **only when sharing**. For personal or
project-specific workflows, keep it in `.claude/skills/`. Plugin skills are
always namespaced (`/plugin-name:skill-name`), which makes them a bit more
verbose to invoke. The docs recommend: start standalone, convert when ready
to share.

### Agent SDK vs Claude Code CLI

**Claim:** "Agent SDK replaces the CLI."
**Reality:** Same engine, different interface. Use the CLI for interactive
work and the SDK for CI/CD, production automation, or custom apps.
Third-party products built on the SDK **may not use claude.ai login** — only
API key auth. CLI sessions and SDK agents can share `.claude/` config (skills,
commands, CLAUDE.md).

### Built-in MCP server (`ide`) vs user-configured MCP

The VS Code extension runs a local MCP server named `ide` that the CLI
connects to automatically. It exposes `mcp__ide__getDiagnostics` (read) and
`mcp__ide__executeCode` (Jupyter, always user-confirmed). It's hidden from
`/mcp` but visible to `PreToolUse` hooks that allowlist MCP tools. Nothing
to configure; unlike user-added MCPs, it's not listed in `.mcp.json`.

## Surface at each level of the trust/scope axis

| Scope | Settings file | Where it wins |
|:--|:--|:--|
| Managed | MDM / registry / `/Library/Application Support/ClaudeCode/managed-settings.json` | Always, cannot be overridden |
| Command line | `--` flags | Per session |
| Local | `.claude/settings.local.json` | Gitignored personal override |
| Project | `.claude/settings.json` | Checked into VCS, shared |
| User | `~/.claude/settings.json` | Your default across projects |

Arrays (like `permissions.allow`) **merge** across scopes. Scalars (like
`model`) take the higher-precedence value.

## Doer skills — delegate actual edits here

claude-expert is the reference. For edits, delegate:

- `update-config` — write/edit `settings.json`, add hooks, adjust permissions.
- `skills-manager` — author, update, archive skills (enforces non-redundancy).
- `keybindings-help` — edit `~/.claude/keybindings.json`.
- `mcp-doctor` — check MCP server health.
- `fewer-permission-prompts` — generate an allowlist from transcripts.
- `claude-code-core-instructions` — core operating rules.

## SDK vs CLI — when to pick which

| Situation | Pick |
|:--|:--|
| Interactive development | CLI |
| One-off task | CLI |
| CI/CD pipeline | Agent SDK |
| Production automation | Agent SDK |
| Programmatic control / custom app | Agent SDK |
| In-process MCP tools (no subprocess) | Agent SDK + `create_sdk_mcp_server` |
| Need `claude.ai` login in a product | CLI only (SDK needs API key) |

CLI and SDK share the same engine and config. A workflow built in the CLI
translates directly to the SDK. SDK agents can read `.claude/` skills,
memory, and plugins by default; set `setting_sources` in `ClaudeAgentOptions`
to isolate for CI.

## ScheduleWakeup vs CronCreate vs /loop skill

| Tool | Use when | Notes |
|:--|:--|:--|
| `/loop <prompt>` (no interval) | Self-pacing poll during a session | ScheduleWakeup picks ~4-min delays to stay in 5-min prompt cache |
| `/loop 4m <prompt>` | Fixed short interval inside cache window | Direct CronCreate under the hood |
| `CronCreate` (explicit) | You need an explicit cron expression or one-shot reminder | Same 7-day expiry as `/loop` |
| `/schedule` (Routines) | Must survive machine off | Cloud-run, minimum 1-hour interval |
| Desktop scheduled tasks | Local files, survive session close | Minimum 1 minute |

Shell `sleep 300` in a polling loop busts the 5-minute prompt cache TTL —
use `/loop` or `Monitor` instead.

## Versions / gotchas worth remembering

- **Opus 4.7** requires Agent SDK v0.2.111+. `thinking.type.enabled` errors
  usually mean the SDK is too old.
- **Custom commands merged into skills** as of the commands/skills doc
  reorganization — both paths still function.
- **`pr-comments` command removed** in v2.1.91. Ask Claude directly.
- **`/vim` removed** in v2.1.92. Use `/config` → Editor mode.
- **Agent tool renamed from Task** in v2.1.63. `Task(...)` still works as alias.
- **Seven-day expiry** on all recurring `/loop` / CronCreate tasks.
- **`--add-dir`** grants file access but not config discovery — except for
  `.claude/skills/`, which IS loaded from added dirs (skills are the
  exception).
- **SSE MCP transport deprecated** — prefer HTTP.
- **`autoMemoryDirectory`** accepted only from user/local/policy settings,
  NOT project settings. Prevents a shared repo from redirecting memory
  writes to sensitive paths.
