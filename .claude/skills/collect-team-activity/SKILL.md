---
name: collect-team-activity
description: Collect a team member's daily work activity from public Slack, Jira, Confluence, GitHub, and Google Drive
user_invocable: true
args: "Optional member name and/or date or date range. Examples: 'Alice Chen', '2026-04-10', 'Alice Chen 2026-04-10', '2026-04-07 to 2026-04-11', 'Alice Chen 2026-04-07 to 2026-04-11'. No args = all members today."
---

# Collect Team Activity

Collect work activity for one or all team members for a given day from public data sources. Designed for engineering leadership (EM, director, VP). Each invocation collects for **one member** and appends to a consolidated daily file, keeping context usage bounded.

## Steps

1. **Role guard**: Read `~/.claude/me/identity.md` and check the user's title/role.
   - If the role is clearly IC-equivalent (e.g., "Software Engineer", "Developer") with no reports, **stop**:
     ```
     This skill is for leadership roles with direct reports.
     Use /collect-my-activity for your own activity.
     ```
   - Leadership roles: Director, VP, Head of, Engineering Manager, Team Lead, Tech Lead, Principal (with reports), Staff (with reports).
   - If ambiguous, proceed — don't block on edge cases.

2. **Load team roster**: Read `~/.claude/me/team.md`.
   - If missing, **stop** with guidance:
     ```
     No team roster found at ~/.claude/me/team.md
     Create one with your direct reports and their platform IDs.
     See the template at the bottom of this skill for the expected format.
     ```
   - Parse each team member's name, role, and platform IDs (Slack, Jira, GitHub).

3. **Determine scope**: Parse the arguments to decide who to collect for and which date(s).
   - **Specific member + date**: `/collect-team-activity Alice Chen 2026-04-10`
   - **Specific member + date range**: `/collect-team-activity Alice Chen 2026-04-07 to 2026-04-11`
   - **Specific member, today**: `/collect-team-activity Alice Chen`
   - **All members + date**: `/collect-team-activity 2026-04-10`
   - **All members + date range**: `/collect-team-activity 2026-04-07 to 2026-04-11`
   - **All members, today**: `/collect-team-activity`

   Match the member name loosely against the team roster (first name, full name, or case-insensitive). If no match, list available names and ask.

   **Multi-day ranges**: Collect one day at a time. One day's MCP responses fit in a single context window; multiple days may not.

4. **Pre-flight checks** (same as collect-my-activity):
   - **Slack MCP**: Required. If missing, fail.
   - **Atlassian MCP**: Required (covers Jira + Confluence). If missing, fail.
   - **`gh` CLI**: Expected. If missing, log a warning via `/log` (`status=WARNING detail=gh CLI not available — GitHub data will be missing. Install with: brew install gh && gh auth login`), mark as a gap, and continue. Do not stop execution.
   - **Google Drive MCP**: Optional. If missing, note in gaps.

   On failure (required tools missing), write a failure status file and invoke `/log` (see steps 9 and 10).

5. **If collecting for all members**: Collect one member at a time to avoid concurrent file writes.

6. **Collect from sources in parallel** (single-member mode):

   **Slack (public channels only):**
   - Search `slack_search_public` for messages from the member using their Slack user ID
   - Use `detailed` response format (never `concise` — it drops timestamps and permalinks). Set `include_context: false` to keep response size manageable; use `slack_read_thread` selectively for context.
   - Capture: channel, timestamp, message summary, permalink
   - Note threads with decisions, guidance, approvals
   - Fold low-signal items (reactions, acks) into the related activity they refer to
   - Paginate using the `cursor` parameter when results hit the page limit

   **Jira:**
   - Search for issues updated by the member in the date range using JQL. **Date boundary**: use `>= "YYYY-MM-DD" AND < "next_day"` (not `<=` — Jira treats `<= "04-10"` as "before start of 04-10").
   - Request minimal fields: `summary, status, issuetype, priority, updated`
   - Also search for issues where the member added comments (comments don't appear in assignee/reporter results)
   - Capture: key, summary, status, what changed, issue URL

   **Confluence:**
   - Search for pages created or updated by the member using `searchConfluenceUsingCql`:
     `contributor = "{accountId}" AND lastmodified >= "YYYY-MM-DD" AND lastmodified < "next_day"` (same date boundary logic as Jira)
   - For each page: capture the space, title, type of contribution (created vs. updated), and the page URL
   - Also search for comments the member added

   **GitHub:**
   - If `gh` CLI is available, search for PRs authored, PRs reviewed, and issues created/commented by the member's GitHub username in the date range
   - For each: capture the repo, number, title, and URL
   - If `gh` is not available, note this gap

   **Google Drive:**
   - If Google Drive MCP tools are available, search for documents created or edited by the member in the date range
   - For each document: capture the title, type, what changed (created vs. edited), and the URL
   - If not available, note this gap

   **Oversized responses (50KB+):** Write a targeted extraction script on the fly based on the actual response structure. Don't use pre-baked scripts — MCP schemas change.

7. **Categorize each item** using the same role-neutral categories defined in collect-my-activity step 6.

8. **Write to the consolidated daily file**: Write to `.claude/memory/activity/YYYY-MM-DD-team-activity.md`.

   **If the file doesn't exist yet**, create it:

   ```markdown
   # Team Activity: YYYY-MM-DD

   ## Status: IN_PROGRESS (1/{total} members collected)
   **Sources checked**: Slack, Jira, Confluence, GitHub (gh CLI / N/A), Google Drive (MCP / N/A)

   ---

   ## {Member Name} -- {Role}

   ### {category}
   - **{brief description framed by impact}**
     - Sources: [Slack permalink], [JIRA-123](url), [Page title](confluence-url)
     - Context: {why this matters}

   ### {category}
   - ...

   ## Gaps
   - {sources that weren't accessible}
   ```

   **If the file already exists**, read it and:
   - Append the new member's section before the `## Gaps` section
   - Update the status line: increment the collected count
   - Merge any new gaps with the existing gaps section
   - If this is the last member, change status to `SUCCESS`

   **If the member already has a section in the file**, replace it (re-collection).

9. **Report to user**:

   For single-member collection:
   ```
   Team activity collected: {Member Name} (YYYY-MM-DD)
   ─────────────────────────────────────────────────────
   Items found: {count}
   Sources: Slack ({count}), Jira ({count}), Confluence ({count}), GitHub ({count or N/A}), Drive ({count or N/A})
   Progress: {n}/{total} members collected
   File: .claude/memory/activity/YYYY-MM-DD-team-activity.md
   ```

   For all-members collection:
   ```
   Team activity collected: YYYY-MM-DD
   ─────────────────────────────────────
   Members: {count}/{total} succeeded
   Total items: {count}
   Failed: {list of members that failed, or "none"}
   File: .claude/memory/activity/YYYY-MM-DD-team-activity.md
   ```

10. **Logging**: On completion (success or failure), invoke the `/log` skill:
    ```
    /log run_id={run_id} skill=collect-team-activity status={SUCCESS|FAILED} detail={member name}: {summary}
    ```
    Use `manual` as run_id if invoked directly by the user.

## Important Rules

- **Every item must have at least one source link.** No exceptions. If you can't link to it, flag it as unverified.
- **Frame by impact, not action.** Not "merged PR #45" but "Shipped connection pooling fix that unblocked staging deployment (PR #45)".
- **Don't fabricate activity.** Only report what you find in the data sources. If someone had a quiet day, say so — that's useful signal too.
- **Public sources only.** No DMs, no private channels. This is intentional and aligns with the team's public-by-default communication culture.
- **Respect date boundaries.** Only include activity within the requested date range.
- **Always write the output file** — even on failure. The Status field lets calling agents check the result programmatically.
- **Don't duplicate with collect-my-activity.** This skill collects *other people's* activity. For the user's own activity, use `/collect-my-activity`.

## team.md Expected Format

The skill expects `~/.claude/me/team.md` to follow this structure:

```markdown
# My Team

## Direct Reports

### Alice Chen
- **Role**: Backend Engineer
- **Slack**: U01ABC123
- **Jira**: 712020:abcdef-1234-5678-abcd-1234567890ab
- **GitHub**: alicechen

### Bob Smith
- **Role**: Frontend Engineer
- **Slack**: U02DEF456
- **Jira**: 712020:fedcba-4321-8765-dcba-0987654321ba
- **GitHub**: bobsmith
```

Platform IDs can be resolved by:
- **Slack**: `slack_search_users` by name, or check a user's profile in the Slack UI
- **Jira**: `lookupJiraAccountId` by email, or check in Jira admin
- **GitHub**: the member's GitHub username
