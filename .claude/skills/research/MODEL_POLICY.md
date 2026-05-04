# Research Skill — Model Policy

**Quality-first, not cost-first.** This skill produces high-stakes research outputs (theses with falsifiability claims, fact-checked corpus). Cost optimization is explicitly de-prioritized vs. the shared `_shared/MODEL_SELECTION.md` policy. Use the strongest reasoning model that fits each task's needs.

**This file is user-editable.** Edit the table below as new models ship or as you change your mind about which reasoning level a stage needs. The orchestrator and subagent dispatchers read this file at runtime.

---

## Reasoning levels

We classify model strength into 4 reasoning levels. The mapping below is to currently-available Claude models as of 2026-04. **Update the model column when newer models ship** — the levels themselves are stable, the mapping shifts.

| Level | Description | Current model |
|---|---|---|
| **L4 — Frontier** | The strongest reasoning model available. Multi-step logical chains, novel synthesis, contradiction resolution under ambiguity, theory drafting with rationalization | **claude-opus-4-7** (1M context) |
| **L3 — Premium** | Strong reasoning, second-tier frontier. High-stakes synthesis, structured argument construction, adversarial fact-checking | **claude-opus-4-6** |
| **L2 — Balanced** | Default reasoning quality. Most coordinated tasks, breadth retrieval with judgment, structured extraction with light reasoning | **claude-sonnet-4-6** |
| **L1 — Light** | Bounded structured tasks: schema validation, regex extraction, label classification. Use ONLY for compliance gates and validators where the task is mechanical | **claude-haiku-4-5** |

**Hard rule:** never use L1 for any stage that produces evidence, synthesis, theory, or fact-check output. L1 is allowed only for the compliance/validation gates between stages.

---

## Per-stage model assignments (production)

Edit this table to change model selection per stage. The orchestrator reads this at runtime.

### `--shallow` depth

| Stage | Task | Reasoning level | Notes |
|---|---|---|---|
| S0 | Decompose query into 1–3 search angles | L2 | Light planning before delegating |
| S1 | Invoke `research-expert` agent | L2 | Single-pass parallel web search; the agent picks its own model from the agent registry |
| S2 | Return agent report verbatim | — | No additional model call |

### `--standard` depth

| Stage | Task | Reasoning level | Notes |
|---|---|---|---|
| ST0 | Decompose into 3–5 sub-questions | L3 | Scope errors here cascade |
| ST1 | Parallel `research-expert` subagents (×3–5) | L2 | Wide coverage with judgment |
| ST2 | Synthesize findings | L3 | Multi-source integration |
| ST3 | Cite-check pass | L2 | Verify every claim has a source |

### `--deep` depth (full 9-stage pipeline)

| Stage | Task | Reasoning level | Notes |
|---|---|---|---|
| 0 | Question refinement | L3 | Frames the entire run; getting scope wrong poisons all downstream stages |
| 1 | Breadth subagents (×5–8) | L2 | Wide coverage, judgment on what's relevant; L3 if topic is highly technical |
| 1.5 | **Compliance gate after Stage 1** | L1 | Schema/enum validation only — mechanical |
| 2 | Depth subagents (×3–5) | L3 | Deep reading, citation chain following, refutation reasoning — quality matters |
| 2.5 | **Compliance gate after Stage 2** | L1 | Mechanical |
| 3 | Synthesis + gap inventory | L3 | Multi-source integration, gap reasoning |
| 3.5 | **Lightweight contradiction triage** | L2 | Surface obvious conflicts to feed Stage 4 — judgment but bounded |
| 4 | Gap-fill subagents (×N) | L2 | Narrow single-question tasks; L3 if gap is high-stakes |
| 4.5 | **Compliance gate after Stage 4** | L1 | Mechanical |
| 5 | Full contradiction & inconsistency detection | **L4** | Cross-corpus reasoning, resolution under ambiguity. Frontier model required |
| 6a | Competing theory candidate generation (×2) | L3 | Two adversarial drafts |
| 6b | Theory selection / merge (orchestrator) | **L4** | Final editorial — frontier reasoning |
| 7 | Fact-check pass | **L4** | Adversarial audit of every claim — frontier reasoning required |
| 8 | Three-tier output compression | L2 | Compression is mostly mechanical once theory is locked |

---

## TEST_MODE

When the environment variable `TEST_MODE=1` is set at skill invocation, **every stage is pinned to `claude-haiku-4-5-20251001`** regardless of the per-stage tables above. Purpose: cost-controlled smoke-testing of the orchestration scaffolding and prompt plumbing without burning frontier-model budget.

**TEST_MODE pin (single model for all stages, all depths):**

| Stage / Depth | Model |
|---|---|
| All stages, all depths | `claude-haiku-4-5-20251001` |

**Caveats — what TEST_MODE does NOT validate:**
- L4 contradiction-resolution quality (Stage 5)
- L4 theory-merge editorial judgment (Stage 6b)
- L4 adversarial fact-checking (Stage 7)
- Synthesis quality on L3 stages
- Real-world deliverable quality

TEST_MODE is for: did the pipeline run end-to-end? Did prompts substitute correctly? Did stages write the expected files? Did the manifest update? Did the agent dispatch fire?

**Activation:** the orchestrator reads `os.environ.get('TEST_MODE')`. When `1`, it overrides the per-stage tables. When unset or `0`, the production tables apply.

**Hard rule for TEST_MODE:** never ship a TEST_MODE-generated deliverable as if it were a real research output. The output directory should be `<workspace>/qa/research-skill-test/` not `<workspace>/inbox/`.

---

## Override mechanism (production runs)

Any user invocation of the skill can override per-stage models. Two formats:

**Inline arg style** (model IDs use the full `claude-...` form, matching the table above):

```
/research <topic> --deep --model-stage5=claude-opus-4-7 --model-stage6=claude-opus-4-7
```

**File style.** Drop a `MODEL_OVERRIDE.md` at `<workspace>/research/<session>/MODEL_OVERRIDE.md` before the orchestrator dispatches. The file is a markdown table mirroring the per-stage assignments above; only the rows you list are overridden. Format:

```markdown
| Stage | Model |
|---|---|
| 5 | claude-opus-4-7 |
| 6b | claude-opus-4-7 |
```

Use the same model-ID format as the table. Stage IDs match the per-stage assignments table (e.g., `1`, `2.5`, `6a`, `6b`). Unlisted stages keep the default level→model mapping.

`TEST_MODE=1` overrides both inline args and `MODEL_OVERRIDE.md` files — when test mode is on, nothing else matters.

---

## Quality-over-cost rationale

Per skill mandate, cost is not the primary constraint for this skill. The reasoning:

1. Bad research is worse than no research — a fact-checked-but-wrong thesis erodes future trust
2. Stage 5 (contradiction detection) and Stage 7 (fact-check) are adversarial — model weakness here is invisible until something blows up downstream
3. Stage 6 (theory drafting) is the highest leverage point in the entire pipeline — every dollar spent here pays back in deliverable quality
4. Subagent stages (1, 2, 4) parallelize, so per-stage premium cost is amortized across N concurrent agents
5. The compliance gates (1.5, 2.5, 4.5) keep L1 for mechanical work, which is where cost savings belong

If a future model offers L4 reasoning at L2 cost, update the mapping above and the policy continues to hold.

---

## When the rules change

Update this file when:
- A new Claude model ships (map to the appropriate level)
- A new non-Claude model becomes available via the runtime
- The operator decides a stage needs more or less reasoning than currently assigned
- A specific failure mode in production reveals a stage was under-modeled

Don't update for:
- Cost spikes — re-read the rationale above
- One-off bad runs — those should be debugged, not papered over with model upgrades
