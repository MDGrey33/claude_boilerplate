---
name: one-on-one-prep
description: Prepare 1:1 meeting notes by synthesizing a team member's recent activity into a structured meeting agenda
user_invocable: true
args: "Member name and optional time range. Examples: 'Alice Chen', 'Alice Chen last 2 weeks', 'Bob Smith 2026-03-28 to 2026-04-11'. Defaults to last 1 week."
---

# 1:1 Meeting Prep

Synthesize a team member's recent activity from daily activity files into a structured meeting prep document. This is a **synthesis skill** — it reads raw data collected by `/collect-team-activity`, it does not collect data itself.

## Steps

1. **Role guard**: Read `~/.claude/me/identity.md` and check the user's title/role.
   - If the role is clearly IC-equivalent with no reports, **stop**:
     ```
     This skill is for leadership roles with direct reports.
     ```
   - If ambiguous, proceed.

2. **Load team roster**: Read `~/.claude/me/team.md`.
   - If missing, **stop** with guidance:
     ```
     No team roster found at ~/.claude/me/team.md
     Create one with your direct reports and their platform IDs.
     ```
   - Match the member name loosely (first name, full name, case-insensitive). If no match, list available names and ask.

3. **Load writing style**: Read the Writing Style section from `~/.claude/me/identity.md`. Apply it to all output. If no style is defined, default to clear and concise.

4. **Determine time range**: Parse the arguments for a date range.
   - If specified, use it (e.g., "last 2 weeks", "2026-03-28 to 2026-04-11")
   - If not specified, default to last 1 week from today
   - Convert to a list of workday dates

5. **Read activity files**: For each date in the range, look for:
   - `.claude/memory/activity/YYYY-MM-DD-team-activity.md` — check for the member's section

   **If activity files are missing for some dates**, note which dates have no data in the output. Do not attempt to collect — that's `/collect-team-activity`'s job. If no activity files exist at all, **stop**:
   ```
   No activity data found for {member} in the requested period.
   Run /collect-team-activity {member} for the missing dates first.
   ```

6. **Synthesize**: Analyze all collected activity across the date range and produce four sections:

   **Completed Tasks & Achievements**
   - Group by project or theme, not by date or activity category
   - Each item: what was accomplished, why it matters, with date and source links
   - Highlight standout contributions

   **In Progress / Open Items**
   - Group by project or theme
   - Each item: current state, what's next, any blockers
   - Flag items that have been in progress across multiple days without visible movement

   **Areas for Improvement / Discussion Points**
   - Identify patterns: stalled tickets, communication gaps, recurring blockers
   - Frame constructively — these are conversation starters, not accusations
   - Only include observations backed by data. Don't invent concerns.

   **Key Talking Points**
   - 3-5 high-level items to guide the meeting
   - Prioritize: blockers first, recognition second, growth third
   - Include anything that warrants a direct conversation rather than async follow-up

7. **Formatting rules**:
   - Add the specific date to each point when available from the source data
   - Jira tickets: always include the full ticket title + number, linked (e.g., `[PROJ-123 - Implement login screen](url)`)
   - Every claim must have a source link. No exceptions.
   - Keep each bullet to 1-2 sentences max
   - Writing tone follows `identity.md` — if not set, default to direct and clear

8. **Write the output file**: Write to `.claude/memory/reports/1-1/{member-slug}/YYYY-MM-DD_to_YYYY-MM-DD-prep.md` where `member-slug` is the member's name in lowercase with hyphens (e.g., `alice-chen`) and the dates are the start and end of the activity period.

   ```markdown
   # 1:1 Prep: {Member Name}
   **Date**: YYYY-MM-DD
   **Period**: YYYY-MM-DD to YYYY-MM-DD
   **Activity data**: {X}/{Y} workdays covered ({list missing dates, if any})

   ## Completed Tasks & Achievements

   ### {Project / Theme}
   - **{What was accomplished}** ({date})
     - Sources: [PROJ-123 - Ticket title](url), [Slack thread](permalink)
     - {Why it matters}

   ## In Progress / Open Items

   ### {Project / Theme}
   - **{Current state}** ({date})
     - Sources: [PROJ-456 - Ticket title](url)
     - Next: {what's expected}

   ## Areas for Improvement / Discussion Points

   - **{Observation}**
     - Evidence: {source links}
     - Suggested framing: {how to bring this up}

   ## Key Talking Points

   1. {Most important item}
   2. {Second}
   3. {Third}
   ```

9. **Report to user** (skip if invoked by another agent):
   ```
   1:1 prep ready: {Member Name}
   ──────────────────────────────
   Period: YYYY-MM-DD to YYYY-MM-DD
   Coverage: {X}/{Y} workdays with activity data
   Missing: {dates without data, or "none"}
   File: .claude/memory/reports/1-1/{member-slug}/YYYY-MM-DD_to_YYYY-MM-DD-prep.md
   ```

10. **Logging**: On completion, invoke the `/log` skill:
    ```
    /log run_id=<run_id> skill=one-on-one-prep status=<SUCCESS|FAILED> detail={member name}: {period}, {coverage}
    ```
    Use `manual` as run_id if invoked directly by the user.

## Important Rules

- **Synthesis only.** This skill reads from `activity/` files. It never queries Slack, Jira, or any other data source directly.
- **Every claim needs a source link.** Inherited from the activity files. If an activity item has no link, flag it as unverified.
- **Don't fabricate concerns.** The "Areas for Improvement" section must be grounded in observable data patterns. No activity for a day is not a concern — it might mean the daily collection wasn't run.
- **Don't over-prepare.** A good 1:1 prep is a starting point for conversation, not a performance review. Keep it focused on what's worth discussing in person.
- **Missing data is a note, not a failure.** If some days have no activity files, say so and move on. The prep is still useful with partial data.
