# claude-expert self-update protocol

> Companion to [SKILL.md](SKILL.md). Describes the bounded, gated refresh that keeps
> claude-expert current without uncontrolled self-modification.
>
> All location-dependent values in this document (where reports go, where the Python
> port lives, which managers exist) are **discovered**, not hardcoded. Run the
> companion `discover-setup.sh` and read its output — this protocol references the
> keys it emits (`STAGING_DIR`, `PYTHON_PORT`, `MANAGERS`, …), never a fixed path.

## Why self-update at all

claude-expert is a reference, and a stale reference is a *dangerous* reference — a wrong
fact about a model, a price, or a surface is worse than a missing one. So the skill keeps
itself fresh with a **bounded, gated** self-update: additive knowledge auto-applies;
anything that changes how the skill *decides* is held for **you**. (These invariants
sharpen judgment, they aren't a checklist — see `reasoning.md`; when a
case doesn't fit, reason from the tradeoff.)

The three invariants this protocol keeps firm:

1. **Automation never rewrites judgment.** Decision logic (forks, surface
   recommendations, anti-pattern verdicts) only ever changes with you in the loop.
2. **Verify before write.** No fact lands without confirming it against the canonical
   source (the official changelog / `code.claude.com/docs`) first.
3. **Additive auto-applies, decision-impacting gates.** New cited facts are low-risk and
   reversible; anything that alters a fork is proposed, never applied.

## Triggers — two, sharing one runbook

claude-expert can refresh from **two** triggers. Both execute the same logic and both
stamp a `.last-research` file in the skill directory on completion, so they
interlock — whichever fires first satisfies the other.

- **Lazy, on-invocation (primary).** Every time claude-expert is invoked it checks
  `.last-research`; if it hasn't researched in ≥7 days (default cadence — tighten it when
  the docs are churning fast) it spawns the refresh as a **background subagent** and
  answers the user's task *in parallel*. This path depends on **no scheduler being
  required** — it is driven by use alone. Self-lock the gate for ~2h on spawn so it never
  double-fires; bump `.last-research` to today on completion.
- **Optional weekly scheduled task (backstop).** A durable local scheduled task (see
  template below) fires weekly. If the machine/app wasn't up to fire it, the lazy check
  covers it on next use; if the scheduled task fires first, it stamps `.last-research` and
  the lazy check then reads FRESH. Either way the work happens about once per week. This
  trigger is **optional** — the lazy path is sufficient on its own; install the scheduled
  task only if you want refreshes to happen without your invoking the skill.

## Mechanism

A single runbook, invoked by either trigger:

1. **Research directly.** Pull the official changelog + `code.claude.com/docs/en/*` since
   the last freshness date, **directly with WebSearch/WebFetch in this same context** —
   not via a nested research skill. Nested research that spawns its own subagents fails on
   the on-invocation path, where this runbook is *already* a subagent. Do the searches and
   fetches inline.
2. **Write a dated freshness report** to the **discovered `STAGING_DIR`** (see below) as
   `claude-expert-freshness-YYYY-MM-DD.md`. Record every delta with an inline source URL
   and a classification:
   - `ADDITIVE` — a new feature, surface, field, model, or price.
   - `CORRECTION` — a fact currently stated in the skill is now wrong.
   - `DECISION-IMPACTING` — changes a fork, a "right surface" recommendation, the manager
     roster, or an anti-pattern verdict.
   - `UNCLASSIFIED → needs you` — a delta that couldn't be confidently classified.

### Where reports go — `STAGING_DIR` (discovered, never hardcoded)

The freshness report is written to whatever `discover-setup.sh` reports as `STAGING_DIR`.
That script resolves it in order:

1. `$CLAUDE_EXPERT_STAGING` environment variable, if set;
2. a `./.claude-expert.staging` file in the skill directory, if present (its contents are
   the path);
3. default: `<skill-dir>/.staging/` (created on first use).

Never write reports to any personal inbox, review queue, or curated knowledge tier — the
report is a *staging* artifact for your review, and `STAGING_DIR` is the only place it goes.

## What auto-applies vs what gates

The **only** file the auto-apply path may write is **`latest.md`** — the inert,
purpose-built freshness/version fact sheet (the dated "as-of" facts), plus the report's own
date stamp. Everything that encodes *judgment* is off-limits to automation: the decision
forks (`decision-forks.md` and the four-way table in `decision-tree.md`), the surface
recommendations (`SKILL.md` + `surfaces/*`), the anti-pattern verdicts (`anti-patterns.md`),
and any manager roster the discovery step assembles (`managers.md`).

| Change class | Action | Rationale |
|:--|:--|:--|
| **ADDITIVE** | Auto-append the new cited fact to **`latest.md`** (the freshness/version fact sheet) and bump its date stamp. | New facts *with citations* are low-risk and reversible (invariant 3). Verify the cite first (invariant 2). |
| **CORRECTION** (a stated fact is now false) | Auto-fix the specific fact **only after confirming the new value against the canonical changelog (invariant 2)**; if unverifiable, GATE it. Flag every correction loudly in the freshness report. | A wrong fact is worse than a missing one, so the fix itself must be verified — and it is logged, never silent. |
| **DECISION-IMPACTING** (alters a fork in `decision-forks.md` / `decision-tree.md`, a "right surface" recommendation, the manager roster in `managers.md`, or an `anti-patterns.md` verdict) | **GATE — propose only, never auto-apply.** Write the proposed diff into the freshness report and stop. | This is the skill's *judgment*, not its data. Automation never rewrites judgment (invariant 1); a scheduled task silently rewriting decision logic is uncontrolled self-modification. |
| **UNCLASSIFIED** | Write the delta into the report marked `needs you`; apply nothing. | Fail closed. |

## Safety rationale — no uncontrolled self-modification

- **Bounded surface.** The auto-apply path touches **only** `latest.md` and its date
  stamp. It **cannot** rewrite `decision-forks.md`, `anti-patterns.md`, `decision-tree.md`,
  the surface recommendations, or `managers.md` without your review — those are the
  load-bearing parts a wrong edit would corrupt.
- **Staging, not curated.** Proposals are written to the discovered `STAGING_DIR`, never
  promoted directly into any reviewed/curated tier. Whatever promotion flow your setup uses
  (a file/record-management manager skill if `discover-setup.sh` reports one PRESENT for the
  `files` type, otherwise a manual move) stays in the loop.
- **Fails closed.** If research errors, the docs are unreachable, or a delta can't be
  classified, the report is written with the delta marked `UNCLASSIFIED → needs you` and
  nothing is applied.
- **Idempotent and logged.** Each run appends its freshness-date delta to a log line so a
  bad auto-apply is trivially diffable and reversible. Back up any decision file before an
  automated touch (the auto-apply path should never touch one — this is belt-and-braces).

Net: claude-expert stays current on **facts** automatically, but its *opinion* about which
surface to pick only ever changes with **you** in the loop.

## Optional weekly scheduled task — inline template

The lazy on-invocation trigger is enough on its own. If you also want a time-based
backstop, install a durable local scheduled task. Create
`~/.claude/scheduled-tasks/claude-expert-freshness/SKILL.md` with the following (no
personal paths — it resolves everything through `discover-setup.sh`):

```markdown
---
name: claude-expert-freshness
description: Weekly bounded, gated refresh of the claude-expert reference.
schedule: "0 8 * * 1"   # Mondays 08:00 local — durable local scheduled task
---

# claude-expert weekly freshness backstop

Run the claude-expert self-update runbook (see the skill's `self-update.md`):

1. Locate the claude-expert skill: `~/.claude/skills/claude-expert/` or
   `./.claude/skills/claude-expert/`. Read `self-update.md`.
2. Resolve `STAGING_DIR` by running the skill's `discover-setup.sh` and reading the
   `STAGING_DIR=` line. Do NOT hardcode a path.
3. Research the official changelog + `code.claude.com/docs/en/*` since the date in
   `.last-research`, **directly with WebSearch/WebFetch** (no nested research skill).
4. Write `claude-expert-freshness-<today>.md` into `STAGING_DIR`, classifying every delta
   ADDITIVE / CORRECTION / DECISION-IMPACTING / UNCLASSIFIED.
5. Apply ONLY verified ADDITIVE facts (and verified CORRECTIONs) to `latest.md`; bump its
   date stamp. GATE everything DECISION-IMPACTING — propose in the report, apply nothing.
6. Stamp by running `freshness-check.sh stamp` (writes `.last-research` + clears the lock
   in the skill's own dir, wherever installed) so the lazy on-invocation check reads FRESH.
```

> Adjust the cron and the scheduler surface to whatever your environment supports.
> `discover-setup.sh` reports whether a schedules-manager-style skill is PRESENT; if so,
> register through it rather than hand-editing the scheduler.

## Activation

This task is **staged, not active** until you approve it. As a durable local scheduled
task it runs on your machine (no cloud billing) but needs the machine on and the app awake
at fire time. To deactivate: archive the
`~/.claude/scheduled-tasks/claude-expert-freshness/` folder. The lazy on-invocation
trigger keeps working regardless.
