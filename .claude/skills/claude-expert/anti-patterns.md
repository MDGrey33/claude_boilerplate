# Anti-pattern catalog — wrong surface → right surface

> Illustrative common miscategorizations, not an exhaustive ban list — reason from the principle.
> These sharpen judgment, they aren't a checklist — see [reasoning.md](reasoning.md);
> when a case doesn't fit, reason from the tradeoff.
>
> Companion to [SKILL.md](SKILL.md). Distinct from [pitfalls.md](pitfalls.md):
> pitfalls.md = failure *modes* of a surface you've already chosen; this file =
> "you chose the wrong surface, here's the right one and why."

## Anti-pattern catalog — symptom → wrong surface → right surface → why

- **"I made a skill that spins off a long research/log dump and returns a summary"** → wrong: **skill** → right: **subagent** → a skill's body enters the conversation as one message and *persists the whole session*, re-paying tokens every turn; a subagent isolates the verbose work and returns only ~1-2k tokens. ([sub-agents](https://code.claude.com/docs/en/sub-agents))

- **"I made a subagent for a tight interactive checklist I run inline"** → wrong: **subagent** → right: **skill** → subagents start cold, can't do quick back-and-forth, and **cannot spawn subagents**, so nested-delegation built this way breaks. Skills share context and load on demand. ([skills](https://code.claude.com/docs/en/skills))

- **"I put 'never let Claude run `rm -rf /` or edit `.env`' in CLAUDE.md / a skill"** → wrong: **memory/skill** → right: **PreToolUse deny hook** → memory is guidance the model may ignore and is exactly what bypass/auto mode discounts; a `permissionDecision:"deny"` hook fires before the permission check and survives `--dangerously-skip-permissions`. ([hooks-and-permission-modes](https://code.claude.com/docs/en/hooks-guide#hooks-and-permission-modes))

- **"My hook validates every Bash call and the session feels sluggish / stuck"** → wrong: **broad blocking hook** (empty matcher, sync, on `UserPromptSubmit`) → right: **`if`-scoped + `async`/`asyncRewake` hook**, and parse `stop_hook_active` on Stop hooks → an omitted/`*` matcher fires on everything; `UserPromptSubmit` blocks model processing on a 30s clock; Stop hooks are force-overridden after 8 consecutive blocks. ([limitations](https://code.claude.com/docs/en/hooks-guide#limitations))

- **"I have a folder of skills + agents + a hook I keep copying between machines/projects"** → wrong: **scattered standalone `.claude/` files** → right: **plugin** (with a marketplace) → plugins give versioning, one-step updates, namespacing, and team distribution; standalone is for single-project iteration only. ([plugins](https://code.claude.com/docs/en/plugins))

- **"I run a `Bash` poll with `timeout: 600000` (or a shell `sleep 300` loop) to watch a deploy"** → wrong: **long-timeout Bash / sleep loop** → right: **`/loop`** (or the Monitor tool) → a foreground sleep ≥300s busts Claude Code's 5-min prompt-cache TTL and re-pays input tokens; `/loop` self-paces inside the cache window and the Monitor tool streams events instead of polling. ([scheduled-tasks](https://code.claude.com/docs/en/scheduled-tasks))

- **"I scheduled 'remind me at 3pm tomorrow' as a durable Desktop scheduled task / Routine"** → wrong: **durable scheduled task** → right: **one-shot cron / natural-language reminder** → one-offs self-delete after firing; standing infrastructure for a single event usually over-builds and clutters the registry — reach for it only when the event will recur. ([scheduled-tasks](https://code.claude.com/docs/en/scheduled-tasks))

- **"I want a recurring task that runs with my laptop closed, so I set up a `/loop`"** → wrong: **`/loop`** → right: **Routine (`/schedule`, cloud)** → `/loop` only fires while the session is open and hard-expires in 7 days; Routines run on Anthropic infra independent of the machine. ([routines](https://code.claude.com/docs/en/routines))

- **"I wrote a skill that pastes the same external-API instructions every time so Claude can hit GitHub/Slack/the DB"** → wrong: **skill** for the integration → right: **MCP server** (then a thin skill orchestrating it) → MCP gives reusable tools across clients/sessions; the 2026 pattern is one pinned MCP per external system + thin skills that drive it. ([mcp](https://code.claude.com/docs/en/mcp))

- **"I asked for `--dangerously-skip-permissions` to get autonomy"** → wrong: **bypass mode** → right: **`auto` mode** → auto keeps the classifier + injection probe + `hard_deny` guardrails; bypass disables them. ([auto-mode](https://www.anthropic.com/engineering/claude-code-auto-mode))

- **"A log file is huge so I deleted it / I added a field to a log other skills consume (e.g. a tool-event log that a pattern-miner reads)"** → wrong: **ad-hoc delete / blind schema change** → right: **route through a logs (lifecycle) manager** → it truncates-in-place (so the producing hook's open handle keeps writing) and coordinates any schema change with the producer + every consuming skill. (machine-local convention)
