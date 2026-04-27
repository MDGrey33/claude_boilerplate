# Stage 7 — Fact-Check Pass

This is a reasoning prompt for the ORCHESTRATOR.

**Model:** L4 (Opus 4.7 frontier) per `MODEL_POLICY.md` — adversarial audit requires frontier reasoning.

Run after Stage 6.

---

Read `06-theory.md`. For EVERY claim made in the theory (arguments, counterarguments, confidence reasoning, falsifiability conditions), audit.

## Materiality classification (REQUIRED first step)

Before auditing, classify every claim in the theory as one of:
- **thesis-core** — the central thesis itself, or any claim whose failure would invalidate the thesis
- **material** — a main argument or counterargument that materially affects the case
- **peripheral** — background context, illustrative example, or non-load-bearing detail

The materiality label determines failure-policy weight (see "Failure thresholds" below).

## Three checks per claim

1. **Cited?** Does the claim point to a specific `claim_id` in the evidence ledger? If no → revise to add citation OR drop the claim.
2. **Admiralty grade.** Is the cited source A or B?
   - C → keep but note
   - D-F → flag, attempt to find a stronger source via gap-fill subagent OR weaken the claim's language ("some sources suggest" instead of "X is true")
3. **Source actually supports the claim?** Open the source via the ledger's `source_url` and `excerpt` field. Does the excerpt actually say what the theory uses it to say? Common failure: citation drift / over-interpretation. If no → revise the claim to match what the source actually says, or drop.

## Special checks

- **Counterargument citations.** Counterarguments must also be properly cited. A strawman counterargument is worse than none.
- **Counter-evidence quota check.** Every main argument should include the STRONGEST opposing evidence in the corpus (per Stage 6 rule). Verify by searching the ledger for claims with `verdict: contested` or `refutes_claim_id` matching the argument's evidence — was the strongest one cited?
- **Confidence-reasoning citations.** If you said "confidence is medium because X," verify X is in the corpus and references Stage 5 contradiction stats correctly.
- **Falsifiability check.** The "what would change my mind" section should be plausible — not a strawman that obviously can't happen.
- **Independence check on grade-1 claims.** If the theory rests on a claim tagged `1`, verify ≥2 different `independence_cluster` values support it. If not, downgrade to `2` and re-audit confidence.

## Output

Write `~/workspace/research/{{session_id}}/07-fact-check.md` with the claim audit table — every claim, every check.

Structure:

```markdown
# Fact-Check Audit

## Claim audit table

| # | Claim (truncated) | Materiality | Cited? | Admiralty | Source supports? | Verdict |
|---|---|---|---|---|---|---|
| 1 | {{claim}} | thesis-core | yes | A/1 | yes | pass |
| 2 | {{claim}} | material | yes | C/3 | over-interpreted | revise |

## Failures

### thesis-core failures
[any thesis-core claim that failed any check — these are FATAL]

### material failures
[material claims that failed]

### peripheral failures
[peripheral claims that failed — informational, low-impact]

## Revisions applied
[changes made to 06-theory.md, with diff]

## Sources upgraded / downgraded
[ledger entries whose admiralty changed during the audit, with reasons]

## Counter-evidence quota check
[per-argument check that strongest counter-evidence was cited]

## Pass 2 (after revisions)
[mini-fact-check on revised sections only]
```

## After the audit

If audit produced revisions:
- Apply them to `06-theory.md` (overwrite, don't fork)
- Re-run a mini fact-check on ONLY the revised sections
- Document the second pass under "Pass 2"

## Failure thresholds

**The canonical thresholds live in `SKILL.md` "Unified governance — failure thresholds and confidence ceilings".** Apply them here; do not restate them. If a threshold needs to change, edit SKILL.md only.

What this stage adds on top of those canonical thresholds:

- **Materiality classification is performed HERE** (Stage 7). Stages 5 and 6 reference the labels you assign.
- **Audit applies after one revision pass.** Run the full audit, apply revisions, run a mini-audit on revised sections only. The abort decision uses post-revision pass-rates against the SKILL.md thresholds.
- **Peripheral failures never abort** — they get logged in the audit table and either fixed or dropped silently.

When pipeline aborts:
- Write failure report to `~/workspace/inbox/deep-research-FAILURE-<topic>-<date>.md`
- Tell the user: corpus is too weak to support a theory at acceptable rigor
- Recommend: more breadth, different research question, or accept lower-confidence output

This is not orchestrator failure — it's the right outcome when evidence isn't there. Do not deliver a theory the corpus can't support.

## Hard rules

1. **No claim escapes audit.** Every sentence with a factual assertion is audited.
2. **Citations to "the synthesis" don't count.** Synthesis is derivative — trace back to underlying source via `claim_id`.
3. **Open the source.** Don't trust the agent's quoted excerpt — verify against the actual URL when feasible. Sample-check at least 30% of citations even when the excerpt looks fine.
4. **Be the adversary.** Read the theory as someone trying to find holes, not as someone trying to ship.
5. **Materiality labels are sticky.** Once classified, don't re-label down to make a failure go away.
