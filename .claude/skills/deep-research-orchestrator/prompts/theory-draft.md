# Stage 6 — Theory Drafting + Rationalization (with competing candidates)

Two-step stage: subagents generate competing theories, orchestrator selects/merges.

**Models:**
- **6a Candidate generation (subagents):** L3 (Opus 4.6) — two concurrent agents with adversarial framings
- **6b Selection / merge (orchestrator):** L4 (Opus 4.7 frontier) — final editorial reasoning

See `MODEL_POLICY.md`.

---

## STAGE 6a — Candidate theory generation (parallel subagents)

Dispatch TWO `research-expert` subagents in parallel with adversarial framings:

### Candidate A — Best-fit theory
Brief: "Read the corpus and synthesis. Draft the theory that best fits the WEIGHT of available evidence. Be charitable to the dominant interpretation. Use the structure below."

### Candidate B — Adversarial alternative
Brief: "Read the corpus and synthesis. Draft the strongest ALTERNATIVE theory — the one that would emerge if the dominant interpretation is wrong. Steelman the contrarian position. Use the structure below."

Both candidates write to `~/workspace/research/{{session_id}}/06-candidates/candidate-A.md` and `candidate-B.md`.

Both must have access to:
- `03-synthesis.md`
- `03b-triage-contradictions.md`
- `05-contradictions.md`
- `corpus/evidence-ledger.jsonl`
- `00-question.md`

Each candidate uses the structure in Stage 6b below. Each candidate stays under 1500 words.

## STAGE 6b — Orchestrator selection and merge

You (the orchestrator, model L4) read both candidates and the corpus. Choose ONE of:
1. **Adopt Candidate A** — corpus weight clearly supports it, B is a strawman
2. **Adopt Candidate B** — A misses something material, B captures it
3. **Merge** — synthesize a theory that incorporates the strongest elements of both. Most common outcome.
4. **Reject both, draft a third** — both candidates miss the mark; rare but valid

Document your selection reasoning in a "## Selection rationale" section at the top of `06-theory.md` before the theory itself.

## Required structure for `06-theory.md`

```markdown
# Theory: {{topic}}

## Selection rationale
[Which candidate (A, B, merged, or third) and why. Reference both candidates explicitly. 100-300 words.]

## Thesis (1-2 sentences)
{{the claim being made — declarative, falsifiable}}

## Confidence
[high / medium / low]

**Reasoning:** {{1-3 sentences on confidence level, referencing materiality of unresolved contradictions per Stage 5 rules}}

## Argument 1: {{label}}
**Claim:** {{supporting argument}}
**Materiality:** thesis-core / material / peripheral
**Evidence:**
- {{evidence point}} `[admiralty]` (claim_id from ledger)
- {{evidence point}} `[admiralty]` (claim_id from ledger)
**Counter-evidence considered:** {{strongest opposing evidence, with claim_id}}
**Why this supports the thesis despite the counter-evidence:** {{logic}}

[repeat for arguments 2-7]

## Counterarguments considered (system-level)
### CA1: {{counterargument}}
**Sources:** {{claim_ids}}
**Why it does NOT overturn the thesis:** {{response}}

[repeat]

## Unresolved contradictions affecting the thesis
{{list from Stage 5, with materiality labels}}

## Falsifiability — what would change this answer
- {{specific evidence type that would weaken thesis}}
- {{specific evidence type that would strengthen thesis}}

## Open questions for future research
{{anything the corpus couldn't address}}
```

## Hard rules — unified governance

1. **Every claim cites the corpus by `claim_id`.** No new claims introduced at this stage. If you need a claim that isn't in the corpus, dispatch a gap-fill subagent first.
2. **Counter-evidence quota:** every main argument must include the STRONGEST opposing evidence found in the corpus, not the weakest. The fact-check stage verifies this.
3. **Confidence ceiling.** Apply the materiality-aware thresholds defined in `SKILL.md` "Unified governance — failure thresholds and confidence ceilings" section. Do not redefine them here — that section is the canonical source. If a threshold needs to change, edit it in SKILL.md only.
4. **Don't bury counterarguments.** Their own section, addressed head-on.
5. **Be willing to conclude "the question is unanswerable from current evidence."** Valid theory.
6. **The thesis must be falsifiable.** "It's complex" is not a thesis. State what you actually believe and what would prove you wrong.

## Anti-patterns to avoid

- Hedging into meaninglessness ("it depends, more research is needed")
- Cherry-picking favorable evidence
- Inflating confidence past corpus support
- Confusing "everyone in the corpus agrees" with "true" — check whether the corpus is biased (use the corpus-quality metrics from Stage 5/8)
- Adopting Candidate A by default because it sounded better — re-read Candidate B's strongest arguments before deciding
