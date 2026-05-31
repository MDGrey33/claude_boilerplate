---
name: research
description: Unified research skill with three depth modes. Use `--shallow` (single-pass parallel web search via the `research-expert` agent) for "quick research", "look up", "find me info on". Use `--standard` (decompose → parallel subagents → synthesize → cite-check) for "research X", "investigate". Use `--deep` (full 9-stage pipeline with breadth scavenging, depth iteration, gap-fill, contradiction detection, theory drafting, fact-check, three-tier output) for "deep research", "thorough investigation", "full literature review", "research this rigorously". Replaces the older `deep-research-orchestrator` skill.
---

# Research

## Role

You orchestrate a research pipeline at one of three depths. You do NOT do research yourself — you sequence stages and dispatch subagents. The `research-expert` agent (registered separately, not a skill) is the workhorse evidence-gatherer; this skill wraps it with depth-appropriate scaffolding.

## Depth selection

Pick depth from the user's phrasing. If ambiguous, default to `--standard`.

| Depth | Trigger phrases | What it does |
|---|---|---|
| `--shallow` | "quick research", "look up", "find me info on", short factual lookups | Decompose → invoke `research-expert` agent → return its report |
| `--standard` | "research X", "investigate", default for non-trivial questions | Decompose → 3–5 parallel `research-expert` subagents → synthesize → cite-check |
| `--deep` | "deep research", "thorough investigation", "full literature review", "research this rigorously" | Full 9-stage pipeline with manifest, contradictions, theory, fact-check, three-tier output |

## Model policy

**Read `MODEL_POLICY.md` in this skill directory before dispatching any subagent or running any orchestrator-direct stage.** That file is the authoritative, user-editable mapping from reasoning level (L1–L4) to current Claude model. Do not hardcode model names — read them at runtime.

**TEST_MODE.** Before reading the production tables, check `os.environ.get('TEST_MODE')`. If it equals `"1"`, every stage at every depth is pinned to `claude-haiku-4-5-20251001` (the model ID is in the TEST_MODE section of `MODEL_POLICY.md`). TEST_MODE deliverables go to `<workspace>/qa/research-skill-test/`, never `<workspace>/inbox/`. Surface a "TEST MODE" banner in the user-facing report so nobody mistakes it for a real research output.

Quality-first, not cost-first (production runs only). The skill produces high-stakes deliverables; cost optimization is explicitly de-prioritized for `--deep` and `--standard`. The operator maintains `MODEL_POLICY.md` and updates it as new models ship or per-stage requirements change.

---

## `--shallow` pipeline

Single-stage wrapper around the existing `research-expert` agent. No new logic, no manifest, no synthesis.

### S0 — Decompose (orchestrator-direct)

Take the user's query and produce 1–3 search angles. Keep it light — this is just to give the agent a structured brief, not a full sub-question tree. If the query is already specific (single named entity, single factual claim), skip and pass through verbatim.

### S1 — Invoke `research-expert` agent

Single Agent call:

```
Agent(
  subagent_type: "research-expert",
  prompt: "<user query> + <decomposed angles> + 'write report to /tmp/research_<slug>.md'"
)
```

The agent does its own parallel web search and writes its report to `/tmp/research_*.md`.

### S2 — Return

Read the agent's report file and return it verbatim to the user. No editorial changes, no re-synthesis. If the agent's report is empty or shorter than 200 chars, retry once with a tightened prompt; if still empty, surface the failure honestly.

**Output location (production):** the agent's `/tmp/research_*.md` file path returned to the user.
**Output location (TEST_MODE):** copy the agent report to `<workspace>/qa/research-skill-test/shallow-output.md`.

---

## `--standard` pipeline

Simplified pipeline. No manifest, no compliance gates, no contradiction stage, no theory stage. Just the spine: decompose → parallel search → synthesize → cite-check.

### ST0 — Decompose

Break the query into 3–5 sub-questions. Each gets a sub-question ID (`Q1`, `Q2`, ...) for downstream citation. Write to `<workspace>/research/<YYYY-MM-DD>-<slug>-<short-uuid>/00-question.md`.

If `question-refiner` skill is available and the user's query is vague, invoke it first. Otherwise inline the decomposition.

### ST1 — Parallel `research-expert` subagents (×3–5)

Dispatch 3–5 `research-expert` subagents IN PARALLEL (single message, multiple Agent calls). Each gets a different sub-question or angle. The subagents do their own web search and return reports.

Use `prompts/breadth-agent.md` as the embedded brief template (substitute the sub-question and acceptance criteria). Lighter compliance than `--deep` — no enforced credibility-rubric tagging — but encourage source citation.

Reports land in `<workspace>/research/<session>/01-search/`.

### ST2 — Synthesize

Invoke the `synthesizer` skill on the search reports. If unavailable, inline a synthesis pass at L3 that:
- Integrates findings into a coherent narrative
- Resolves obvious contradictions inline (no separate stage)
- Surfaces 3–5 key claims with citations to the source reports
- Flags any gaps as caveats but does NOT trigger a gap-fill stage

Output: `<workspace>/research/<session>/02-synthesis.md`.

### ST3 — Cite-check

Invoke `citation-validator` on the synthesis. If unavailable, run an inline pass at L2 that:
- Verifies every factual claim in `02-synthesis.md` has a source
- Flags any unsupported claim with a `[citation needed]` marker
- Returns the corrected synthesis

Output: `<workspace>/research/<session>/03-cite-checked.md`.

**Output location (production):** copy the cite-checked synthesis to `<workspace>/inbox/research-<slug>-<date>-<short-uuid>.md`.
**Output location (TEST_MODE):** copy to `<workspace>/qa/research-skill-test/standard-output.md`.

---

## `--deep` pipeline

Full 9-stage pipeline. Identical to the prior `deep-research-orchestrator` skill — preserved verbatim. Manifest-based, resumable, with contradiction detection and three-tier output.

### State directory

Every run gets its own session directory with a UUID suffix to prevent same-day collisions:

```
<workspace>/research/<YYYY-MM-DD>-<topic-slug>-<short-uuid>/
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
  "model_policy_path": "~/.claude/skills/research/MODEL_POLICY.md",
  "depth": "deep",
  "test_mode": false,
  "stages": [
    {"name": "00-question", "status": "passed", "started_at": "...", "completed_at": "...", "model": "opus-4-6", "notes": "..."},
    {"name": "01-breadth", "status": "passed", "agent_count": 6, "ledger_entries_added": 73, "...": "..."},
    {"name": "01-compliance", "status": "passed", "rejected_agents": 1, "rerun_agents": 1, "...": "..."}
  ],
  "final_status": "<in_progress|completed|aborted>",
  "abort_reason": null
}
```

Final deliverable lands in `<workspace>/inbox/deep-research-<topic>-<date>-<short-uuid>.md` (production) or `<workspace>/qa/research-skill-test/deep-output.md` (TEST_MODE). The UUID disambiguates same-day runs on the same topic.

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

Final deliverable: a single markdown at `<workspace>/inbox/deep-research-<topic>-<date>-<short-uuid>.md` (or `<workspace>/qa/research-skill-test/deep-output.md` in TEST_MODE) with three sections (sentence / brief / thesis). The evidence ledger and corpus-quality report stay in the session directory and are referenced by path, not concatenated.

## Cross-cutting (deep only): credibility & bias tagging

Every piece of evidence collected by ANY subagent in `--deep` MUST be tagged inline using `prompts/credibility-rubric.md`. The compliance gate enforces this — it is the primary mechanism, not a backup.

Tag fields (single source of truth — `prompts/credibility-rubric.md`):
- **Admiralty source** (A-F) × **Admiralty information** (1-6); grade `1` requires ≥2 independent `independence_cluster` values
- **Verdict**: true / likely / contested / false / unknown
- **Legal-status**: court-settled / contested / opinion / gossip
- **Bias**: `left` / `right` / `center` / `sponsored` / `neutral` / `unknown` (single enum, no synonyms)
- **Source type**: primary / secondary / tertiary / unknown

Ledger schema includes `claim_id`, `parent_claim_id`, `refutes_claim_id`, `excerpt`, `quote_location`, `publication_date`, `retrieved_at`, `language`, `independence_cluster`, `subquestion_id`, plus the tag fields above. See `prompts/credibility-rubric.md` for full schema.

`--shallow` and `--standard` do NOT enforce credibility tagging — that's intentional. If you need it, use `--deep`.

## Unified governance — failure thresholds and confidence ceilings (deep only)

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

When pipeline aborts: write failure report to `<workspace>/inbox/deep-research-FAILURE-<topic>-<date>-<short-uuid>.md`, tell the user, recommend remediation.

## Subagent prompt templates (deep)

When dispatching subagents for `--deep`, embed the relevant template after substituting placeholders:
- `prompts/breadth-agent.md` — Stage 1
- `prompts/depth-agent.md` — Stage 2
- `prompts/gap-fill-agent.md` — Stage 4
- `prompts/compliance-gate.md` — Stages 1.5 / 2.5 / 4.5 (orchestrator-direct, not a subagent)
- `prompts/contradiction.md` — Stages 3.5 / 5 (orchestrator-direct)
- `prompts/theory-draft.md` — Stage 6 (subagent briefs for 6a + orchestrator structure for 6b)
- `prompts/fact-check.md` — Stage 7 (orchestrator-direct)
- `prompts/credibility-rubric.md` — referenced by every subagent template (single source of truth)

`--standard` reuses `prompts/breadth-agent.md` lightly (no enforced tagging). `--shallow` does not use these prompts at all — the `research-expert` agent has its own internal brief.

## Failure modes & escalation

- **Subagent times out** — retry once with narrower scope; if still fails, log and proceed only if minimum-agent threshold still met.
- **Rate limits during breadth** — fall back to sequential dispatch (slower but completes). Update manifest.
- **Skill tool unavailable from inside this skill** — if `Skill` tool can't invoke `synthesizer`, `citation-validator`, `question-refiner`, fall back to inlining their logic via direct LLM call at the appropriate model level. Log this in manifest.
- **Filesystem write contention on JSONL ledger** — append mode with `flock` (Bash). If locking unavailable, dispatch agents sequentially within Stage 1 (slower).
- **Contradictions unresolvable after tiebreaker** — present both sides in theory with explicit "unresolved" flag; lower confidence per ceiling rules.
- **Fact-check abort** — see unified governance.
- **Topic out of scope** (asks for harmful info) — refuse at Stage 0.
- **`research-expert` agent fails (`--shallow` only)** — retry once; if still fails, escalate to `--standard` and tell the user why.

## Composition with existing skills

This skill orchestrates these existing skills (do not duplicate their logic):
- `question-refiner` — Stage 0 (deep), ST0 (standard, optional)
- `synthesizer` — Stage 3 (deep), ST2 (standard)
- `citation-validator` — Stage 7 (deep), ST3 (standard)
- `fact-checker` — credibility rubric (referenced inline by deep subagents)
- `got-controller` — optional, for very complex topics where Graph-of-Thoughts path optimization is warranted (Stage 1 + Stage 2 can run as GoT Generate/Aggregate)

This skill calls the `research-expert` agent (registered separately, not a skill) at every depth. Do not invoke the archived `deep-research-orchestrator` skill — this skill supersedes it.

## Success criteria

### `--shallow`

A run is complete when:
- [ ] `research-expert` agent returned a non-empty report
- [ ] Report path surfaced to the user

### `--standard`

A run is complete when:
- [ ] All sub-questions covered by at least one search report
- [ ] Synthesis integrates findings into a coherent narrative
- [ ] Cite-check passed (every factual claim has a source)
- [ ] Final deliverable in `<workspace>/inbox/`

### `--deep`

A run is complete when:
- [ ] All stages executed (or skipped with logged justification in run-manifest.json)
- [ ] Every claim in `06-theory.md` has a tagged corpus citation by `claim_id`
- [ ] All contradictions documented with resolution status and materiality label
- [ ] Three output tiers generated and consistent with each other
- [ ] Evidence ledger has ≥ 20 tagged entries
- [ ] Final deliverable in `<workspace>/inbox/`
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

### `--shallow`
1. **One-paragraph summary** of the agent's report
2. **Inbox path** (or `/tmp/research_*.md` path) for full report
3. **Caveat** that this is shallow — no contradiction handling, no fact-check

### `--standard`
1. **One-paragraph synthesis lead**
2. **3–5 key claims** with sources
3. **Inbox path** to full deliverable
4. **Caveats** flagged in cite-check (any unsupported claims, gaps not filled)

### `--deep`
1. **The one-sentence answer** (top of message)
2. **Confidence level** (high/medium/low + 1 reason, citing unified governance rule)
3. **Inbox path** to the full deliverable + session-directory path for ledger/corpus-quality
4. **Any unresolved contradictions** flagged briefly with materiality
5. **Any corpus-quality caveats** (e.g., "primary-source share was 22% — below 30% threshold; treat the technical-claim arguments as preliminary")
6. **What would change the answer** (falsifiability hook)

Do NOT paste the full thesis inline unless explicitly asked.

If `TEST_MODE=1`, prefix the entire reply with: `[TEST MODE — pinned to claude-haiku-4-5; output is for scaffolding validation only, not real research]`.
