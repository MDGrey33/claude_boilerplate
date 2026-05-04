# Compliance Gate — runs after every subagent batch

This is an orchestrator-direct stage that runs after Stages 1, 2, and 4. Model: L1 (Haiku 4.5) per `MODEL_POLICY.md` — the work is mechanical schema validation, no reasoning.

The gate REJECTS subagent output that doesn't meet the contract. Rejected agents are re-dispatched once with a tightened prompt; if they fail twice, their findings are dropped and logged.

---

## Inputs
- Directory of subagent reports just produced (e.g., `<workspace>/research/<session>/01-breadth/`)
- Lines appended to `corpus/evidence-ledger.jsonl` since last gate
- Manifest of dispatched agent IDs

## Validation checks (all must pass)

### Per-report (markdown)
1. **File exists** at expected path with non-zero length
2. **Returned summary** in agent's reply (≥ 1 sentence)
3. **No untagged claims** — every bullet/quote with a factual assertion has an inline `[admiralty, verdict, legal_status, bias]` tag

### Per-ledger-line (JSONL)
4. **Valid JSON** (parses cleanly)
5. **Required fields present:** `claim_id`, `parent_claim_id` (nullable), `refutes_claim_id` (nullable), `claim`, `source_url`, `source_title`, `source_type`, `primary_secondary`, `publication_date` (nullable but warn), `retrieved_at`, `excerpt`, `quote_location` (nullable), `language`, `admiralty`, `verdict`, `legal_status`, `bias`, `independence_cluster` (nullable), `agent_id`, `stage`, `subquestion_id` (nullable), `timestamp`
6. **Enum compliance:**
   - `admiralty` matches `^[A-F]/[1-6]$`
   - `verdict` ∈ `{true, likely, contested, false, unknown}`
   - `legal_status` ∈ `{court-settled, contested, opinion, gossip}`
   - `bias` ∈ `{left, right, center, sponsored, neutral, unknown}` — see normalization rule in rubric
   - `source_type` ∈ `{primary, secondary, tertiary, unknown}`
   - `primary_secondary` ∈ `{primary, secondary}` (derived from source_type)
7. **claim_id uniqueness** within the ledger
8. **agent_id matches** the dispatched agent
9. **stage matches** the current stage number
10. **No duplicate claims** (same `claim` text + same `source_url` + same `agent_id` = duplicate, reject extras)

### Cross-report sanity
11. **Coverage:** at least one ledger entry per dispatched agent (an agent that produced no entries is suspicious)
12. **Tag-density floor:** ≥ 5 tagged claims per breadth agent, ≥ 3 per depth agent, ≥ 1 per gap-fill agent
13. **D-F flag:** ledger entries with admiralty grade D, E, or F automatically populate `gap-candidates.jsonl` (these become Stage 4 inputs)

## Output

Write `<workspace>/research/<session>/<stage>-compliance.md` with:
- Per-agent pass/fail
- Specific violations (file path + line if JSONL)
- Re-dispatch decisions
- Final accepted-agent count

Update `run-manifest.json` with stage status.

## Decision rules

- **All pass** → proceed to next stage
- **Some fail, recoverable** → re-dispatch failed agents once with tightened prompt highlighting the violations. Wait for retry, re-validate.
- **Re-dispatch fails again** → drop the agent's contribution, log it, proceed if remaining agents meet the minimum (≥ 3 breadth agents accepted, ≥ 2 depth agents, ≥ 1 gap-fill per gap)
- **Below minimum after retries** → ABORT pipeline, write failure report to `<workspace>/inbox/`
