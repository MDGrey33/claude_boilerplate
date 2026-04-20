# Context management — what loads when

Sources: https://code.claude.com/docs/en/context-window,
https://code.claude.com/docs/en/memory, https://code.claude.com/docs/en/skills,
https://code.claude.com/docs/en/how-claude-code-works.

Context is the budget every session competes for. This file summarizes
what consumes it and when.

## At session start

Loaded **in full**:
- Every CLAUDE.md walking up from cwd (project root + parents).
- Every `CLAUDE.local.md` alongside them (appended after CLAUDE.md in
  each dir).
- Unconditional `.claude/rules/*.md` (no `paths:` frontmatter).
- First 200 lines or 25 KB of `MEMORY.md` (auto-memory, if enabled).
- Managed CLAUDE.md if present.
- `@`-imported files (up to depth 5).

Loaded as **description only**:
- Every skill's `name` + `description` + `when_to_use` (combined cap 1,536
  chars per skill).
- Every subagent's `name` + `description`.
- Every tool's description (built-in + MCP + plugin).

NOT loaded yet:
- Skill bodies (only on invoke).
- Subagent system prompts (only when spawned).
- CLAUDE.md files in subdirectories (on demand when Claude reads files
  there).
- Path-scoped `.claude/rules/*.md` (when matching files open).
- Auto-memory topic files beyond `MEMORY.md` (on demand).

## Skill description budget

> "Skill descriptions are loaded into context so Claude knows what's
> available. All skill names are always included, but if you have many
> skills, descriptions are shortened to fit the character budget."

- Budget scales at 1% of context window.
- Fallback minimum 8,000 characters.
- Per-skill `description + when_to_use` capped at 1,536 chars.
- Override budget via env var `SLASH_COMMAND_TOOL_CHAR_BUDGET`.

If descriptions get cut, **the keywords Claude needs to match get
stripped first**. Front-load trigger phrases.

## Skill content lifecycle

Once invoked, a skill's body enters the conversation as a **single
message** and stays for the session. Claude does not re-read the skill
file on later turns.

### After `/compact`

Claude Code re-attaches the **most recent invocation** of each skill:
- Keeps first 5,000 tokens of each re-attached skill.
- Combined budget: 25,000 tokens shared across all re-attached skills.
- Fills from most recently invoked. Older invocations may drop entirely
  if budget fills.
- If a skill seems to stop influencing behavior, re-invoke it.

### Subagent context separately

Subagents have their **own context windows**. Main conversation compaction
doesn't affect them, and vice versa. Subagent transcripts persist
independently at
`~/.claude/projects/{project}/{sessionId}/subagents/agent-{id}.jsonl`.

Subagents auto-compact at ~95% by default. Override with
`CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=50`.

## CLAUDE.md lifecycle

- Project root CLAUDE.md **survives** `/compact` — re-injected.
- Nested CLAUDE.md files in subdirectories do NOT auto-re-inject. They
  reload next time Claude reads a file in that subdir.
- If an instruction disappeared after compaction, it was either
  conversation-only or in a nested CLAUDE.md that hasn't reloaded.
- Block HTML comments stripped before injection. Comments inside code
  blocks preserved.
- HTML comments still visible when you Read the file directly.

## Auto-memory lifecycle

- First 200 lines / 25 KB of `MEMORY.md` loaded at session start.
- Topic files (`debugging.md`, `patterns.md`) NOT loaded at start. Claude
  reads them on demand with its standard file tools when relevant.
- Claude writes to memory during sessions ("Writing memory" / "Recalled
  memory" indicators in the UI).
- Applies only to MEMORY.md, not to CLAUDE.md.

## What `/context` shows

Visualizes current context usage as a colored grid. Flags optimization
suggestions for context-heavy tools, memory bloat, capacity warnings.

## Commands that change context

- `/compact [instructions]` — summarize to free context. Optional
  instructions focus the summary.
- `/clear` / `/reset` / `/new` — new empty context (previous remains in
  `/resume`).
- `/branch` / `/fork` — branch conversation at this point; original
  preserved.
- `/rewind` / `/checkpoint` / `/undo` — rewind code or conversation to a
  previous point.

## Env vars that affect context

| Env var | Effect |
|:--|:--|
| `SLASH_COMMAND_TOOL_CHAR_BUDGET` | Override skill listing char budget |
| `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` | Lower compaction trigger from default ~95% |
| `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD` | Load CLAUDE.md from `--add-dir` directories |
| `CLAUDE_CODE_DISABLE_AUTO_MEMORY` | `=1` disables auto-memory |
| `CLAUDE_CODE_SKIP_PROMPT_HISTORY` | Disable session transcript writes |

Settings-based:
- `cleanupPeriodDays` — session retention (default 30).
- `autoMemoryEnabled` — toggle auto-memory.
- `autoMemoryDirectory` — override memory storage dir.

## Cache busting from sleep >300s

Source: https://code.claude.com/docs/en/scheduled-tasks (ScheduleWakeup behavior)

Claude Code's prompt cache has a **5-minute TTL**. Any gap longer than 300
seconds between requests re-pays full input token costs. Common mistakes:

- `sleep 300` in a shell polling loop — busts cache at every iteration.
- A CronCreate task at `*/6 * * * *` (6-minute interval) — always misses
  the cache window.

Remedies:
- Use `/loop` without an interval — ScheduleWakeup chooses ~4-minute delays
  to stay inside the TTL for stable tasks.
- Use the `Monitor` tool to stream events rather than re-prompting.
- Use `/loop 4m <prompt>` if you need a fixed interval.

## PreCompact hook

Use a `PreCompact` hook to save notes, trigger logging, or block automatic
compaction. See [surfaces/hooks.md](hooks.md) for the recipe. After compaction:

- Project-root CLAUDE.md re-attaches.
- Most recent invocation of each skill re-attaches (5,000 token cap each,
  25,000 token combined cap).

## Compaction specifics

Auto-compaction triggers at default ~95% of context window. After
compaction:
- A summary replaces the bulk of the conversation.
- Project-root CLAUDE.md re-attaches.
- Most recent invocation of each skill re-attaches (5,000 token cap each,
  combined 25,000 token cap, oldest dropped first).
- Subagent transcripts unaffected.
- Conversation-only instructions are lost unless promoted to CLAUDE.md or
  re-provided.

## Context-saving patterns

- Put repeatedly-referenced details in CLAUDE.md and supporting files in
  skills, not inline conversation.
- Use `disable-model-invocation: true` for skills you only manually
  invoke. Their descriptions are NOT loaded.
- Use subagents for verbose tasks — their output stays in their context.
- Use `context: fork` skills for one-shot tasks that would flood main
  context with output.
- Define MCP servers inline in a subagent (`mcpServers:`) to keep
  long-descripton servers out of main conversation.
- Use `.claude/rules/*.md` with `paths:` to load rules only when relevant
  files open.
- Use `@`-imports in CLAUDE.md rather than duplicating content.
- Break large CLAUDE.md (>200 lines) into imported files or rules.

## Inspection

- `/context` — visual grid of current usage.
- `/memory` — list loaded CLAUDE.md, CLAUDE.local.md, rules, and auto-memory.
- `/skills` — list available skills. Press `t` to sort by token count.
- `/status` — session panel, settings sources, origins.

## Gotchas

- **Skills don't re-read files on later turns.** Write guidance as standing
  instructions, not one-time steps.
- **Description budget cuts can strip match keywords.** Front-load them.
- **Nested CLAUDE.md files don't re-inject after /compact.** Move critical
  content to project-root CLAUDE.md.
- **Subagent context doesn't count against main budget.** That's why they
  help with large side-tasks.
- **Large skills invoked many times** share a 25,000-token compaction
  budget; older invocations drop.
- **If auto-memory `MEMORY.md` exceeds 200 lines / 25 KB**, Claude is
  supposed to curate by moving detail to topic files. Verify by opening
  `~/.claude/projects/<project>/memory/MEMORY.md`.

## Disambiguation

- **Context vs memory:** context is what's in the model's window right now;
  memory (CLAUDE.md + auto-memory) is what gets loaded into context at
  session start. Memory is the **source**; context is the **consumption**.
- **Compaction vs clear:** compaction summarizes; clear wipes. Clear loses
  skill invocations entirely.
- **Loaded in full vs on demand:** CLAUDE.md, unconditional rules, auto-memory
  index load in full. Skill bodies, subagent prompts, nested CLAUDE.md,
  path-scoped rules, auto-memory topics load on demand.
