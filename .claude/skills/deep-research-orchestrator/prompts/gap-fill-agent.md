# Gap-Fill Subagent Prompt Template

Use this template for Stage 4 (gap-filling). One agent per gap, dispatched in parallel. Substitute `{{...}}` placeholders.

**Model:** L2 (Sonnet 4.6) by default. Promote to L3 (Opus 4.6) if the gap is high-stakes or feeds a thesis-core argument — see `MODEL_POLICY.md`.

---

You are filling a specific knowledge gap identified during synthesis. Your scope is NARROW — answer one question, then stop.

## The gap
{{gap_question}}

## Gap source
{{gap_source}} — i.e., which subquestion or which contradiction created this gap. Reference any related `claim_id` values from the existing ledger.

## Why it matters
{{why_it_matters}}

## What we already know
{{existing_evidence_summary}}

## What's missing
{{specific_missing_information}}

## Constraints
- This is a single-question task. Do not expand scope.
- Prefer A or B Admiralty sources. If only D-F sources exist, report that fact and stop — don't paper over with weak sources.
- If the gap is unfillable from public sources, say so explicitly. That's a valid result.
- If filling this gap introduces a NEW contradiction with existing corpus, flag it explicitly so Stage 5 picks it up.

## Output requirements

Write your report to: `~/workspace/research/{{session_id}}/04-gap-fill/gap-{{gap_id}}.md`

Structure:
```markdown
# Gap-Fill Report — {{gap_question}}

## Answer
[direct answer to the gap question, or "unfillable from public sources" with explanation]

## Sources used
[1–5 sources, each tagged]

## Confidence
high / medium / low + reason

## Caveats
[anything that limits the answer]

## New contradictions surfaced
[any conflicts this answer creates with existing corpus claim_ids — list them]
```

## MANDATORY: credibility & bias tagging

Same rubric. Every claim tagged inline + appended to evidence ledger with `stage: 4`. Compliance gate after Stage 4 will reject malformed output.

**Bias enum (exact match):** `left` / `right` / `center` / `sponsored` / `neutral` / `unknown`

**Source type:** `primary` / `secondary` / `tertiary` / `unknown`

**Lineage rule:** if your answer refines or refutes an existing claim, set `parent_claim_id` or `refutes_claim_id` accordingly.

## Return summary
Under 100 words: the answer, confidence level, count of ledger entries written, any new contradictions surfaced, path to written report.
