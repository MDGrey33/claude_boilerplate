<!-- AUTO-UPDATED FILE — a periodic claude-expert-freshness task appends ADDITIVE
     deltas here and bumps the freshness date below. Decision-impacting changes are
     NEVER auto-applied here; they are written as a proposal to the staging dir
     (resolve via $CLAUDE_EXPERT_STAGING → a ./.claude-expert.staging file →
     default ./.staging/ under this skill) for a human to review. See self-update.md.
     Hand-edit freely; keep newest deltas on top. -->

# Latest & best practices

**Freshness: 2026-06-07.** Companion to [SKILL.md](SKILL.md). Live docs at
code.claude.com/docs win on any conflict.

## Latest & best practices (as of 2026-06)

*Deltas since the 2026-04-20 baseline. Live docs win on conflict.*

### Reliability & autonomy (added 2026-06-07)
- **`fallbackModel` setting** (v2.1.166; partial since v2.1.152): configure **up to three** fallback models tried in order when the primary is overloaded/unavailable; `--fallback-model` now also applies to **interactive** sessions (previously print-mode only), and Claude Code retries a turn once on the fallback when the API returns an unexpected non-retryable error (auth / rate-limit / request-size / transport errors still surface immediately). ([changelog v2.1.166](https://code.claude.com/docs/en/changelog))
- **Cross-session messaging hardened** (v2.1.166): messages relayed via `SendMessage` from *other* Claude sessions no longer carry user authority — receivers **refuse relayed permission requests**, and `auto` mode blocks them. Treat an inter-session message as untrusted input, not as the operator speaking. ([changelog v2.1.166](https://code.claude.com/docs/en/changelog))
- **`auto` mode on cloud providers** (v2.1.158): now available on **Bedrock, Vertex, and Foundry** for Opus 4.7 and Opus 4.8 — opt in with `CLAUDE_CODE_ENABLE_AUTO_MODE=1`. (Earlier docs implied auto/Routines were gated off under those auth paths; auto mode no longer is.) ([changelog v2.1.158](https://code.claude.com/docs/en/changelog))

### Surfaces & cost visibility (added 2026-06-07)
- **Plugins auto-load from `.claude/skills/`** (v2.1.157): a plugin placed in a `.claude/skills` directory is now loaded **with no marketplace required**, and `claude plugin init <name>` scaffolds a new plugin straight into `.claude/skills`. Blurs the standalone↔plugin line — you can iterate on a plugin locally before ever publishing a marketplace. *(Surface-choice impact on decision-fork (d) is gated, not auto-applied — see the 2026-06-07 staging report.)* ([changelog v2.1.157](https://code.claude.com/docs/en/changelog))
- **`/usage` per-category breakdown** (v2.1.149): `/usage` now itemizes what's driving your limits — **skills, subagents, plugins, and per-MCP-server cost** — the missing piece for a cost/context audit. ("extra usage" was renamed to **usage credits**; `/extra-usage` → `/usage-credits`, v2.1.144.) ([changelog v2.1.149](https://code.claude.com/docs/en/changelog))
- **`reloadSkills` / `/reload-skills`** (v2.1.152): a `SessionStart` hook can return `reloadSkills: true` (top-level, not under `hookSpecificOutput`) to re-scan skill dirs so a skill the hook just installed is usable **in the same session**; `/reload-skills` does the same on demand without a restart. (Complements the `sessionTitle` SessionStart output already noted below.) ([changelog v2.1.152](https://code.claude.com/docs/en/changelog))
- **Worktree controls**: `worktree.baseRef` (`fresh`|`head`, v2.1.133) chooses whether `--worktree` / `EnterWorktree` / agent-isolation worktrees branch from `origin/<default>` or local `HEAD` (default `fresh` keeps unpushed commits out); `worktree.bgIsolation: "none"` (v2.1.143) lets background sessions edit the working copy directly without `EnterWorktree`; `EnterWorktree` can switch between Claude-managed worktrees mid-session (v2.1.157). ([changelog](https://code.claude.com/docs/en/changelog))

### New extension surfaces (now seven, not five)
- **Channels** (research preview, shipped 2026-03-20, `--channels` flag): MCP servers that *push* external events (Telegram → Discord → iMessage) **into** a running session; Claude replies via `reply`/`react`/`edit_message`. Being in `.mcp.json` is not enough — a server must also be named in `--channels`; every channel keeps a sender allowlist and silently drops unapproved IDs. This is the event-driven primitive: use it **instead of polling**. ([docs](https://code.claude.com/docs/en/channels))
- **LSP servers in plugins**: plugins can ship `.lsp.json` (Language Server Protocol) so the built-in LSP tool gives jump-to-definition, find-references, and post-edit type errors. Official marketplace ships Python/TS/Rust LSP plugins; `claude plugin details` shows which LSP servers a plugin provides (v2.1.142/144). ([docs](https://code.claude.com/docs/en/plugins))
- **`/goal`** (v2.1.139): set a completion condition and Claude keeps working turn-after-turn until it's met. The until-done counterpart to `/loop`'s on-interval. ([changelog v2.1.139](https://code.claude.com/docs/en/scheduled-tasks))
- **Dynamic workflows / `ultracode`** (research preview, v2.1.154, 2026-05-28): fans tens-to-hundreds of subagents with adversarial cross-verification. The bare word `workflow` no longer triggers it (renamed to `ultracode` in v2.1.154; v2.1.166 added a `/config` toggle). Consumes meaningfully more usage; prompts before first run. ([blog](https://claude.com/blog/introducing-dynamic-workflows-in-claude-code))

### Permission-model overhaul
- **`auto` mode** (research preview, 2026-03-24) is now the recommended autonomy path, **replacing `--dangerously-skip-permissions`**. A Sonnet-4.6 transcript classifier reviews each tool call before execution (2-stage: fast filter → chain-of-thought, ~0.4% false-positive) plus a prompt-injection probe on tool outputs. 20+ `hard_deny` rules under `settings.autoMode.hard_deny` (v2.1.139). Honest limit: ~17% false-negative on overeager actions — not a substitute for human review on prod/infra. ([engineering writeup](https://www.anthropic.com/engineering/claude-code-auto-mode), [permission-modes](https://code.claude.com/docs/en/permission-modes))
- **`dontAsk` mode**: auto-*denies* anything not pre-approved (inverse of bypass) — for locked-down/CI runs. ([permissions](https://code.claude.com/docs/en/permissions))
- **`Agent(<name>)` permission rules**: `Agent(Explore)`, `Agent(Plan)`, `Agent(my-custom-agent)` can go in deny lists / `--disallowedTools` to disable specific subagents. `subagent_type` matching is now case- and separator-insensitive. ([sub-agents](https://code.claude.com/docs/en/sub-agents))

### Surface-merge & frontmatter
- **Slash commands merged into Skills** (v2.1.3): "Merged slash commands and skills, simplifying the mental model with no change in behavior." `.claude/commands/deploy.md` and `.claude/skills/deploy/SKILL.md` both create `/deploy`; on a name clash the **skill wins**; `slash-commands` docs now redirect to the skills page. ([skills](https://code.claude.com/docs/en/skills))
- **Skill frontmatter is now a superset**: `disable-model-invocation`, `user-invocable` (hyphen, not underscore), `allowed-tools`/`disallowed-tools` (kebab-case), `model`, `effort` (low→max), `context: fork` + `agent:` (run a skill *as* a subagent), `skills:` preload (a subagent injects full skill bodies), `paths:` globs to gate auto-activation. ([skills frontmatter](https://code.claude.com/docs/en/skills)) *(Note: older skills may still use the legacy `user_invocable:` underscore, which keeps working; both forms are accepted, but the docs now prefer the hyphen.)*
- **Skill-listing budget is configurable**: description+`when_to_use` truncated at 1,536 chars; listing budget scales at ~1% of context window, raisable via `skillListingBudgetFraction` / `SLASH_COMMAND_TOOL_CHAR_BUDGET`; least-invoked descriptions drop first; `/doctor` reports overflow. Front-load the key use case — truncation cuts from the back. ([skills](https://code.claude.com/docs/en/skills))

### Hooks (now ~29 events, 5 handler types)
- Event surface grew far past the original 9: added `PostCompact`, `PostToolUseFailure`, `PostToolBatch`, `PermissionRequest`/`PermissionDenied`, `SubagentStart`, `TaskCreated`/`TaskCompleted`, `StopFailure`, `MessageDisplay`, `Setup`, `UserPromptExpansion`, `Elicitation`/`ElicitationResult`, `ConfigChange`, `CwdChanged`, `WorktreeCreate`/`Remove`, `TeammateIdle`, `InstructionsLoaded`. ([hooks-guide](https://code.claude.com/docs/en/hooks-guide#how-hooks-work))
- Five handler types: `command`, `http`, `mcp_tool`, `prompt` (single-turn Haiku judge), `agent` (multi-turn verifier, experimental). ([hooks-guide](https://code.claude.com/docs/en/hooks-guide#prompt-based-hooks))
- New controls: `if` arg-level filter (v2.1.85+, tool events only, **fails open**); `async`/`asyncRewake` for slow hooks; `args: string[]` exec-form (no shell); `continueOnBlock` for PostToolUse; Stop/SubagentStop `additionalContext`; SessionStart `sessionTitle`; `$CLAUDE_EFFORT`; 8-consecutive-block Stop-hook cap (override `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`). ([hooks-guide](https://code.claude.com/docs/en/hooks-guide#limitations))

### Scheduling consolidated to three surfaces + two adjacents
- Docs now present exactly three scheduling surfaces in one comparison table (repeated verbatim on `/scheduled-tasks`, `/routines`, `/desktop-scheduled-tasks`): **Cloud Routines**, **Desktop scheduled tasks**, **`/loop`**. ([scheduled-tasks](https://code.claude.com/docs/en/scheduled-tasks))
- **Routines** (cloud `/schedule`, launched 2026-04-14) run on Anthropic infra, survive machine-off, draw down subscription usage with a daily cap (Pro 5 / Max 15 / Team-Enterprise 25), min interval **1 hour**, 3 trigger types (Scheduled/API/GitHub). `/schedule` is hidden under API-key/Bedrock/Vertex/Foundry auth or CLI < v2.1.81. ([routines](https://code.claude.com/docs/en/routines))
- **Desktop scheduled tasks** persist on disk as `~/.claude/scheduled-tasks/<kebab-name>/SKILL.md`, min interval 1 minute, full local-file + MCP access, can self-reschedule via the `update_scheduled_task` MCP tool. The CronCreate `durable` flag is an internal/transitional path — the *documented* durable-local surface is Desktop tasks. ([desktop-scheduled-tasks](https://code.claude.com/docs/en/desktop-scheduled-tasks))
- Adjacent primitives docs steer you to *instead of polling*: **`/goal`** (until-done) and **Channels** (event-driven). ([channels](https://code.claude.com/docs/en/channels))

### Plugins & enterprise lockdown
- `claude plugin details <name>` shows component inventory + projected per-session token cost; `defaultEnabled: false`; `/plugin list --enabled/--disabled`; dependency-aware enable/disable; `skipLfs`; marketplace `remove --scope`. ([changelog v2.1.144-163](https://code.claude.com/docs/en/discover-plugins))
- Managed lockdown: `strictPluginOnlyCustomization` (skills/agents/hooks/MCP may come *only* from plugins or managed settings), `allowManagedHooksOnly`, `allowManagedMcpServersOnly`, `requiredMinimumVersion`/`requiredMaximumVersion` (v2.1.163), `disableAutoMode`, `disableBypassPermissionsMode`. ([permissions managed settings](https://code.claude.com/docs/en/permissions))
- MCP: HTTP transport recommended, **SSE deprecated**; glob deny rules in the tool-name position (`"*"` denies **all tools**, not just MCP tools; allow rules reject non-MCP globs; unknown tool names in deny rules warn at startup — v2.1.166); reserved `workspace` server name; credential redaction. ([mcp](https://code.claude.com/docs/en/mcp), [permissions](https://code.claude.com/docs/en/permissions))
