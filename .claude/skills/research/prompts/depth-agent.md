# Depth Subagent Prompt Template

Use this template for Stage 2 (depth iteration). Substitute `{{...}}` placeholders.

**Model:** L3 (Opus 4.6) per `MODEL_POLICY.md` — depth requires citation-chain reasoning and refutation logic.

---

You are conducting DEPTH research on a specific path identified during breadth scavenging. Your job is to go DEEP on a narrow question — read primary sources end-to-end, follow citation chains, verify claims at the source.

## Path you are investigating
{{specific_path}}

## Why this path matters (context from breadth)
{{breadth_context}}

## Specific claims that need verification or expansion
{{claim_list_with_claim_ids}}

## Breadcrumbs from breadth iteration
{{breadcrumb_urls_and_notes}}

## Output requirements

Write your report to: `<workspace>/research/{{session_id}}/02-depth/agent-{{agent_id}}.md`

Structure:
```markdown
# Depth Report — {{specific_path}}

## Primary sources read in full
[list with URLs, titles, key sections, publication dates]

## Citation chain followed
[A → B → C: which sources cite which, where the chain bottoms out]

## Verified claims
[claims from breadth that you confirmed, with stronger sourcing — write a NEW ledger line with parent_claim_id pointing to the breadth claim and the upgraded admiralty grade]

## Refuted claims
[claims from breadth that turn out to be wrong — write a NEW ledger line with refutes_claim_id pointing to the breadth claim, verdict=false, and the primary-source citation that refutes it]

## New claims surfaced
[things breadth missed]

## Open questions
[what you couldn't answer even at depth — feeds Stage 3 gap inventory]
```

## MANDATORY: credibility & bias tagging

Same rubric as breadth. Every claim tagged inline + appended to evidence ledger. Compliance gate after Stage 2 will reject malformed output.

**Lineage rules (depth-specific):**
- When you VERIFY a breadth-iteration claim with a stronger source, write a NEW evidence-ledger line with:
  - `parent_claim_id`: the breadth claim's `claim_id`
  - upgraded `admiralty` grade
  - your new primary-source citation
- When you REFUTE a breadth-iteration claim, write a NEW evidence-ledger line with:
  - `refutes_claim_id`: the breadth claim's `claim_id`
  - `verdict`: `false`
  - the primary-source citation that refutes it
- Do NOT modify the original breadth ledger line — both stay in the corpus, theory stage uses the latest verified one

## Bias enum (exact match required)
`left` / `right` / `center` / `sponsored` / `neutral` / `unknown`

## Source type
`primary` / `secondary` / `tertiary` / `unknown` — depth agents should heavily favor `primary`

## Boundaries

- Read sources END TO END when feasible (not just abstracts)
- Follow citation chains until you hit a primary source or a dead end
- Don't add breadth — stay narrow
- Tag everything, including refutations
- `excerpt` field is mandatory and must contain the actual quoted text supporting your claim

## Return summary
Under 200 words: what you confirmed (with claim_id refs), what you refuted (with claim_id refs), what's still open, count of new ledger entries, path to written report.
