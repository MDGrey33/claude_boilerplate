# Background and scheduled tasks

Sources:
- https://code.claude.com/docs/en/scheduled-tasks (`/loop`, CronCreate)
- https://code.claude.com/docs/en/routines (cloud routines)
- https://code.claude.com/docs/en/desktop-scheduled-tasks (desktop)

Requires Claude Code v2.1.72+.

## Three flavors of recurring work

|  | Cloud (Routines) | Desktop scheduled tasks | `/loop` (session-scoped) |
|:--|:--|:--|:--|
| Runs on | Anthropic cloud | Your machine | Your machine |
| Requires machine on | No | Yes | Yes |
| Requires open session | No | No | Yes (restored on `--resume` if unexpired) |
| Persistent | Yes | Yes | Until session ends (restored on resume within 7 days) |
| Local files | No (fresh clone) | Yes | Yes |
| MCP servers | Per-task connectors | Config files / connectors | Inherits session |
| Permission prompts | None (autonomous) | Configurable | Inherits session |
| Customizable schedule | Via `/schedule` | Yes | Yes |
| Minimum interval | 1 hour | 1 minute | 1 minute |

**Pick:** cloud for unattended work, Desktop for local-file work that must
survive session close, `/loop` for quick polling during an active session.

## `/loop` — session-scoped recurring prompt

Bundled skill. Forms:

| Form | Example | Behavior |
|:--|:--|:--|
| Interval + prompt | `/loop 5m check the deploy` | Fixed cron schedule |
| Prompt only | `/loop check CI` | Claude self-paces between 1 min and 1 hour |
| Nothing | `/loop` | Runs `loop.md` if present, else built-in maintenance prompt |

Intervals: `s` (rounded up), `m`, `h`, `d`. Rounded to nearest clean cron
step. Bare token (`30m`) or trailing clause (`every 2 hours`).

`/loop <interval> /<command>` works — re-runs a packaged slash command
each iteration.

### Self-pacing mode

Claude picks delay between 1 min and 1 hour based on what it observed.
Short waits when active; longer when quiet. May use the `Monitor` tool
instead of re-prompting (more efficient).

### Built-in maintenance prompt

`/loop` with no prompt and no `loop.md`: continue unfinished work, tend to
current branch's PR (reviews, CI failures, conflicts), run cleanup
(simplification, bug hunts) when nothing pending. Won't start new
initiatives. Irreversible actions only proceed if transcript already
authorized them.

### `loop.md` — override the default

| Path | Scope |
|:--|:--|
| `.claude/loop.md` | Project. Takes precedence. |
| `~/.claude/loop.md` | User. Fallback. |

Plain markdown; treated as the prompt for bare `/loop`. Ignored when you
supply a prompt on the command line. Edits apply next iteration. Truncated
at 25 KB.

### Stopping a loop

Press `Esc` while the loop is waiting for next iteration. Loops created
manually via natural-language Claude (`CronCreate`) don't respond to Esc.

### Jitter

- Recurring tasks: up to 10% of period late, capped at 15 min.
- One-shot at `:00` or `:30`: up to 90 seconds early.
- Derived from task ID, so consistent per task.

Avoid `:00`/`:30` minutes if exact timing matters.

### Seven-day expiry

Recurring tasks auto-expire 7 days after creation (fire once more then
delete). Cancel and recreate to extend, or use Routines / Desktop tasks
for durable scheduling.

## One-time reminders

Natural language: "remind me at 3pm to push the release branch" or "in 45
minutes check if tests passed". Claude schedules a one-shot cron task that
deletes itself after running.

## Manage scheduled tasks

Ask Claude or call the tools directly.

### Tools

| Tool | Purpose |
|:--|:--|
| `CronCreate` | Create a task. 5-field cron expression, prompt, one-shot or recurring. |
| `CronList` | List tasks with IDs, schedules, prompts. |
| `CronDelete` | Cancel by ID. |

Each task has 8-char ID. Max 50 tasks per session.

### Cron expression

Standard 5-field: `minute hour day-of-month month day-of-week`. Wildcards
(`*`), values, steps (`*/15`), ranges (`1-5`), comma lists (`1,15,30`).

| Example | Meaning |
|:--|:--|
| `*/5 * * * *` | Every 5 minutes |
| `0 * * * *` | Every hour on the hour |
| `7 * * * *` | Every hour at :07 |
| `0 9 * * *` | Every day at 9am local |
| `0 9 * * 1-5` | Weekdays at 9am local |
| `30 14 15 3 *` | March 15 at 2:30pm |

Day-of-week `0` or `7` = Sunday. **NOT supported:** `L`, `W`, `?`, name
aliases (`MON`, `JAN`).

When both DOM and DOW are constrained, date matches if either matches
(standard vixie-cron).

All times local.

## How tasks execute

- Scheduler checks every second for due tasks.
- Tasks enqueue at low priority — fire between turns, not mid-response.
- If Claude is busy when due, task waits until current turn ends.

### No catch-up

If a task's time passes while Claude is busy on a long request, it fires
once when idle, not once per missed interval.

### Session-scoped only

- Tasks only fire while Claude Code is running AND idle.
- Closing terminal or exiting session stops them.
- `/clear` or starting a fresh conversation clears session-scoped tasks.
- `claude --resume` or `claude --continue` restores unexpired tasks:
  recurring tasks within 7 days of creation; one-shots whose time hasn't
  passed.
- Background Bash and monitor tasks NEVER restored on resume.

## Disabling the scheduler

`CLAUDE_CODE_DISABLE_CRON=1` in environment. Makes cron tools and `/loop`
unavailable, stops already-scheduled tasks from firing.

## Routines (cloud)

`/schedule [description]` or `/routines`. Cloud-run, machine-independent.
Configured via `/schedule` wizard. Uses connectors for MCP per-task.
Minimum 1-hour interval.

## Desktop scheduled tasks

Local, per-task config file. Minimum 1 minute. Inherits full local file
access.

## ScheduleWakeup — dynamic `/loop` pacing

Source: https://code.claude.com/docs/en/scheduled-tasks

When you run `/loop <prompt>` without an interval, Claude uses the internal
`ScheduleWakeup` tool to self-pace iterations:

1. Claude executes the prompt.
2. At the end, it calls `ScheduleWakeup` with a chosen delay (1 min – 1 hour).
3. The delay is picked based on what was observed — short when active, longer
   when quiet.
4. On Bedrock/Vertex/Foundry, dynamic scheduling falls back to a fixed
   10-minute interval.

**Cache strategy:** Claude Code's prompt cache has a 5-minute TTL.
ScheduleWakeup may choose ~4-minute delays for stable tasks to stay within
the cache window and avoid re-paying input token costs. This means a sleep
of 300 seconds or longer in a shell loop busts the cache — prefer
ScheduleWakeup-driven `/loop` or the Monitor tool for long-running polls.

## Monitor tool — react to events instead of polling

For watching ongoing processes, prefer the `Monitor` tool over a polling
loop:

- Streams each stdout line of a background script as a notification.
- Token-efficient.
- Often used under the hood for `/loop` self-paced mode.

## Gotchas

- **Seven-day expiry** is easy to forget. Recurring loops silently die.
  Use Routines or Desktop tasks for durable.
- **Cron syntax is strict 5-field, vixie semantics.** `L`, `W`, names not
  supported.
- **Jitter** means `0 9 * * *` may fire at 9:03. If exact timing matters,
  pick `3 9 * * *`.
- **Bedrock, Vertex, Foundry** — `/loop` with no interval fires every 10
  minutes instead of self-pacing.
- `/clear` wipes all session-scoped tasks.
- **Background tasks** don't restore on resume.

## Disambiguation

- **`/loop` vs CronCreate:** `/loop` is the bundled skill / convenience
  wrapper. Under the hood it calls `CronCreate`. Manage with the same
  `CronList` / `CronDelete` tools.
- **`/loop` vs Routines:** `/loop` only fires while session open. Routines
  run in Anthropic cloud, survive machine off.
- **Routines vs Desktop scheduled tasks:** cloud vs local. Cloud = no
  machine, no local files. Desktop = full local env.
- **Monitor tool vs `/loop`:** Monitor watches a background script and
  pushes events; `/loop` re-runs a prompt.
- **CronCreate vs GitHub Actions `schedule`:** GitHub Actions are
  CI-driven. CronCreate is Claude Code-driven.

## Minimal examples

**Polling a deploy:**
```
/loop 5m check if the deploy finished and tell me what happened
```

**Auto-handle PR review + CI while session open:**
```
/loop check whether CI passed and address any review comments
```

**Reminder:**
```
remind me at 3pm to push the release branch
```

**Cancel:**
```
cancel the deploy check job
```
