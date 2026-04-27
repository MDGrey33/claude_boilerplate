# Deep Research Orchestrator — Model Policy

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

## Per-stage model assignments

Edit this table to change model selection per stage. The orchestrator reads this at runtime.

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

## Override mechanism

Any user invocation of the skill can override per-stage model with:

```
/deep-research <topic> --model-stage5=opus-4-7 --model-stage6=opus-4-7
```

Or by adding a `MODEL_OVERRIDE.md` file at `~/workspace/research/<session>/MODEL_OVERRIDE.md` before dispatch.

---

## Quality-over-cost rationale

Per the user's mandate, cost is not the primary constraint for this skill. The reasoning:

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
- The user decides a stage needs more or less reasoning than currently assigned
- A specific failure mode in production reveals a stage was under-modeled

Don't update for:
- Cost spikes — re-read the rationale above
- One-off bad runs — those should be debugged, not papered over with model upgrades
