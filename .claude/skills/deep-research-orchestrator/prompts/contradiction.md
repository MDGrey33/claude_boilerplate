# Contradiction & Inconsistency Detection — Two Passes

This is a reasoning prompt for the ORCHESTRATOR. Two distinct passes, not one.

**Models:**
- **Triage pass (Stage 3.5):** L2 (Sonnet 4.6) — bounded judgment to surface obvious conflicts
- **Full pass (Stage 5):** L4 (Opus 4.7 frontier) — cross-corpus reasoning under ambiguity

See `MODEL_POLICY.md`.

---

## PASS 1 — Triage (runs after Stage 3, before Stage 4)

Goal: feed Stage 4 (gap-fill) with high-priority contradictions that need a tiebreaker source.

**Action:** read `03-synthesis.md` + the evidence ledger. Surface the top 3-7 OBVIOUS conflicts (factual disagreements that any reader would spot). For each:

```markdown
## Triage contradiction T-{{N}}: {{label}}
**Claim A:** "{{text}}" `[admiralty]` — claim_id, source
**Claim B:** "{{text}}" `[admiralty]` — claim_id, source
**Why this matters for the thesis:** {{1 sentence}}
**Tiebreaker needed:** {{specific evidence type}} — feeds Stage 4 as gap with id `gap-from-T-{{N}}`
```

Write to `~/workspace/research/{{session_id}}/03b-triage-contradictions.md`.

These triage contradictions automatically become Stage 4 gap-fill targets (one gap-fill agent per triage contradiction, in addition to other gaps from synthesis).

**Don't try to resolve** at triage — just surface and route to Stage 4. The full pass at Stage 5 does resolution.

---

## PASS 2 — Full contradiction & inconsistency detection (Stage 5, after Stage 4)

Goal: authoritative pass with full corpus available, including gap-fill results.

Read everything:
- `~/workspace/research/{{session_id}}/corpus/evidence-ledger.jsonl`
- All reports in `01-breadth/`, `02-depth/`, `04-gap-fill/`
- `03-synthesis.md` and `03b-triage-contradictions.md`

### Pass 2a: Cross-source contradictions

For every meaningful claim in the corpus, check whether another source contradicts it. Look for:
- Direct factual conflicts ("X happened in 2024" vs "X happened in 2025")
- Conflicting interpretations ("X is good" vs "X is harmful")
- Conflicting magnitudes ("X is 10x faster" vs "X is 2x faster")
- Conflicting causality ("X caused Y" vs "Y caused X" or "no causal link")
- Conflicting scope ("X affects all users" vs "X affects only segment A")

For each contradiction, document:

```markdown
## Contradiction C-{{N}}: {{short label}}

**Claim A:** "{{exact text}}" `[admiralty]` — claim_id, source URL
**Claim B:** "{{exact text}}" `[admiralty]` — claim_id, source URL

**Type:** factual / interpretive / magnitude / causal / scope

**Resolution method (in priority order):**
1. Higher Admiralty wins → {{which one}}, why
2. Newer source wins (date-sensitive claim) → check `publication_date` on both
3. Primary > secondary > tertiary → check `source_type`
4. Independent corroboration wins (more independence_clusters supporting it)
5. Domain-expert source wins (specialty match) → which one and why
6. If still tied → present both with explicit "unresolved" tag

**Resolution:** {{the chosen winning claim_id, or "unresolved — both presented"}}

**Action:** [resolved / dispatch tiebreaker subagent / present both with caveat]
```

### Pass 2b: Internal inconsistencies

Within a single source or within the assembled synthesis, look for:
- A source that contradicts itself (claim X in section 1, ¬X in section 4)
- The synthesis stating something the corpus doesn't actually support
- Citations that don't match the cited source's content (citation drift)
- Claims with verdict `true` but Admiralty grade D-F (red flag)
- Claims with grade `1` but only one `independence_cluster` (rule violation)

For each inconsistency, document and decide: keep, revise, or drop.

### Tiebreaker dispatch

When a contradiction is unresolvable from existing corpus AND the question matters for the final theory, dispatch ONE `research-expert` subagent with a tiebreaker brief. Write tiebreaker output to `04-gap-fill/tiebreaker-{{N}}.md` and update evidence ledger. Re-run Pass 2a on the affected claims with the new evidence.

## Output

Write `~/workspace/research/{{session_id}}/05-contradictions.md` containing:
- Cross-reference to triage contradictions from Pass 1 (and whether Stage 4 gap-fills resolved them)
- All Pass 2 contradictions documented with resolution status
- All Pass 2 inconsistencies with action taken
- Summary header:
  - Total contradictions found
  - % resolved automatically (Admiralty / date / source-type / independence)
  - % resolved by tiebreaker
  - % unresolved (and why)
  - Materiality breakdown: how many of the unresolved contradictions touch thesis-core claims

Update `run-manifest.json` with stage status.

## Hard rules — unified governance

These rules are authoritative. The fact-check stage and theory-draft stage reference these same numbers — do not let them drift.

1. **Do not silently resolve.** Every contradiction documented even if "resolved trivially."
2. **Unresolved is OK.** Must be flagged in final theory's confidence level.
3. **Don't manufacture contradictions.** Two sources disagreeing on minor wording isn't a contradiction. Reserve the label for material conflicts.
4. **Materiality classification:** label every contradiction as `thesis-core` (touches the central thesis), `material` (touches a main argument), or `peripheral` (background detail).
5. **Confidence ceiling rule:** if ≥30% of MATERIAL contradictions are unresolved, final theory confidence cannot exceed "medium". If ANY thesis-core contradiction is unresolved, confidence cannot exceed "low".
6. **Don't manufacture contradictions.** Wording disagreements aren't contradictions; reserve the label for material conflicts.
