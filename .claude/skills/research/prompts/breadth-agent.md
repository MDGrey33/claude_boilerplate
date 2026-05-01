# Breadth Subagent Prompt Template

Use this template when dispatching a `research-expert` subagent for Stage 1 (breadth scavenging). Substitute the `{{...}}` placeholders before sending.

**Model:** L2 (Sonnet 4.6) per `MODEL_POLICY.md`. Promote to L3 if topic is highly technical.

---

You are conducting BREADTH-FIRST research on the following question. Your job is to cover ground widely, NOT deeply. Other agents are working in parallel on different angles — yours is **{{angle}}** (e.g., "academic peer-reviewed sources" or "critic / counter-evidence" or "industry / commercial").

## Research question
{{refined_question}}

## Sub-questions to address
{{sub_questions_bulleted_with_ids}}

## Your specific angle
{{angle_brief}}

For example, if your angle is "critic / counter-evidence":
- Actively search for opposing viewpoints, debunkings, criticisms, failed implementations, and rebuttals
- Do NOT confirm the mainstream view — your job is to find what's wrong with it

If your angle is "academic":
- Prioritize arxiv, Google Scholar, ACL Anthology, journal databases
- Skip blog posts and news

## Output requirements

Write your report to: `<workspace>/research/{{session_id}}/01-breadth/agent-{{agent_id}}.md`

Structure:
```markdown
# Breadth Report — {{angle}}

## Sources surveyed
[list of URLs/titles you actually read, with publication and retrieval dates]

## Key findings
[bulleted findings, each one tagged inline using the credibility rubric]

## Notable contradictions surfaced
[claims you saw conflicting accounts of — flag for Stage 5]

## Sources NOT yet surveyed but relevant
[breadcrumbs for the depth iteration]
```

## MANDATORY: credibility & bias tagging

Every single claim in your report MUST be tagged inline using the rubric below. NO untagged claims. ALSO append every claim to the evidence ledger as a JSON line.

**The compliance gate after Stage 1 will REJECT your output if any claim is untagged or any enum value is invalid.** Re-dispatch happens once; second failure drops your contribution.

### Credibility rubric (NATO Admiralty + verdict + legal-status + bias + source-type)

**Admiralty source (letter):** A=completely reliable; B=usually reliable; C=fairly reliable; D=not usually reliable; E=unreliable; F=cannot judge.

**Admiralty info (number):** 1=confirmed by ≥2 INDEPENDENT reliable sources (different `independence_cluster` values); 2=probably true; 3=possibly true; 4=doubtful; 5=improbable; 6=cannot judge.

**Verdict:** `true` / `likely` / `contested` / `false` / `unknown`
**Legal-status:** `court-settled` / `contested` / `opinion` / `gossip`
**Bias (single enum, exact match):** `left` / `right` / `center` / `sponsored` / `neutral` / `unknown`
- `left/right/center` = political bias
- `sponsored` = paid/PR/marketing (overrides political)
- `neutral` = explicitly non-political (peer-reviewed science, primary gov data, court records)
- `unknown` = cannot determine

**Source type:** `primary` (original document, raw data, court record, peer-reviewed paper) / `secondary` (commentary, news report on a primary source) / `tertiary` (encyclopedic/aggregated) / `unknown`

### Inline tag format

> "Claim text here." `[B/2, likely, opinion, neutral]` (source: example.com/article, published 2026-03-15, retrieved {{retrieval_date}})

### Evidence ledger

For EVERY claim, also append a JSON line to: `<workspace>/research/{{session_id}}/corpus/evidence-ledger.jsonl`

```json
{
  "claim_id": "<ULID-or-UUIDv7>",
  "parent_claim_id": null,
  "refutes_claim_id": null,
  "claim": "<claim text>",
  "source_url": "<url>",
  "source_title": "<title>",
  "source_type": "<primary|secondary|tertiary|unknown>",
  "primary_secondary": "<primary|secondary>",
  "publication_date": "<YYYY-MM-DD or null>",
  "retrieved_at": "<ISO-8601 timestamp>",
  "excerpt": "<exact quoted text supporting the claim>",
  "quote_location": "<paragraph N | p. N | section X | null>",
  "language": "<ISO 639-1 code>",
  "admiralty": "<X/Y>",
  "verdict": "<true|likely|contested|false|unknown>",
  "legal_status": "<court-settled|contested|opinion|gossip>",
  "bias": "<left|right|center|sponsored|neutral|unknown>",
  "independence_cluster": "<domain root or org>",
  "agent_id": "{{agent_id}}",
  "stage": 1,
  "subquestion_id": "<Q1.1 | null>",
  "timestamp": "<ISO-8601 timestamp>"
}
```

**Independence rule:** if you tag `1` for info credibility, you must have ≥2 sources with different `independence_cluster` values supporting the claim. Otherwise downgrade to `2`.

## Boundaries

- DO NOT go deep on a single source — leave that for Stage 2
- DO NOT skip the tagging — compliance gate WILL reject untagged claims
- DO write to the file — don't return findings only in your reply summary
- DO note breadcrumbs for depth iteration
- DO record `excerpt` (the actual quoted source text) for every claim — paraphrase-only is rejected unless explicitly marked

## Time budget
~10–15 sources surveyed. Quality of tagging > quantity of sources.

## Return summary
Reply with under 200 words: top 3 findings (with tags), top 2 contradictions surfaced, count of ledger entries written, and the path to your written report.
