---
name: log
description: Append a structured entry to the agent log with automatic rotation
user_invocable: false
args: "run_id=<id> skill=<name> status=<SUCCESS|FAILED> detail=<message>"
---

# Agent Log

Append a structured log entry to `.claude/memory/agent-log.md`. This skill owns the log format, creation, and rotation. All other skills and agents call this instead of writing to the log directly.

## Steps

1. **Parse input**: Extract the fields from the arguments:
   - `run_id` — Identifier linking related entries (e.g., `cos-2026-04-11-1`). Use `manual` if invoked by a user or no run ID was provided.
   - `skill` — Name of the skill or agent that produced this entry
   - `status` — `SUCCESS`, `WARNING`, or `FAILED`
   - `detail` — Brief description (item counts on success, error reason on failure)

2. **Check if log file exists**: Read `.claude/memory/agent-log.md`.
   - If it doesn't exist, create it with this header:

   ```markdown
   # Agent Log

   | Timestamp | Run ID | Skill | Status | Detail |
   |-----------|--------|-------|--------|--------|
   ```

3. **Append the entry**: Add a new row with the current timestamp in ISO 8601 format (e.g., `2026-04-11T17:30Z`).

4. **Rotate**: Count the data rows (excluding the header and separator lines). If there are more than 200, remove the oldest rows to keep exactly 200. Historical entries are preserved in git history.

5. **No output**: This skill is silent — it does not print anything to the user. It is a utility called by other skills.
