# Slash commands — deep reference

Source: https://code.claude.com/docs/en/commands (full list) and
https://code.claude.com/docs/en/skills (custom commands are now skills).

## Two kinds of commands

**Built-in** — hard-coded CLI behavior (`/help`, `/compact`, `/doctor`,
`/config`, `/mcp`, `/permissions`, etc.). Can't be re-implemented in user
skills.

**Bundled skills** — prompt-driven skills that ship with Claude Code (e.g.
`/simplify`, `/batch`, `/debug`, `/loop`, `/claude-api`,
`/fewer-permission-prompts`). Marked "Skill" in the commands reference.

**Custom commands** — user-created. These have been **merged into skills**:
`.claude/commands/foo.md` still works but a skill at
`.claude/skills/foo/SKILL.md` is equivalent and strictly more powerful.

## Legacy command file (`.claude/commands/foo.md`)

Works identically to a skill with only `SKILL.md`. Same frontmatter schema
(description, argument-hint, allowed-tools, model, etc.). No supporting
files. Loses live-reload and the nested-directory benefits skills enjoy.

If a skill and a command share a name, **the skill wins**.

## Built-in commands — full list (abridged; authoritative table at /en/commands)

- `/add-dir <path>` — add a working directory for the session.
- `/agents` — manage subagent configurations.
- `/autofix-pr [prompt]` — cloud session that watches current branch's PR.
- `/branch [name]` / `/fork` — branch the current conversation.
- `/btw <question>` — side-question, doesn't affect conversation context.
- `/chrome` — configure Claude in Chrome.
- `/clear` / `/reset` / `/new` — start a fresh conversation. To free context
  while continuing, use `/compact`.
- `/color [name]` — prompt bar color.
- `/compact [instructions]` — summarize conversation to free context.
- `/config` / `/settings` — Settings UI.
- `/context` — visualize context usage.
- `/copy [N]` — copy the last (or N-th latest) assistant response.
- `/cost` — token usage stats.
- `/desktop` / `/app` — open current session in Desktop app.
- `/diff` — interactive diff viewer.
- `/doctor` — diagnose installation. Press `f` to have Claude fix.
- `/effort [level|auto]` — set model effort (`low`/`medium`/`high`/
  `xhigh`/`max`).
- `/exit` / `/quit`.
- `/export [filename]` — export conversation as plain text.
- `/extra-usage` — configure rate-limit overage.
- `/fast [on|off]` — toggle fast mode.
- `/feedback` / `/bug`.
- `/focus` — focus view (fullscreen only).
- `/heapdump` — write JS heap snapshot.
- `/help`.
- `/hooks` — view configured hooks.
- `/ide` — manage IDE integrations.
- `/init` — generate CLAUDE.md. `CLAUDE_CODE_NEW_INIT=1` for interactive flow.
- `/insights` — session-analysis report.
- `/install-github-app`, `/install-slack-app`.
- `/keybindings` — open keybindings config file.
- `/login`, `/logout`.
- `/mcp` — MCP server management and OAuth.
- `/memory` — edit CLAUDE.md, manage auto-memory.
- `/mobile` / `/ios` / `/android` — QR for mobile app.
- `/model [name]` — change model.
- `/passes` — free week for friends (if eligible).
- `/permissions` / `/allowed-tools` — manage permission rules.
- `/plan [description]` — enter plan mode.
- `/plugin` — manage plugins.
- `/powerup` — interactive feature lessons.
- `/privacy-settings` (Pro/Max only).
- `/recap` — one-line session summary.
- `/release-notes` — changelog picker.
- `/reload-plugins` — reload plugins mid-session.
- `/remote-control` / `/rc` — enable remote control.
- `/remote-env` — configure web-session remote env.
- `/rename [name]` — rename session.
- `/resume [session]` / `/continue` — resume by ID/name.
- `/review [PR]` — local PR review.
- `/rewind` / `/checkpoint` / `/undo` — rewind code or conversation.
- `/sandbox` — toggle sandbox mode.
- `/schedule [description]` / `/routines` — cloud cron agents.
- `/security-review` — scan current diff for security issues.
- `/setup-bedrock` (when `CLAUDE_CODE_USE_BEDROCK=1`).
- `/setup-vertex` (when `CLAUDE_CODE_USE_VERTEX=1`).
- `/skills` — list available skills.
- `/stats` — daily/session usage.
- `/status` — status panel.
- `/statusline` — configure status line.
- `/stickers` — order merchandise.
- `/tasks` / `/bashes` — background tasks.
- `/team-onboarding` — generate onboarding guide from your usage.
- `/teleport` / `/tp` — pull a web session into the terminal.
- `/terminal-setup` — fix terminal keybindings for Shift+Enter etc.
- `/theme` — color theme picker.
- `/tui [default|fullscreen]` — terminal UI renderer.
- `/ultraplan <prompt>` — cloud planning session.
- `/ultrareview [PR]` — cloud multi-agent code review.
- `/upgrade` — plan upgrade.
- `/usage` — plan usage/rate limits.
- `/voice` — toggle push-to-talk dictation.
- `/web-setup` — connect GitHub for Claude Code on the web.

Availability varies by platform, plan, environment.

## Removed commands (be aware if older docs mentioned them)

- `/vim` — removed in v2.1.92. Use `/config` → Editor mode.
- `/pr-comments` — removed in v2.1.91. Ask Claude directly instead.

## Bundled skills (prompt-driven, invokable as slash commands)

- `/simplify [focus]` — parallel review-and-fix for recent changes.
- `/batch <instruction>` — spawn many background agents in worktrees for
  large-scale refactors.
- `/debug [description]` — enable debug logging and analyze issues.
- `/loop [interval] [prompt]` — run a prompt on schedule (see
  surfaces/background-tasks.md).
- `/claude-api` — load Claude API reference material.
- `/fewer-permission-prompts` — generate an allowlist from transcripts.

## MCP prompts

`mcp__<server>__<prompt>` — dynamically discovered from connected MCP servers.

## Plugin commands

Plugin-provided commands/skills are namespaced `/<plugin-name>:<command>`.
Example: if plugin `acme` provides `hello`, invoke as `/acme:hello`.

## Frontmatter for custom commands (legacy `.claude/commands/`)

Same as skills:

```yaml
---
description: What this command does
argument-hint: "[issue-number]"
allowed-tools: Read, Grep, Bash(git status *)
model: sonnet
disable-model-invocation: true
---

Command body. Use $ARGUMENTS, $0, $1 for args.
```

## When to use a skill vs a slash command

They're functionally the same now. Prefer a skill (`.claude/skills/foo/`) when:
- You want supporting files (scripts, examples, reference docs).
- You want live-reload.
- You want nested monorepo discovery.

Prefer a legacy command file only for tiny single-file workflows — and even
then, a skill with just SKILL.md costs nothing more.

## Disambiguation

- **Built-in command vs bundled skill:** built-ins are hard-coded (e.g.
  `/compact`, `/config`); bundled skills are ordinary skills Anthropic
  ships (e.g. `/simplify`). Bundled skills can be invoked via the Skill
  tool; some built-ins (`/init`, `/review`, `/security-review`) also work
  through the Skill tool, others (`/compact`) don't.
- **Custom command vs skill:** functionally merged. Always prefer skill.
- **Slash command vs shortcut/keybinding:** slash commands are typed;
  keybindings are one-key-combo triggers for editor actions.
- **Skill's `allowed-tools` vs `/permissions` rules:** the frontmatter
  pre-approves tools while the skill runs; `/permissions` sets session-wide
  rules.

## Minimal worked example

```
~/.claude/skills/standup/SKILL.md
```

```yaml
---
name: standup
description: Draft a standup update. Use when asked for a standup, daily update, or end-of-day report.
allowed-tools: Bash(git log *) Bash(git status *) Read
---

Draft an end-of-day standup:

1. Run `git log --oneline --author=\$(git config user.email) --since='24 hours ago'` for recent commits.
2. Note any WIP in `git status`.
3. Output: "Done / Doing / Blockers" in 5 bullet total.
```

Invoke `/standup` or ask "give me a standup".
