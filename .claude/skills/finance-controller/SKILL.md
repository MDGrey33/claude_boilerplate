---
name: finance-controller
description: Audits the Claude Code setup (CLAUDE.md, skills, MCPs) for cost and context efficiency without touching quality. Produces a report with sized, prioritized actions and delegates execution to skills-manager or asks the user for approval. Use weekly, when sessions feel slow, or when bills spike.
user_invocable: true
args: Optional — "audit" (default, full scan) | "skills" | "mcps" | "claude-md" | "apply <recommendation-id>"
---

## Model Selection

- **Default model:** Haiku — the audit is structured file inspection (sizes, frontmatter grep, MCP list parsing); the script does the work.
- **Promote to Sonnet when:** judging whether a bloated skill's content is load-bearing or removable; resolving ambiguity in routing-table assignments; drafting the final report narrative.
- **Promote to Opus when:** never. If a judgment call is this hard, escalate to skills-manager.

## Purpose

Keep the setup **financially optimal without quality loss**. Three levers, ranked by impact/risk ratio:

1. **Prompt caching** — 90% read-cost reduction, zero quality risk (enforce stable system prompts).
2. **Model tier right-sizing** — 3-5× cost variance; Haiku $1/$5, Sonnet $3/$15, Opus $5/$25 per MTok.
3. **Progressive disclosure** — trim always-loaded bloat (CLAUDE.md, skill descriptions, MCP manifests).

## When to invoke

- Weekly maintenance sweep
- After adding/modifying multiple skills
- When sessions start slower than usual (context bloat signal)
- On the words "audit", "why is this slow", "cost check", "finance controller"

## Workflow

### Stage 1 — Scan (deterministic, scripted)

Run `bash .claude/skills/finance-controller/scripts/audit.sh`. It produces a JSON report with:
- CLAUDE.md byte count and token estimate
- Every SKILL.md: size, token estimate, model-tier declared (or missing)
- MCP servers configured + connected (via `claude mcp list`)
- Flag list against thresholds in `references/thresholds.md`

No LLM is used in this stage.

### Stage 2 — Classify (LLM, Haiku default)

For each flag, classify severity using `references/thresholds.md`:
- 🟢 Green — within budget
- 🟡 Yellow — watch, propose at next weekly cycle
- 🟠 Orange — recommend action this session
- 🔴 Red — recommend action now, block merges until resolved

### Stage 3 — Recommend

Produce the report using the template at `references/report-template.md`. Each recommendation has an ID (e.g., `R-CMD-1`, `R-SKL-3`, `R-MCP-2`), an estimated context/cost impact, a risk label, and the exact diff or command.

### Stage 4 — Delegate execution (never apply directly)

| Target | Route to |
|---|---|
| Skill file edit | `skills-manager` via its UPDATE flow (approval gate in its Stage 5) |
| New skill to add | `skills-manager` ADD flow |
| Skill to archive | `skills-manager` ARCHIVE flow |
| CLAUDE.md edit | Present diff, ask the user for approval, then Edit |
| MCP disable / project-local move | Present command, ask the user, then execute |
| Model-tier annotation for a skill missing one | `skills-manager` UPDATE flow |

Finance-controller **never edits skill files or CLAUDE.md directly**. It observes and recommends.

### Stage 5 — Log

Append one line per applied recommendation to `.claude/memory/finance-controller-log.md` with the date, ID, target, estimated impact, and the approver.

## Thresholds (summary — full table in `references/thresholds.md`)

| Surface | Green | Yellow | Orange | Red |
|---|---|---|---|---|
| CLAUDE.md | ≤3k tok | ≤5k tok | ≤8k tok | >8k |
| SKILL.md (one file) | ≤400 tok | ≤1.5k | ≤3k | >3k |
| MCPs enabled | ≤5 | ≤8 | ≤12 | >12 |
| Skill model-tier declared | 100% | 95% | 85% | <85% |

## Model routing table (summary — full table in `references/routing-table.md`)

| Skill archetype | Default tier |
|---|---|
| Deterministic scan/audit/lookup/format | Haiku |
| Research synthesis, code edit, orchestration, writing | Sonnet |
| Architectural proposal, cross-skill consolidation, contested reasoning | Opus (sparingly) |

## What finance-controller does NOT do

- Does **not** edit skills directly (skills-manager owns that).
- Does **not** delete MCP configs without asking (destructive, even if reversible).
- Does **not** trim CLAUDE.md content that looks redundant — CLAUDE.md content is intentional; trim only with approval.
- Does **not** recommend Opus downgrade for quality-critical skills (orchestration, quality-gates, security reasoning) without evidence.
- Does **not** run more than once per session unless explicitly asked. Repeat audits waste tokens.

## Invocation examples

```
/finance-controller              # full audit
/finance-controller skills       # skills only
/finance-controller mcps         # MCP hygiene only
/finance-controller claude-md    # CLAUDE.md only
/finance-controller apply R-MCP-2   # execute recommendation (still gates through approval)
```

## Supporting files

- `scripts/audit.sh` — deterministic scanner (Haiku-free, pure bash + jq)
- `references/thresholds.md` — full threshold matrix with rationale per row
- `references/routing-table.md` — skill-archetype → recommended tier, with evidence
- `references/mcp-hygiene.md` — per-MCP keep/disable/project-local decision rules
- `references/report-template.md` — the output format with example sections
