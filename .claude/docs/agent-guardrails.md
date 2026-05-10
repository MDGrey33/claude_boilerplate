# Agent Guardrails

> Operational principles for agents working in this boilerplate. Three sections
> by scope: rules that apply to any agent (Universal), rules specific to the
> user's main Claude session (Session-agent), and rules specific to sub-agents
> spawned via the Agent tool (Autonomous-agent).

## Universal rules

Apply to any agent — main session or autonomous sub-agent.

- **Don't fabricate.** Only report what you find in data sources. Flag uncertainty rather than guessing.
- **Every report claim needs a source link.** Unverified items are flagged, not presented as fact.
- **Maximize parallelization.** Run independent operations concurrently when there are no data dependencies.
- **Active session context comes from the session marker, never from cwd.** Skills that need the active project, workstream, or open item read `<workspace>/sessions/active/<id>.md` (workspace-level) or `<workspace>/projects/<slug>/sessions/active/<id>.md` (project-scoped). Do not derive from `pwd`, the Bash tool's reported cwd, or path inspection — these drift mid-session as Claude or the user navigate the filesystem (cd into a subdir to run tests, grep across projects, inspect fixtures), and a cwd-derived lookup will silently misroute writes. The only exception is `/hello` at session start, which may use cwd as a confirmation hint to suggest a likely project; the user always confirms, and the marker becomes the source of truth from that moment.

## Session-agent rules

Apply only to the user's main Claude conversation.

- **Re-check `sessions/active/` when the user shifts to a new open item mid-session.** If the user's stated work changes from the active session marker's recorded item(s), scan for overlap with other active markers in `sessions/active/`. Warn the user if any overlap exists, with the other session's age in human-readable form. Optionally update the active marker to reflect the new item.

## Autonomous-agent rules

Apply only to sub-agents spawned via the Agent tool. They have a fixed prompt, run to completion, and return one result.

- **Bound each unit of work to one context window.** If the work won't fit, decompose into independent sub-tasks before dispatch.
- **Skip "Report to user" steps in skills.** The dispatching agent reports; sub-agents return their result and exit.
- **Log via `/log` on completion** (status: SUCCESS, WARNING, or FAILED). The dispatching agent reads logs to track sub-agent state.
- **Allowlists must be project-level.** Sub-agents inherit project-level `.claude/settings.json` permissions; user-interactive Allow approvals don't propagate. Skills that spawn sub-agents must ship project-level allowlists for any tool the sub-agent will use.
