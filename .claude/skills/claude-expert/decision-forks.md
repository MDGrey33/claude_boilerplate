# Decision forks — the load-bearing surface choices

> Companion to [SKILL.md](SKILL.md). These are the forks where picking the wrong
> surface costs the most. SKILL.md carries the one-line rules; this file carries
> the tables and failure modes. Live docs at code.claude.com/docs win on conflict.

## Decision forks — the load-bearing choices

These sharpen judgment, they aren't a checklist — see [reasoning.md](reasoning.md); when a case doesn't fit, reason from the tradeoff. Each fork is a strong default plus the failure mode it encodes. Forks (a), (d), (e) are heuristics — override with stated cause. Fork (b) is the exception: it carries invariant 3 (a guard that must survive an adversary is a harness mechanism), so keep it firm.

### (a) Skill ↔ Subagent — both directions

A **skill** runs *inline* in the main conversation (shared context, cheap, fast, stays resident all session). A **subagent** runs in a *fresh isolated context window* with its own system prompt, tools, model, and permissions, and returns only a ~1-2k-token summary ([sub-agents](https://code.claude.com/docs/en/sub-agents)).

| If the work is… | Use | Because |
|:--|:--|:--|
| A reusable playbook / checklist / reference you keep re-pasting | **Skill** | "Consider Skills when you want reusable prompts or workflows that run in the main conversation context rather than isolated subagent context." Cheapest, everything shares context. |
| Interactive / iterative / needs tight back-and-forth | **Skill** (or main thread) | Subagents start cold, can't do quick turns, and **cannot spawn subagents** — nested-delegation built as subagents breaks. |
| Verbose output you won't reference again (research, logs, test runs) | **Subagent** | Skill content enters the conversation as one message and **stays the whole session** — every turn re-pays those tokens. |
| Needs tool/permission restriction or a cheaper model | **Subagent** | Per-agent `tools`/`disallowedTools`/`model`/`permissionMode`. |
| Parallelizable independent units | **Subagent** (fan-out) | True parallelism + context isolation. |

**Failure mode → both directions:**
- *Subagent where a skill belongs* (iterative work): latency from cold-start context-gathering, no back-and-forth, nested-delegation breaks. A `context: fork` skill with only guidelines and no task returns nothing.
- *Skill where a subagent belongs* (high-volume work): verbose output permanently bloats the main window every turn.
- *Meta-failure*: spawning excessive subagents for trivial queries — coordination overhead with no payoff.

**They compose both ways:** a skill runs *in* a subagent via `context: fork` + `agent:`; a subagent *preloads* skills via its `skills:` field (injects full bodies, not just descriptions — except skills with `disable-model-invocation: true`). ([skills](https://code.claude.com/docs/en/skills), [sub-agents](https://code.claude.com/docs/en/sub-agents))

### (b) When a guard belongs in a PreToolUse DENY hook, NOT a skill or memory

**Rule: if the requirement is "X must NEVER happen, even if the model is talked into it," it is a `PreToolUse` deny hook — full stop.**

> "PreToolUse hooks fire before any permission-mode check. A hook that returns `permissionDecision:"deny"` blocks the tool even in `bypassPermissions` mode or with `--dangerously-skip-permissions`." ([hooks-and-permission-modes](https://code.claude.com/docs/en/hooks-guide#hooks-and-permission-modes))

| Surface | Enforcement strength |
|:--|:--|
| CLAUDE.md / auto-memory | **Guidance only** — context the model *may* follow; and it's the very thing bypass mode ignores. |
| Skill instruction | Guidance — same weakness; lives inside the model's reasoning. |
| `permissions.deny` rule | Hard, but bypassable by mode in some flows; static patterns only. |
| **PreToolUse deny hook** | **Deterministic harness-level enforcement** the model cannot talk past; survives bypass mode and `--dangerously-skip-permissions`. |

**Why memory cannot enforce it:** memory is *context*, and bypass/auto modes that you're guarding against are precisely the modes that skip the interactive prompt and discount that context. A deny hook is harness machinery, not a suggestion. Canonical patterns: `protect-files.sh` (deny edits to `.env`/`.git/`/lockfiles), `block-rm-rf.sh`. Caveat: the `if` arg filter is **best-effort and fails open** on `$()`/backticks/`$VAR`; for a hard guard do the real matching *inside* the deny script (canonicalize the command) and **fail closed** (deny if `jq` missing / JSON malformed). ([block-edits-to-protected-files](https://code.claude.com/docs/en/hooks-guide#block-edits-to-protected-files))

### (c) The "hook that hinders progress" anti-pattern — and how to avoid it

A hook that fires too broadly or runs too long stalls the agent. Avoid it with four levers:
1. **Scope tightly** — use `matcher` (tool name) *and* the `if` field (tool name + args, v2.1.85+, tool events only) so the hook process only spawns on real matches. An empty/`*`/omitted matcher fires on **every** occurrence — the over-eager default.
2. **Mind the fast-path timeouts** — `UserPromptSubmit` blocks model processing and drops to a 30s timeout; a stuck one stalls the session. Keep it trivial.
3. **Use `async`/`asyncRewake`** for slow work so Claude doesn't wait (asyncRewake wakes Claude on exit 2 with stderr as a system reminder).
4. **Respect the Stop-hook block cap** — a Stop hook returning block makes Claude keep working; after **8 consecutive blocks without progress** Claude Code overrides it. Parse `stop_hook_active` and exit 0 early so the hook doesn't re-trigger a continuation it already started. ([limitations](https://code.claude.com/docs/en/hooks-guide#limitations), [stop-hook-block-cap](https://code.claude.com/docs/en/hooks-guide#stop-hook-hits-the-block-cap))

### (d) When to package as a PLUGIN

**Default: standalone `.claude/` while you iterate; convert to a plugin once "share / version / reuse-across-projects" enters the picture — that's the line the cost of duplication crosses payoff.** ([plugins](https://code.claude.com/docs/en/plugins))

| Trigger | Surface |
|:--|:--|
| Single project, personal, experimenting, want short `/names` | **Standalone** `.claude/` files |
| Share with team/community, same skills/agents across many projects, want version control + easy updates, marketplace distribution | **Plugin** (namespaced `/plugin-name:skill`) |

Official workflow: "Start with standalone configuration in `.claude/` for quick iteration, then convert to a plugin when you're ready to share." Structural gotcha: **only `plugin.json` goes in `.claude-plugin/`**; every component dir (`skills/`, `agents/`, `hooks/`) lives at plugin **root** — the #1 "loads but components missing" bug.

### (e) `/loop` vs `/schedule` (Routines) vs a local scheduled task

**One-line decision (official):** "Use cloud tasks for work that should run reliably without your machine. Use Desktop tasks when you need access to local files and tools. Use `/loop` for quick polling during a session." ([scheduled-tasks](https://code.claude.com/docs/en/scheduled-tasks))

| If you need… | Use | Key constraint |
|:--|:--|:--|
| Quick polling while a session is open (deploy/CI watch) | **`/loop`** | Session-scoped; 7-day hard expiry; min 1 min |
| Work to run with the laptop closed | **`/schedule` (Routines, cloud)** | Min **1 hour**; daily cap; draws subscription usage; no local files |
| Recurring work that touches local files + MCP and survives session close | **Local Desktop scheduled task** (`~/.claude/scheduled-tasks/<name>/SKILL.md`) | Needs machine on + Desktop awake; min 1 min |
| React to an event, not poll | **Channels** | Push, not pull |
| Run until a condition is met (not on an interval) | **`/goal`** | Until-done, not recurring |

Anti-pattern: lean against putting a one-off ("remind me at 3pm") in a durable scheduled task — a one-shot cron / natural-language reminder that self-deletes fits better, because the durable surface then accrues dead entries.
