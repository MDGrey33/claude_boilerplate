# pitfalls.md — common failure modes

Sources:
- https://github.com/wshobson/agents (documented trigger success rates)
- https://glama.ai/mcp/servers (configuration errors)
- https://code.claude.com/docs/en/hooks, /en/scheduled-tasks, /en/context-window

Each pitfall: one cause paragraph, one fix.

---

## Skill description too vague — never triggers

A skill with a description like "Helps with coding tasks" or "Improves code
quality" lacks semantic specificity. Claude's discovery uses the description
as a semantic match against the user's words. If the description contains no
domain terms, action verbs, or input/output signals, the skill is invisible
to automatic activation.

**Fix:** Rewrite to pattern "action verb + domain terms + input/output" —
e.g., "Generate React components from Figma designs with TypeScript types
and CSS modules". Front-load trigger phrases because budget cuts strip from
the back. Use `when_to_use:` for additional natural language phrasings. Check
`/skills` to confirm the description is not truncated.

---

## Hook loops — PostToolUse triggering itself

A `PostToolUse` hook that writes a file triggers another `PostToolUse` on
that write, which writes another file, recursing indefinitely. Shell hooks
don't have built-in depth tracking, so the loop runs until a timeout or OS
limit.

**Fix:** Make the hook target-specific — match only the tool names and file
patterns that should be watched, not `*`. If the hook itself must write a
file, use a sentinel file or env var to track depth. For SDK hooks (Python
callbacks), check a depth counter and return early if exceeded. Alternatively,
use `PostToolUse` only on specific tool names with narrow matchers, and
exclude writes that the hook itself produces.

---

## Subagent context blowout

A subagent given a large chunk of parent context — or a task that reads
many large files — can exhaust its own context window. Unlike the main
conversation, subagent context issues don't benefit from the parent's
compaction budget.

**Fix:** Pass only what the subagent needs: a clear task description,
specific file paths (not full contents), and acceptance criteria. Use
`Read` with `offset + limit` for large files. For very large side-tasks,
spawn multiple smaller subagents rather than one with a large context.
The parent conversation gets only the subagent's summary, so keep the
subagent scoped to one well-defined deliverable.

---

## Memory cannot enforce automation — only hooks can

Adding "from now on, always run the linter after every edit" to `CLAUDE.md`
creates an instruction Claude tries to follow, not a guarantee the harness
enforces. Claude may drift, skip it under distraction, or simply stop
reading the instruction after compaction.

**Fix:** Use a `PostToolUse` hook on `Edit|Write` to run the linter
deterministically. Hooks are code the harness executes regardless of what
Claude decides. CLAUDE.md is behavioral guidance — "Claude reads it and
tries to follow it" — not enforcement. Any requirement phrased as "every
time X happens, do Y" belongs in a hook, not memory. Delegate authoring
to the `update-config` skill.

---

## Permission allowlist over-granting

Granting `Bash(*)` or `mcp__server__*` to avoid permission prompts removes
all protection for that category. A broad allowlist means a malicious prompt
injection, runaway skill, or mistake by Claude can execute arbitrary commands
without any check.

**Fix:** Apply least-privilege rules. Start with the narrowest rule that
covers real usage: `Bash(npm run test)` instead of `Bash(*)`. Use the
`fewer-permission-prompts` bundled skill to build an allowlist from actual
transcripts — it auto-scans your history and proposes specific rules. Pair
broad allows with narrow denies: allow `Bash`, then deny `Bash(rm -rf *)`.
Review `/permissions` periodically and remove stale broad rules.

---

## Sleep >300s busts the prompt cache

Claude Code has a 5-minute prompt cache TTL on the Anthropic API. Any pause
longer than 300 seconds re-sends all input tokens at full cost. A common
mistake is writing a shell polling loop with `sleep 300` or scheduling a
CronCreate task every 6+ minutes. Each wake-up pays full input token costs,
eliminating the cost advantage of prompt caching.

**Fix:** Use `/loop` without an interval — ScheduleWakeup internally targets
~4-minute delays for stable tasks to stay within the cache window. If you
need a fixed interval, use `/loop 4m <prompt>`. Use the `Monitor` tool to
stream events from a background script instead of re-prompting. If you must
use CronCreate directly, stay within `*/4 * * * *` or shorter. The 78%
savings from prompt caching (100k-token doc reused 10x: ~$1.08 vs ~$5)
disappear the moment you exceed the 5-minute TTL.

---

## MCP stdio server inheriting a broken environment

Stdio MCP servers are launched as subprocesses. On macOS (launchd), the
working directory is often `/` and only a minimal PATH is inherited.
Relative paths in `args`, missing `API_KEY` variables, and npm packages
not on PATH all cause silent connection failures at startup.

**Fix:** Always use absolute paths in `args`. Explicitly declare every
required variable in the `env` block of the MCP server config — do not
rely on shell inheritance. Use `npx -y` (npm) or `uvx` (Python) to
auto-install packages. Check `/mcp` after connecting and run `mcp-doctor`
if a server shows as disconnected.

---

## Plugin subagent fields silently ignored

Plugin-provided subagents do not support `hooks`, `mcpServers`, or
`permissionMode` in their frontmatter. These fields are silently dropped
for security reasons. If you publish a plugin and users report that hooks
or per-agent MCP servers aren't running, this is why.

**Fix:** Copy the agent file from the plugin into `.claude/agents/` on the
user's machine. Standalone agent files (not plugin-provided) support all
frontmatter fields. Document this clearly in the plugin's README. If
`permissionMode` is critical, enforce it via a project-level `settings.json`
rule that applies to all subagents.
