# Agent Guardrails

> Operational principles for agents working in Memnyx. Three sections
> by scope: rules that apply to any agent (Universal), rules specific to the
> user's main Claude session (Session-agent), and rules specific to sub-agents
> spawned via the Agent tool (Autonomous-agent).

## Universal rules

Apply to any agent — main session or autonomous sub-agent.

- **Don't fabricate.** Only report what you find in data sources. Flag uncertainty rather than guessing.
- **Every report claim needs a source link.** Unverified items are flagged, not presented as fact.
- **Maximize parallelization.** Run independent operations concurrently when there are no data dependencies.
- **When a skill chains to another skill via the `Skill` tool, the called skill's output is intermediate.** The calling skill must resume its remaining steps after the called skill completes. Never treat the called skill's output as a terminal response.
- **Active session context comes from the session marker, never from cwd.** Skills that need the active project, workstream, or open item read `<workspace>/sessions/active/<id>.md` (workspace-level) or `<workspace>/projects/<slug>/sessions/active/<id>.md` (project-scoped). Do not derive from `pwd`, the Bash tool's reported cwd, or path inspection — these drift mid-session as Claude or the user navigate the filesystem (cd into a subdir to run tests, grep across projects, inspect fixtures), and a cwd-derived lookup will silently misroute writes. The only exception is `/hello` at session start, which may use cwd as a confirmation hint to suggest a likely project; the user always confirms, and the marker becomes the source of truth from that moment.
- **Artefact outputs live under `artifacts/<slug>/`, scope-aware.** Skills and sessions that emit files (feedback, generated documents, collected data, derived artefacts) write to `<scope>/artifacts/<skill-slug-or-workstream-slug>/<filename>`. Scope is resolved from the session marker: workspace scope → `<workspace>/artifacts/`; project scope → `<workspace>/projects/<slug>/artifacts/`. Never co-locate artefacts with `workstreams/` (which are open-item ledgers /bye writes into) or `sessions/`.
- **Workspace detection uses the workspace marker file.** Skills that need to locate the workspace walk up three directory levels from their own base dir (`<workspace>/.claude/skills/<skill>/`), then validate that `<workspace>/.claude/.workspace` exists. Do not bind workspace detection to the existence of any specific skill (e.g., `.claude/skills/setup-workspace/`) — skill names can change; the marker file is the contract.
- **Follow explicit SKILL instructions; surface deviations before deviating.** When a SKILL has an explicit instruction (pagination, validation, atomicity, ordering, write-back rules), follow it as written. SKILLs usually document their own principled deviation points (stop-and-flag thresholds, fallback cases, error branches) — use those, don't invent parallel ones. If you genuinely think the SKILL is wrong for the invocation at hand, surface the choice to the user BEFORE deviating — name the instruction, name the proposed deviation, name what cost is saved. Don't reframe an unannounced shortcut as a "deliberate trade-off" in the recap; honest framing is "I deviated from step X; here's the gap."

## Session-agent rules

Apply only to the user's main Claude conversation.

- **Re-check `sessions/active/` when the user shifts to a new open item mid-session.** If the user's stated work changes from the active session marker's recorded item(s), scan for overlap with other active markers in `sessions/active/`. Warn the user if any overlap exists, with the other session's age in human-readable form. Optionally update the active marker to reflect the new item.
- **In an inline skill chain, continue the calling skill in the same response turn.** The called skill's output is visible to the user in the conversation, but the turn must not end there. Resume the calling skill's remaining steps immediately after the called skill finishes.

## Autonomous-agent rules

Apply only to sub-agents spawned via the Agent tool. They have a fixed prompt, run to completion, and return one result.

- **Bound each unit of work to one context window.** If the work won't fit, decompose into independent sub-tasks before dispatch.
- **Skip "Report to user" steps in skills.** The dispatching agent reports; sub-agents return their result and exit.
- **Log via `/log` on completion** (status: SUCCESS, WARNING, or FAILED). The dispatching agent reads logs to track sub-agent state.
- **Allowlists must be project-level.** Sub-agents inherit project-level `.claude/settings.json` permissions; user-interactive Allow approvals don't propagate. Skills that spawn sub-agents must ship project-level allowlists for any tool the sub-agent will use.
- **If a sub-agent invokes a skill via the `Skill` tool, fold the called skill's result into the sub-agent's own return — do not surface it as user-facing output directly.** The "Skip Report to user" rule applies to the called skill as much as to the sub-agent itself.
