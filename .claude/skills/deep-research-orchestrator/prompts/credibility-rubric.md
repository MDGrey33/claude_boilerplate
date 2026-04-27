# Credibility & Bias Rubric

Every claim picked up by a research subagent MUST be tagged inline with this rubric. Tags also go into `corpus/evidence-ledger.jsonl` as one JSON line per claim.

The compliance gate (`prompts/compliance-gate.md`) rejects untagged claims and invalid enum values before downstream stages consume them. Schema drift between this rubric and the SKILL.md or subagent prompts is a bug — fix here first, then propagate.

## Admiralty Code (NATO STANAG 2511)

### Source reliability (letter)
- **A** — Completely reliable: peer-reviewed journals, primary government documents, court records, audited financials, Tier-1 academic institutions
- **B** — Usually reliable: established news outlets with editorial standards, secondary academic, industry leaders' official communications
- **C** — Fairly reliable: trade press, established blogs by domain experts, well-sourced Wikipedia, reputable analyst firms
- **D** — Not usually reliable: anonymous sources, partisan outlets, non-expert blogs, marketing material
- **E** — Unreliable: known disinformation outlets, hostile-actor sources, AI-generated unsourced content
- **F** — Reliability cannot be judged: new source, no track record, anonymous

### Information credibility (number)
- **1** — Confirmed by multiple **independent** reliable sources (see independence rule below)
- **2** — Probably true: consistent with other information, plausible
- **3** — Possibly true: reasonable but not corroborated
- **4** — Doubtful: inconsistent with other information
- **5** — Improbable: contradicted by other reliable info
- **6** — Cannot be judged

Format: `[B/2]` means usually-reliable source with probably-true information.

### Independence rule for grade `1`

A claim earns `1` only if it is confirmed by ≥ 2 sources from **different `independence_cluster` values**. Five rewrites of the same press release belong to one cluster and count as ONE source.

**`independence_cluster` is a single string** identifying the most specific source family. Use this precedence (most specific first):

1. **Parent organization or media-group identifier** when sources share a corporate parent (e.g., `cnn-warner-bros-discovery`, `nyt-company`)
2. **Syndication wire service** when content is republished from a wire (e.g., `reuters`, `ap`, `afp`) — overrides the carrier domain
3. **Domain root** as the default (e.g., `anthropic.com`, `arxiv.org`, `nature.com`)

Default to `unknown` if you cannot determine any of the three.

Example: a Reuters story republished on five different newspaper sites all share `independence_cluster: "reuters"` and count as ONE source for the `1` grade. A primary Anthropic announcement on anthropic.com uses `independence_cluster: "anthropic.com"`.

## Verdict scale (PolitiFact-style)
- **true** — claim is accurate as stated
- **likely** — claim is mostly accurate, minor caveats
- **contested** — credible sources disagree
- **false** — claim is contradicted by reliable evidence
- **unknown** — insufficient evidence to judge

## Legal-status overlay
- **court-settled** — adjudicated in a court of competent jurisdiction
- **contested** — under dispute, in litigation, or actively challenged
- **opinion** — explicitly framed as opinion / editorial / analyst view
- **gossip** — rumor, unsourced, or anonymous-only

## Bias (normalized vocabulary — single enum)

**Use exactly one value from this list. The compliance gate rejects anything else.**

- **left** — politically left-leaning source (per AllSides / Ad Fontes Media)
- **right** — politically right-leaning source
- **center** — politically center / neutral on partisan issues (use this for non-extreme political sources, not for technical/scientific content)
- **sponsored** — paid content, ad, press release, vendor whitepaper, marketing material (overrides political bias if both apply)
- **neutral** — explicitly non-political content (peer-reviewed science, technical specs, court records, primary government data, audited financials). Use sparingly — much "neutral-looking" content has subtle bias
- **unknown** — cannot determine

**Disambiguation rule:** if a source is both political AND sponsored, tag `sponsored` (the funding source dominates). If a source is political but specifically neutral on the topic at hand (e.g., a partisan outlet's straight news report), use the political tag, not `neutral`.

## Source type
- **primary** — original document, court record, official statement, raw data, peer-reviewed paper, eyewitness account, original interview
- **secondary** — analysis, commentary, summary, news report on a primary source
- **tertiary** — encyclopedic or aggregated content (Wikipedia, news roundups, AI-summarized content)
- **unknown** — cannot determine

`primary_secondary` is derived from this: primary → `primary`, secondary/tertiary → `secondary`.

## Inline tagging format

In subagent reports, tag every claim like this:

> "Anthropic released Claude Opus 4.7 in early 2026" `[A/1, true, court-settled, neutral]` (source: anthropic.com/news, 2026-01-15)

> "Competitor X is failing internally" `[D/4, contested, gossip, unknown]` (source: anonymous Reddit thread, 2026-03-02)

## Evidence ledger format

One JSON object per line in `corpus/evidence-ledger.jsonl`. **All fields required** unless marked nullable:

```json
{
  "claim_id": "ULID-or-uuid-v7",
  "parent_claim_id": null,
  "refutes_claim_id": null,
  "claim": "Anthropic released Claude Opus 4.7 in early 2026",
  "source_url": "https://anthropic.com/news/...",
  "source_title": "Anthropic news — Opus 4.7 release",
  "source_type": "primary",
  "primary_secondary": "primary",
  "publication_date": "2026-01-15",
  "retrieved_at": "2026-04-27T10:15:00Z",
  "excerpt": "...we are releasing Claude Opus 4.7...",
  "quote_location": "paragraph 1",
  "language": "en",
  "admiralty": "A/1",
  "verdict": "true",
  "legal_status": "court-settled",
  "bias": "neutral",
  "independence_cluster": "anthropic.com",
  "agent_id": "breadth-3",
  "stage": 1,
  "subquestion_id": "Q1.2",
  "timestamp": "2026-04-27T10:15:00Z"
}
```

### Field meanings

- **claim_id** — unique ID for this claim (use ULID or UUID v7 — sortable). Used for cross-references.
- **parent_claim_id** — if this claim refines/upgrades an earlier claim, point to it. Use for depth-stage upgrades of breadth claims. Null otherwise.
- **refutes_claim_id** — if this claim refutes an earlier claim, point to it. Both claims stay in ledger; theory stage uses the latest verified one.
- **publication_date** — when the source was published. Required when feasible (warn on missing). Used by contradiction stage's "newer wins" rule.
- **retrieved_at** — when the agent fetched the source. Always required.
- **excerpt** — the actual quoted text from the source supporting the claim. Empty string only if claim is paraphrased and no quote applies.
- **quote_location** — where in the source ("paragraph 3", "p. 17", "section 2.1"). Nullable.
- **language** — ISO 639-1 code (en, lv, de, ru). Used for language-coverage check.
- **independence_cluster** — domain root or parent organization. Used for grade `1` independence check.
- **subquestion_id** — which Stage 0 sub-question this answers. Nullable.

## Hard rules

1. **No untagged claims.** Compliance gate rejects untagged. Drop or mark `[F/6, unknown, gossip, unknown]` with explanation if you must keep.
2. **Tag at collection time, not after.** Post-hoc tagging defeats the purpose.
3. **D-F sources flagged for gap-fill.** Compliance gate auto-populates `gap-candidates.jsonl` from D-F entries.
4. **Sponsored content not banned**, but must be tagged. Many vendor whitepapers contain useful primary data.
5. **Bias ≠ credibility.** A left-biased A-source is still A/1 if the specific factual claim is well-sourced.
6. **claim_id is mandatory and unique.** No duplicate IDs in the ledger.
7. **Independence required for grade 1.** Single-source claims max out at `1`'s sibling grade `2`, even from an A-source.
