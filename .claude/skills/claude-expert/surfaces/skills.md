# Skills — deep reference

Source: https://code.claude.com/docs/en/skills

## What a skill is

A skill is a directory containing a `SKILL.md` file with YAML frontmatter and
markdown body. Claude adds it to its toolkit. A skill is **invoked** either:

- automatically by Claude when the description matches the conversation, or
- explicitly by typing `/<skill-name>` (if `user-invocable` is true, the default).

Custom slash commands are now skills. `.claude/commands/deploy.md` and
`.claude/skills/deploy/SKILL.md` both create `/deploy`. The skill form is
preferred because it supports a directory for supporting files and more
frontmatter fields.

Bundled skills ship with Claude Code: `/simplify`, `/batch`, `/debug`, `/loop`,
`/claude-api`, `/fewer-permission-prompts`.

Skills follow the open Agent Skills standard (agentskills.io). Claude Code
extends it with invocation control, subagent execution, and dynamic context
injection.

## Where they live

| Location   | Path                                     | Scope                          |
|:-----------|:-----------------------------------------|:-------------------------------|
| Enterprise | via managed settings                     | All users in the organization  |
| Personal   | `~/.claude/skills/<name>/SKILL.md`       | All your projects              |
| Project    | `.claude/skills/<name>/SKILL.md`         | This project only              |
| Plugin    | `<plugin>/skills/<name>/SKILL.md`         | Where the plugin is enabled    |

Precedence when names collide: **enterprise > personal > project**. Plugin
skills always use `plugin-name:skill-name` namespace so they can't conflict.
If a skill and a legacy `.claude/commands/<name>.md` share a name, the skill
wins.

Live change detection: edits reload within the session. Creating a top-level
skills directory that didn't exist at session start requires a restart.

Nested discovery: `.claude/skills/` under a subdirectory is discovered when
Claude works with files there (monorepo support). `--add-dir` also loads
skills as an exception to the rule that added directories don't load config.

## SKILL.md frontmatter

```yaml
---
name: my-skill
description: What this skill does and when to use it
disable-model-invocation: true
allowed-tools: Read Grep
---

Your skill instructions here...
```

All fields are optional. Only `description` is recommended.

| Field | Required | Description |
|:--|:--|:--|
| `name` | No | Display name. Lowercase letters, numbers, hyphens. Max 64 chars. Defaults to dir name. |
| `description` | Recommended | What it does, when to use it. Combined with `when_to_use`, capped at 1,536 chars in the skill listing. Front-load the use case. |
| `when_to_use` | No | Extra trigger phrases/examples. Appended to `description`. |
| `argument-hint` | No | Hint shown during autocomplete (e.g. `[issue-number]`). |
| `disable-model-invocation` | No | `true` = only the user can invoke (`/name`). Default `false`. |
| `user-invocable` | No | `false` = hide from the `/` menu. Default `true`. |
| `allowed-tools` | No | Tools pre-approved while the skill is active. Space-separated or YAML list. Does NOT restrict — only pre-approves. |
| `model` | No | Model when this skill is active. |
| `effort` | No | `low`/`medium`/`high`/`xhigh`/`max`. Overrides session effort. |
| `context` | No | `fork` = run the skill as a subagent. |
| `agent` | No | Subagent type to use when `context: fork` (default `general-purpose`). |
| `hooks` | No | Hooks scoped to this skill's lifecycle. |
| `paths` | No | Glob patterns limiting auto-activation to matching files. |
| `shell` | No | `bash` (default) or `powershell`. |

## Body

Anything goes. The full body loads into context when invoked and stays for the
session. Claude does not re-read the file on later turns — write instructions
as standing rules, not one-time steps.

## Variables

| Variable | Expands to |
|:--|:--|
| `$ARGUMENTS` | Full arg string as typed |
| `$ARGUMENTS[N]` or `$N` | The N-th positional arg (0-indexed), shell-quoted |
| `${CLAUDE_SESSION_ID}` | Current session ID |
| `${CLAUDE_SKILL_DIR}` | Directory of the skill's SKILL.md (useful for referencing bundled scripts regardless of cwd) |

Args with no `$ARGUMENTS` placeholder are still appended as
`ARGUMENTS: <value>` so Claude sees them.

## Invocation control

| Frontmatter | User can invoke | Claude can invoke | Context loading |
|:--|:--|:--|:--|
| (default) | Yes | Yes | Description always loaded; body on invoke |
| `disable-model-invocation: true` | Yes | No | Description NOT loaded; body loads on user invoke |
| `user-invocable: false` | No | Yes | Description always loaded; body loads on Claude invoke |

`user-invocable: false` only hides from the `/` menu; it doesn't block the
`Skill` tool. To block programmatic invocation, use `disable-model-invocation`.

## `allowed-tools` — pre-approves, doesn't restrict

`allowed-tools: Bash(git add *) Bash(git commit *)` lets Claude run those
commands without prompting while the skill is active. It does NOT prevent
Claude from using other tools. To restrict, add deny rules in
`permissions.deny` in settings.

## Supporting files (progressive disclosure)

Skills can include any number of files in their directory:

```
my-skill/
├── SKILL.md         # required - entry point
├── reference.md     # detailed doc - loaded on demand
├── examples.md      # examples - loaded on demand
└── scripts/
    └── helper.py    # executed, not loaded
```

Reference them from SKILL.md so Claude knows what each contains. Official
tip: keep SKILL.md under 500 lines and put bulky reference material in
separate files.

## Dynamic context injection

```` ```! ```` (fenced block) or `` !`<command>` `` (inline) runs shell
commands BEFORE the skill body is sent to Claude. Output replaces the
placeholder. Useful for PR summaries, env info, etc.

Disable via `disableSkillShellExecution: true` in settings.

## Running in a subagent (`context: fork`)

Adds isolation: the skill body becomes the system prompt for a subagent of
the specified `agent` type. Does NOT have access to the parent conversation.
Only makes sense for task-driven skills with explicit instructions, not
reference-style skills.

| Approach | System prompt | Task | Also loads |
|:--|:--|:--|:--|
| Skill with `context: fork` | From agent type | SKILL.md content | CLAUDE.md |
| Subagent with `skills:` field | Subagent markdown body | Claude's delegation | Preloaded skills + CLAUDE.md |

## Permission control

- **Disable all skills:** deny `Skill` in `/permissions`.
- **Allow specific:** `Skill(commit)`, `Skill(review-pr *)`.
- **Deny specific:** `Skill(deploy *)`.
- **Hide from Claude:** `disable-model-invocation: true` in frontmatter.

Syntax: `Skill(name)` exact; `Skill(name *)` prefix with args.

## Context lifecycle

- Description loads at session start. Full body loads on invoke.
- Budget: dynamically 1% of context window, fallback 8,000 chars. Override
  with `SLASH_COMMAND_TOOL_CHAR_BUDGET`. Per-entry `description + when_to_use`
  capped at 1,536 chars.
- After compaction: most recent invocation of each skill re-attached, first
  5,000 tokens kept. Combined budget 25,000 tokens. Oldest invocations drop
  if budget fills.
- If a skill seems to stop influencing behavior, re-invoke it; the content is
  usually still there, Claude just chose other approaches.

## Gotchas

- Putting many skills with long descriptions slowly starves the listing
  budget. Trim `description` aggressively if keywords get cut. Check
  `/skills`.
- `allowed-tools` does NOT restrict; it pre-approves. For restriction use
  permission deny rules.
- In a regular session, a skill description is always in context; in a
  subagent with preloaded skills, the entire skill body is injected at
  startup.
- Skill directories under `~/.claude/skills/` must exist at session start
  for Claude Code to watch them (per docs). New top-level dirs need restart;
  files within watched dirs are picked up live.
- If a skill shares a name with a legacy command in `.claude/commands/`, the
  skill takes precedence.

## Disambiguation

- **Skill vs hook**: skills are prompts/instructions Claude follows; hooks
  are deterministic shell/HTTP/prompt callbacks the harness runs. If you
  need guaranteed behavior, use a hook.
- **Skill vs CLAUDE.md**: CLAUDE.md is always in context; skill bodies load
  only when invoked. Use CLAUDE.md for facts always true; use skills for
  procedures that matter sometimes.
- **Skill vs subagent**: skills run in the main conversation context;
  subagents run isolated. Use subagents when the work generates noise you
  don't want back in main context.
- **Skill vs MCP**: skills are Claude behavior patterns; MCPs are external
  tools. Often pair them.
- **Skill vs slash command**: functionally merged. `.claude/skills/foo/SKILL.md`
  is the modern way; `.claude/commands/foo.md` still works.

## Minimal worked example

Personal skill that runs a read-only review of current changes.

```
~/.claude/skills/quick-review/SKILL.md
```

```yaml
---
name: quick-review
description: Quickly review the uncommitted diff for obvious issues. Use when asked to "review my changes" or before committing.
allowed-tools: Bash(git diff *) Bash(git status *) Read Grep
---

Review the current changes:

1. Run `git status` to see what changed.
2. Run `git diff` to read the actual diff.
3. Look for: obvious bugs, missing error handling, forgotten debug prints,
   leaked secrets, TODO comments that shouldn't ship.
4. Report findings in priority order. No code rewrites unless asked.
```

Invocable as `/quick-review` or triggered automatically when the user says
"review my changes" — the description front-loads that trigger.

## Trigger phrase engineering

Source: https://github.com/wshobson/agents (analysis of 184 agents)

The `description` field doubles as the semantic discovery hook. Claude
uses it to decide auto-activation. Effective patterns:

- **Action verb + domain + input/output:** "Generate React components from
  Figma designs with TypeScript types and CSS modules"
- **Front-load trigger phrases** — budget cuts strip from the back.
- **Include edge-case coverage:** "with error recovery", "supporting TypeScript"

Anti-patterns that never trigger:
- "Helps with coding tasks" — too generic, no semantic hooks
- "Makes things better" — no domain terms
- "Uses AST parsing" — describes implementation, not use case

## When to split a skill

Community rule of thumb (from wshobson/agents analysis):

- **Keep in one skill:** atomic capability, all instructions needed together,
  body under ~8,000 tokens.
- **Split into sibling files:** body over 10,000 tokens. Reference from
  SKILL.md so Claude knows where to find depth.
- **Split into multiple skills:** distinct phases (plan / execute / validate),
  optional advanced features rarely needed, clear domain boundaries
  (Python vs JavaScript, read-only vs write).
- **Bundle in a plugin:** skills share dependencies, compose naturally in
  workflows, or are ready to share.

## Troubleshooting

- **Skill not triggering:** description lacks the keywords the user says.
  Add more natural phrasings or `when_to_use` entries.
- **Skill triggers too often:** tighten the description and/or add
  `disable-model-invocation: true` for manual-only.
- **Description cut short:** listing budget exceeded. Trim text to 1,536
  chars and/or raise `SLASH_COMMAND_TOOL_CHAR_BUDGET`.
