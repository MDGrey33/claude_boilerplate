---
name: memory-hygiene
description: Audit and prune the auto-memory system. Classifies each MEMORY.md entry and topic file as ENFORCE / HOT / WARM / STALE, archives old ones, and optionally promotes stable HOT patterns into CLAUDE.md Hard Overrides. Use when MEMORY.md gets dense (>30 entries), sessions feel slow from context bloat, or on a monthly cadence. Trigger "memory hygiene", "clean memory", "memory audit", "memory promote", "prune memory".
user_invocable: true
args: `audit` (default) | `promote` | `archive` | `compact` | `graduate`
---

## When to Use

- MEMORY.md shows 30+ entries
- Sessions feel slow from context bloat
- Monthly cadence (schedule via `/schedule` if desired)
- Same correction has happened multiple times despite an existing memory entry → consider promotion to CLAUDE.md

## Paths

The skill operates on the active project's auto-memory directory. Resolve `<slug>` from the active project — typically the path of `~/.claude/projects/<slug>/`.

| What | Where |
|---|---|
| MEMORY.md (auto-memory index) | `~/.claude/projects/<slug>/memory/MEMORY.md` |
| Topic files | `~/.claude/projects/<slug>/memory/*.md` |
| Session summaries (if your hooks write them) | `~/.claude/projects/<slug>/memory/sessions/` |
| Archive | `~/.claude/projects/<slug>/memory/archive/` |
| Global overrides | `~/CLAUDE.md` (Hard Overrides section — see below) |
| Reports | `<your-workspace>/memory-hygiene-<YYYY-MM-DD>.md` |

If `MEMORY.md` has a hook-generated header, don't edit it — only the body entries are fair game.

### Out of scope — never touch

If your setup has an immutable wiki / claims layer (sources, time-stamped fact claims), this skill must NEVER read, classify, archive, prune, or compact anything in:

- Any `sources/` directory holding raw immutable source material
- Any `claims/` directory holding time-stamped fact claims
- Any file whose YAML frontmatter contains `immutable: true`

This skill's authority is bounded to: `MEMORY.md` and the auto-memory topic files (`feedback_*.md`, `reference_*.md`, `project_*.md`, `user_*.md`).

## Triggers

- Manual: "memory hygiene", "clean memory", "memory audit", "prune memory"
- Monthly cadence
- When MEMORY.md shows 30+ entries

---

## Action: `audit` (default)

### 1. Inventory

- Read `MEMORY.md` — count entries (lines that match `^- \[.+\]`), note total lines.
- List topic files with sizes.
- Target: MEMORY.md body stays under ~40 entries / 200 lines.

### 2. Classify each entry

For every link in MEMORY.md and every topic file:

| Class | Definition | Evidence |
|---|---|---|
| **ENFORCE** | Rule-shaped, must fire at generation time | Mirror into `~/CLAUDE.md` Hard Overrides. Criteria: (a) a slip happened despite the memory, OR (b) same correction 2+ times in 30 days, OR (c) user said "must not happen again" |
| **HOT** | Referenced in last 3 session summaries, or mentioned in last 7 days | `grep -l "<keyword>" <session-dir>/*.md \| tail -3` |
| **WARM** | Referenced in last 30 days, or still-valid technical reference | Check if the files/paths it refers to still exist |
| **STALE** | Not referenced in 30+ days AND info is outdated or superseded | Archival candidate |

### 3. Check for duplication

For each entry, ask: is it in CLAUDE.md already? If yes → WARM/STALE candidate — don't keep two copies of the same rule.

### 4. Report

Write a report to a workspace location (e.g. `<workspace>/memory-hygiene-<YYYY-MM-DD>.md`):

```markdown
# Memory Hygiene — YYYY-MM-DD

**MEMORY.md:** N entries / M lines
**Topic files:** K files, total L KB

## Classification

| Entry / file | Class | Last referenced | Duplicate? | Proposed action |
|---|---|---|---|---|
| feedback_terminal_unsupported.md | STALE | 2026-02-10 | No | Archive |
| user_role.md | WARM | 2026-04-10 | No | Keep |

## Proposed ENFORCE promotions (need approval)
- <entry> — reason: <slip pattern> — proposed rule text for CLAUDE.md Hard Overrides

## Summary
- Archive: <n> stale entries (-<lines> lines)
- Promote: <n> entries to ENFORCE (review needed)
- Keep: <n>
```

Present the report. Do not act without approval.

---

## Action: `promote`

Move stable HOT patterns into MEMORY.md (if they're in lesson files only) or into `~/CLAUDE.md` Hard Overrides (ENFORCE class).

### WARM → MEMORY.md (lessons → memory)

1. Read recent lesson files (if your setup has them).
2. If a lesson has been corroborated across 3+ sessions, draft a MEMORY.md entry in the standard format.
3. Present to the user for approval. On approval, append a new `- [description](topic_file.md)` line referencing the source file.

### HOT → ENFORCE (MEMORY.md → CLAUDE.md Hard Overrides)

Only promote when one of:
- A memory entry already exists AND a slip happened this session (proves memory alone was insufficient)
- Same correction happened 2+ times in the last 30 days
- User explicitly flagged "this must not happen again"

Procedure:
1. Draft the rule in this shape:
   ```markdown
   ### <Category> — <rule title>
   <One-sentence imperative>.
   **Why:** <specific incident tied to the slip>
   **How to apply:** <when/where this fires>
   ```
2. Present to the user. ENFORCE entries go into the "always in-context" layer — every one has a context cost, so be stingy.
3. On approval: append to the `## Hard Overrides` section of `~/CLAUDE.md` (if the section doesn't exist, propose its creation). Leave the HOT entry in MEMORY.md as the backing record — CLAUDE.md is a projection, not a replacement.
4. Log the promotion in `~/.claude/projects/<slug>/memory/enforce-log.md` with date and rationale.

### Demotion

If an ENFORCE rule has gone 60+ days with zero slips AND no related lessons opened, propose demoting it back to HOT to free context budget. Context cost should be earned continuously.

---

## Action: `archive`

1. Read the latest audit report (run `audit` first if there isn't one).
2. For each entry marked STALE-archive:
   - Write `~/.claude/projects/<slug>/memory/archive/archived-YYYY-MM-DD-<topic>.md` with the entry content plus an "Archived because:" line.
   - Remove the entry from MEMORY.md (and the source topic file if no longer referenced).
3. Report final line count.

---

## Action: `compact`

Emergency reduction when MEMORY.md is bloated past target (>200 lines or >50 entries):

1. Run `audit` silently.
2. Archive ALL STALE entries.
3. If still over, archive the lowest-value WARM entries (starting with anything duplicated in CLAUDE.md).
4. Report line count delta and list of archived items.

`compact` is the only action that may run without explicit per-entry approval — but only the user authorises `compact` in the first place.

---

## Action: `graduate`

Converts stable auto-memory entries into long-term source documents, staging them for epistemically-managed storage (a wiki/claims layer if you have one, or a plain permanent record if you don't).

**Model:** Haiku 4.5 — claim rewriting is mechanical extraction, not judgment.

### When to use

- After `audit` identifies ENFORCE-class entries stable for 30+ days
- HOT `feedback` entries representing durable insights (not project-specific preferences)
- `reference` entries pointing to architecturally important external systems
- Explicit: "graduate <file or all>"

### Steps

**1. Select candidates**

Default: ENFORCE-class entries from the last audit + HOT `feedback` entries older than 30 days.
Present candidates and get confirmation before proceeding.

**2. Determine output directory**

If you have a wiki/sources layer, write to its sources directory (e.g. `~/workspace/sources/`).
Otherwise write to `<your-workspace>/memory-graduated/` (create if missing).

**3. For each candidate, write a source doc**

Path: `<sources-dir>/memory-graduate-YYYY-MM-DD-<slug>.md`

Frontmatter:
```yaml
---
title: <memory name>
source_type: auto-memory
memory_type: <feedback|user|project|reference>
graduated_at: YYYY-MM-DD
origin_file: ~/.claude/projects/<slug>/memory/<filename>
authority_prior: high
immutable: false
---
```

Body: rewrite the memory in third-person episodic form. Strip first-person language. For `feedback` entries, extract 2–5 atomic claims in the form:
> "Users with this workflow profile require X when Y, because Z."

**4. Tag the original memory file**

Add `graduated: <YYYY-MM-DD>` to the YAML frontmatter of the original file.

**5. Update MEMORY.md**

Append ` (graduated YYYY-MM-DD)` to the relevant line.

**6. Report**

List source docs written, paths. Note that if wiki-ingest is available, it will pick these up automatically; otherwise they are permanent human-readable records.

### Wiki-ingest integration (optional)

If you have a `wiki-ingest` skill installed: call it on each source doc after writing. If not, source docs accumulate as correctly-formatted records the user can query or ingest later.

### Don't

- Don't graduate `project` entries with absolute deadlines or ephemeral state
- Don't graduate entries already tagged `graduated:` (idempotent check)
- Don't lose the specific incident or rationale — the "why" is the epistemic value
- Don't delete or archive the original auto-memory entry after graduation — it still serves as a fast reflex

---

## Error handling

- MEMORY.md under 30 entries → report "healthy, no action needed" and stop.
- No session files found → cannot classify freshness; mark UNKNOWN, suggest manual review.

## Don't

- Don't edit MEMORY.md header lines if they're hook-generated.
- Don't silently archive; every archival must appear in the audit report.
- Don't add to `~/CLAUDE.md` without explicit per-rule approval.
- Don't duplicate CLAUDE.md content into MEMORY.md — they're different layers.
- Don't run `compact` pre-emptively; it's for emergencies.
