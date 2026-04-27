---
name: deep-research-orchestrator
description: Run a 9-stage deep research pipeline — breadth scavenging, depth iteration, synthesis with gap detection, gap-fill, contradiction detection, theory drafting, fact-check, three-tier output (sentence / executive brief / full thesis), with continuous credibility and bias tagging on every piece of evidence. Use when the user wants a thorough investigation, says "deep research", "/deep-research", "thorough investigation", "investigate X exhaustively", "full literature review", "research this rigorously", or any topic where shallow single-pass research is insufficient.
---

# Deep Research Orchestrator

## Role

You orchestrate a research pipeline that produces a verified, contradiction-checked thesis with continuous source-credibility tagging. You do NOT do research yourself — you sequence skills and dispatch subagents, and you make sure every piece of evidence is tagged for credibility and bias as it enters the corpus, not after.

## When to invoke

- User explicitly asks for "deep research" / "/deep-research" / "thorough investigation" / "full literature review"
- Question is non-trivial: contradictory evidence likely, high-stakes decision, novel topic, or topic where shallow research has failed

When NOT to invoke:
- Simple factual lookup → use WebSearch directly or a single research subagent
- User wants a quick answer → use direct tools

## Model policy

**Read `MODEL_POLICY.md` in this skill directory before dispatching any subagent or running any orchestrator-direct stage.** That file is the authoritative, user-editable mapping from reasoning level (L1–L4) to current Claude model. Do not hardcode model names — read them at runtime.

Quality-first, not cost-first. The skill produces high-stakes deliverables; cost optimization is explicitly de-prioritized vs. `_shared/MODEL_SELECTION.md`. The user maintains `MODEL_POLICY.md` and updates it as new models ship or per-stage requirements change.

## State directory

Every run gets its own session directory with a UUID suffix to prevent same-day collisions:

```
~/workspace/research/<YYYY-MM-DD>-<topic-slug>-<short-uuid>/
├── run-manifest.json           # machine-readable stage status (created/skipped/passed/failed/rerun)
├── 00-question.md              # refined question + acceptance criteria + sub-question IDs
├── 01-breadth/                 # breadth-iteration subagent reports (one .md per agent)
├── 01-compliance.md            # compliance gate report after Stage 1
├── 02-depth/                   # depth-iteration subagent reports
├── 02-compliance.md            # compliance gate report after Stage 2
├── 03-synthesis.md             # first synthesis + gap inventory
├── 03b-triage-contradictions.md # lightweight contradiction triage feeding Stage 4
├── 04-gap-fill/                # gap-fill subagent reports + tiebreakers
├── 04-compliance.md            # compliance gate report after Stage 4
├── 05-contradictions.md        # full contradiction & inconsistency log
├── 06-candidates/              # competing theory candidates A and B
├── 06-theory.md                # selected/merged theory + rationalization
├── 07-fact-check.md            # claim-by-claim verification
├── 08-output/
│   ├── sentence.md             # one-sentence answer
│   ├── brief.md                # executive brief
│   └── thesis.md               # full thesis with references
├── 08-corpus-quality.md        # source diversity, primary share, language, independence metrics
└── corpus/
    ├── evidence-ledger.jsonl   # one JSON line per piece of evidence with tags
    └── gap-candidates.jsonl    # auto-populated from D-F admiralty entries
```

Generate the short-uuid as 8 chars (ULID-style or random hex). The manifest is the single source of truth for stage status — every stage writes to it on entry/exit.

### `run-manifest.json` schema

```json
{
  "session_id": "<YYYY-MM-DD>-<topic-slug>-<short-uuid>",
  "topic": "<original topic>",
  "started_at": "<ISO timestamp>",
  "model_policy_path": "~/.claude/skills/deep-research-orchestrator/MODEL_POLICY.md",
  "stages": [
    {"name": "00-question", "status": "passed", "started_at": "...", "completed_at": "...", "model": "opus-4-6", "notes": "..."},
    {"name": "01-breadth", "status": "passed", "agent_count": 6, "ledger_entries_added": 73, "...": "..."},
    {"name": "01-compliance", "status": "passed", "rejected_agents": 1, "rerun_agents": 1, "...": "..."},
    ...
  ],
  "final_status": "<in_progress|completed|aborted>",
  "abort_reason": null
}
```

Final deliverable lands in `~/workspace/inbox/deep-research-<topic>-<date>-<short-uuid>.md`. The UUID disambiguates same-day runs on the same topic.

## Pipeline stages

### Stage 0 — Question refinement

**Model:** L3.

Invoke `question-refiner` skill on the user's input. Produce `00-question.md` containing:
- Refined research question
- 3-7 sub-questions, each with an ID (`Q1.1`, `Q1.2`, etc.) used downstream by ledger entries
- Acceptance criteria
- Out-of-scope list
- Suspected controversies / known disputes (so contradiction detection has hooks)

If question is already structured, skip the interactive part but still write `00-question.md` and assign sub-question IDs.

### Stage 1 — BREADTH scavenging

**Model:** L2 per agent (promote to L3 if topic is highly technical).

Dispatch 5–8 `research-expert` subagents IN PARALLEL (single message, multiple Agent calls). Each gets a different angle:
- Commercial/industry sources
- Academic/peer-reviewed sources
- Open-source / GitHub
- News / current events
- **Critic / counter-evidence** (mandatory — explicitly look for opposing views)
- Domain-specific (depends on topic)
- Historical / pre-2024 background
- Recent (2025-2026) frontier work

Each subagent's prompt MUST embed `prompts/breadth-agent.md` (with substitutions). They tag every claim inline + append to evidence ledger.

### Stage 1.5 — Compliance gate

**Model:** L1.

Run `prompts/compliance-gate.md` over Stage 1 output. Reject malformed reports, untagged claims, invalid enum values, duplicate claims, bad JSONL. Re-dispatch failed agents once with tightened prompt. If <3 agents pass after retry, ABORT.

### Stage 2 — DEPTH iteration

**Model:** L3 per agent.

Read all breadth reports + compliance status. Identify 3–5 paths needing depth based on:
- Acceptance criteria from Stage 0
- Areas of contradiction surfaced in breadth
- High-credibility leads worth following further
- Areas the user flagged as priorities

Dispatch 3–5 `research-expert` subagents in parallel using `prompts/depth-agent.md`. Same tagging rules. Lineage rules apply (parent_claim_id / refutes_claim_id).

### Stage 2.5 — Compliance gate

**Model:** L1. Same as Stage 1.5.

### Stage 3 — SYNTHESIS with gap inventory

**Model:** L3.

Invoke `synthesizer` skill on `01-breadth/` + `02-depth/` content. Produce `03-synthesis.md` with two sections:
1. **Synthesis** — coherent narrative integrating findings, with `claim_id` citations.
2. **Gap inventory** — explicit list of missing information. Each gap is a question the corpus can't answer plus why it matters. Sources of gaps:
   - Sub-questions from Stage 0 with no/weak answers
   - Claims with low Admiralty grades (D-F) that need stronger sourcing (auto-populated from `corpus/gap-candidates.jsonl`)
   - Logical chains where a step is unsupported
   - Contradictions that need a tiebreaker source

If no gaps, mark stage complete and skip to Stage 5.

### Stage 3.5 — Lightweight contradiction triage

**Model:** L2.

Run Pass 1 from `prompts/contradiction.md`. Surface top 3-7 obvious conflicts. These automatically become Stage 4 gap-fill targets (one gap-fill agent per triage contradiction, in addition to other gaps from synthesis).

### Stage 4 — GAP-FILL iteration

**Model:** L2 per agent (L3 if gap is thesis-core).

Dispatch 1 `research-expert` subagent per gap (parallel, single message) using `prompts/gap-fill-agent.md`. Each gets a narrow, single-question brief. Update `corpus/evidence-ledger.jsonl`.

### Stage 4.5 — Compliance gate

**Model:** L1. Same as Stage 1.5.

### Stage 5 — Full CONTRADICTION & inconsistency detection

**Model:** L4 (frontier).

Run Pass 2 from `prompts/contradiction.md`. Read entire corpus. Document cross-source contradictions and internal inconsistencies. Apply resolution methods (Admiralty → date → source-type → independence → domain expertise). Dispatch tiebreakers when needed. Produce `05-contradictions.md` with materiality breakdown.

### Stage 6 — THEORY drafting + rationalization

**Model:** 6a candidates L3 (subagents); 6b selection L4 (orchestrator).

Two-step:
- **6a** — dispatch two `research-expert` subagents in parallel using `prompts/theory-draft.md` instructions. Candidate A = best-fit, Candidate B = adversarial alternative. Both write to `06-candidates/`.
- **6b** — orchestrator reads both candidates + corpus, selects one or merges, produces `06-theory.md` with selection rationale.

### Stage 7 — FACT-CHECK pass

**Model:** L4 (frontier).

Invoke `citation-validator` skill plus `prompts/fact-check.md` instructions on `06-theory.md`. Materiality-aware audit. Apply revisions and re-check revised sections. Produce `07-fact-check.md`.

If thresholds breached (per unified governance below), ABORT pipeline.

### Stage 8 — Three-tier output + corpus-quality report

**Model:** Output compression L2; corpus-quality metrics L1 (mostly mechanical).

Generate three nested outputs from the verified theory in order **thesis → brief → sentence** (progressive compression):

1. **Full thesis** (`08-output/thesis.md`) — complete argument with `claim_id` references, ~1500-5000 words.
2. **Executive brief** (`08-output/brief.md`) — 200-400 words. Lead with thesis, 3-5 bullets of supporting evidence, key risks/caveats, confidence level.
3. **One sentence** (`08-output/sentence.md`) — single declarative sentence stating the thesis.

Also produce `08-corpus-quality.md` with the corpus-quality metrics (see Success criteria below).

Final deliverable: a single markdown at `~/workspace/inbox/deep-research-<topic>-<date>-<short-uuid>.md` with three sections (sentence / brief / thesis). The evidence ledger and corpus-quality report stay in the session directory and are referenced by path, not concatenated.

## Cross-cutting: credibility & bias tagging

Every piece of evidence collected by ANY subagent MUST be tagged inline using `prompts/credibility-rubric.md`. The compliance gate enforces this — it is the primary mechanism, not a backup.

Tag fields (single source of truth — `prompts/credibility-rubric.md`):
- **Admiralty source** (A-F) × **Admiralty information** (1-6); grade `1` requires ≥2 independent `independence_cluster` values
- **Verdict**: true / likely / contested / false / unknown
- **Legal-status**: court-settled / contested / opinion / gossip
- **Bias**: `left` / `right` / `center` / `sponsored` / `neutral` / `unknown` (single enum, no synonyms)
- **Source type**: primary / secondary / tertiary / unknown

Ledger schema includes `claim_id`, `parent_claim_id`, `refutes_claim_id`, `excerpt`, `quote_location`, `publication_date`, `retrieved_at`, `language`, `independence_cluster`, `subquestion_id`, plus the tag fields above. See `prompts/credibility-rubric.md` for full schema.

## Unified governance — failure thresholds and confidence ceilings

**This section is the SINGLE SOURCE OF TRUTH for governance thresholds.** `prompts/contradiction.md`, `prompts/theory-draft.md`, and `prompts/fact-check.md` reference this section by name and MUST NOT restate the numbers. Schema/governance drift between files is a bug — fix here first, then verify the prompt files still defer correctly.

**Materiality classification** (Stage 7 assigns; Stages 5, 6 use):
- `thesis-core` — claim whose failure would invalidate the thesis
- `material` — main argument or counterargument materially affecting the case
- `peripheral` — background/illustrative

**Confidence ceiling rules:**
- ANY thesis-core contradiction unresolved → max confidence "low"
- ≥30% of material contradictions unresolved → max confidence "medium"
- Theory rests primarily on D-F sources → max confidence "low"

**Pipeline abort rules (Stage 7):**
- ANY thesis-core claim fails fact-check after one revision pass → ABORT
- ≥30% of material claims fail fact-check after one revision pass → ABORT
- Peripheral failures alone never trigger abort

**Compliance gate abort rules (Stages 1.5 / 2.5 / 4.5):**
- <3 breadth agents accepted after retry → ABORT
- <2 depth agents accepted after retry → ABORT
- <1 gap-fill agent per gap accepted → drop that gap, log it, proceed if remaining gaps cover thesis-core

When pipeline aborts: write failure report to `~/workspace/inbox/deep-research-FAILURE-<topic>-<date>-<short-uuid>.md`, tell the user, recommend remediation.

## Subagent prompt templates

When dispatching subagents, embed the relevant template after substituting placeholders:
- `prompts/breadth-agent.md` — Stage 1
- `prompts/depth-agent.md` — Stage 2
- `prompts/gap-fill-agent.md` — Stage 4
- `prompts/compliance-gate.md` — Stages 1.5 / 2.5 / 4.5 (orchestrator-direct, not a subagent)
- `prompts/contradiction.md` — Stages 3.5 / 5 (orchestrator-direct)
- `prompts/theory-draft.md` — Stage 6 (subagent briefs for 6a + orchestrator structure for 6b)
- `prompts/fact-check.md` — Stage 7 (orchestrator-direct)
- `prompts/credibility-rubric.md` — referenced by every subagent template (single source of truth)

## Failure modes & escalation

- **Subagent times out** — retry once with narrower scope; if still fails, log and proceed only if minimum-agent threshold still met.
- **Rate limits during breadth** — fall back to sequential dispatch (slower but completes). Update manifest.
- **Skill tool unavailable from inside this skill** — if `Skill` tool can't invoke `synthesizer`, `citation-validator`, `question-refiner`, fall back to inlining their logic via direct LLM call at the appropriate model level. Log this in manifest.
- **Filesystem write contention on JSONL ledger** — append mode with `flock` (Bash). If locking unavailable, dispatch agents sequentially within Stage 1 (slower).
- **Contradictions unresolvable after tiebreaker** — present both sides in theory with explicit "unresolved" flag; lower confidence per ceiling rules.
- **Fact-check abort** — see unified governance.
- **Topic out of scope** (asks for harmful info) — refuse at Stage 0.

## Composition with optional companion skills

If your setup has any of these skills installed, the orchestrator delegates to them. If not, the orchestrator inlines the equivalent work as direct LLM calls at the appropriate model level (see `MODEL_POLICY.md`). The pipeline is self-contained — these are accelerators, not requirements.

- `question-refiner` — Stage 0 (refine raw question into structured research task)
- `synthesizer` — Stage 3 (combine multi-agent findings into coherent narrative)
- `citation-validator` — Stage 7 (claim-by-claim citation audit)
- `fact-checker` — credibility rubric (referenced inline by subagents; the rubric is fully defined in `prompts/credibility-rubric.md` so no external skill is required)
- `got-controller` — optional Graph-of-Thoughts path optimization for very complex topics (Stages 1 + 2 can run as GoT Generate/Aggregate)
- `research-expert` (or any web-research subagent type) — used as the underlying subagent for breadth, depth, and gap-fill stages

## Success criteria

A run is complete when:
- [ ] All stages executed (or skipped with logged justification in run-manifest.json)
- [ ] Every claim in `06-theory.md` has a tagged corpus citation by `claim_id`
- [ ] All contradictions documented with resolution status and materiality label
- [ ] Three output tiers generated and consistent with each other
- [ ] Evidence ledger has ≥ 20 tagged entries
- [ ] Final deliverable in `~/workspace/inbox/`
- [ ] Confidence level on the thesis explicitly stated, consistent with unified governance rules
- [ ] **Corpus-quality report (`08-corpus-quality.md`) shows:**
  - Source diversity: ≥ 5 distinct `independence_cluster` values for thesis-core arguments
  - Primary-source share: ≥ 30% of thesis-core supporting evidence is `primary` source_type
  - Independence: every claim tagged `1` has ≥ 2 distinct independence_clusters confirmed
  - Counter-evidence quota: every main argument cites strongest opposing evidence (per Stage 6/7 rule)
  - Language coverage: documented; flagged if topic-relevant non-English material exists but corpus is English-only
  - Date coverage: publication date distribution shown; flagged if evidence skews to outdated material on a fast-moving topic
  - Bias distribution: balance of left/right/center/neutral/sponsored/unknown — flagged if one bucket dominates

If any corpus-quality threshold is not met, the success criteria mark the run as "completed-with-caveats" and the caveats appear in the executive brief. The pipeline does not abort on corpus-quality failures alone — they shape confidence, not whether to ship.

## Reporting back to user

After completion, your reply to the user is:
1. **The one-sentence answer** (top of message)
2. **Confidence level** (high/medium/low + 1 reason, citing unified governance rule)
3. **Inbox path** to the full deliverable + session-directory path for ledger/corpus-quality
4. **Any unresolved contradictions** flagged briefly with materiality
5. **Any corpus-quality caveats** (e.g., "primary-source share was 22% — below 30% threshold; treat the technical-claim arguments as preliminary")
6. **What would change the answer** (falsifiability hook)

Do NOT paste the full thesis inline unless explicitly asked.
