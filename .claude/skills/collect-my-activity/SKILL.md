---
name: collect-my-activity
description: Collect the user's daily work activity from Slack, Jira, Confluence, GitHub, and Google Drive with source links
user_invocable: true
args: "Optional date or date range (e.g., '2026-04-11', '2026-04-07 to 2026-04-11'). Defaults to today."
---

# Collect My Activity

Collect the user's work activity for a given day (or date range) from all available data sources (Slack, Jira, Confluence, GitHub, Google Drive). Every item must include a source link. Output is written to `.claude/memory/activity/`.

## Steps

1. **Pre-flight checks**: Verify the environment before collecting:
   - **Slack MCP**: Check Slack tools are available. If missing, fail.
   - **Atlassian MCP**: Check Atlassian tools are available. If missing, fail.
   - **`gh` CLI**: Check if `gh` is available (`which gh`). Expected but not blocking. If missing, log a warning via `/log` (`status=WARNING detail=gh CLI not available — GitHub data will be missing. Install with: brew install gh && gh auth login`), mark as a gap, and continue.

   If Slack or Atlassian MCP is missing, **stop and write a failure status**:

   ```markdown
   # My Activity: YYYY-MM-DD

   ## Status: FAILED
   **Reason**: [which MCP servers were unavailable]
   ```

   Also invoke `/log` to record the failure (see Logging section below).

2. **Resolve identity from MCP**: Use the available MCP tools to resolve the user's platform IDs:
   - Call `slack_read_user_profile` to get the user's Slack ID
   - Call `atlassianUserInfo` to get the user's Atlassian account ID and Jira cloud ID
   - Fall back to `~/.claude/me/identity.md` only if MCP calls fail
   - If neither MCP nor identity file provides the IDs, ask the user directly

3. **Determine date range**: Use the argument if provided, otherwise default to today. Convert to the format needed by each platform's query syntax.

   **Multi-day ranges**: Collect one day at a time. One day's MCP responses fit in a single context window; multiple days may not.

4. **Collect from sources in parallel**:

   **Slack:**
   - Search for messages from the user in the date range using their Slack user ID
   - Use `detailed` response format (never `concise` — it drops timestamps and permalinks). Set `include_context: false` to keep response size manageable; use `slack_read_thread` selectively for context.
   - Capture: channel, timestamp, message summary, permalink
   - Check threads where the user participated — decisions, guidance, approvals
   - Fold low-signal items (reactions, acks) into the related activity they refer to
   - Paginate using the `cursor` parameter when results hit the page limit
   - DMs are not accessible via MCP — ask the user about notable DMs at the end

   **Jira:**
   - Search for issues updated by the user in the date range using JQL. **Date boundary**: use `>= "YYYY-MM-DD" AND < "next_day"` (not `<=` — Jira treats `<= "04-10"` as "before start of 04-10").
   - Request minimal fields: `summary, status, issuetype, priority, updated`
   - Also search for issues created by the user, and separately for issues where the user added comments (comments don't appear in assignee/reporter results)
   - Capture: key, summary, status, what changed, issue URL

   **GitHub:**
   - If `gh` CLI is available, use it to search for PRs authored, PRs reviewed, issues created/commented in the date range
   - For each: capture the repo, number, title, and URL
   - If `gh` is not available, note this gap in the output

   **Confluence:**
   - Uses the same Atlassian MCP as Jira — no separate pre-flight check needed
   - Search for pages created or updated by the user in the date range using `searchConfluenceUsingCql` with CQL: `contributor = "{accountId}" AND lastmodified >= "YYYY-MM-DD" AND lastmodified < "next_day"` (same date boundary logic as Jira)
   - For each page: capture the space, title, type of contribution (created vs. updated), and the page URL
   - Also search for comments the user added on Confluence pages in the date range

   **Google Drive:**
   - If Google Drive MCP tools are available, search for documents created or edited by the user in the date range
   - For each document: capture the title, type (doc, sheet, slide), what changed (created vs. edited), and the URL
   - If not available, note this gap in the output

   **Oversized responses (50KB+):** Write a targeted extraction script on the fly based on the actual response structure. Don't use pre-baked scripts — MCP schemas change.

5. **Deduplicate and cross-reference**: A single activity may appear in multiple sources (e.g., a Jira ticket discussed in Slack and linked in a PR). Group related items into a single entry with multiple source links rather than listing them separately.

6. **Categorize each item** into one or more of (categories are role-neutral — an IC, PM, EM, or director will naturally use different subsets):
   - `engineering` — Writing code, debugging, code reviews, technical problem-solving
   - `architecture` — Design decisions, technical direction, system design, RFCs, design docs
   - `team` — Mentoring, feedback, hiring, 1:1s, process improvements, onboarding
   - `infrastructure` — Infra, cost optimization, security, DevOps, incident response
   - `delivery` — Sprint work, project tracking, unblocking dependencies, release management
   - `product` — Requirements, user research, feature specs, stakeholder alignment, roadmap
   - `operational` — Process improvements, monitoring, on-call, documentation, cross-team coordination
   - `strategic` — Executive comms, OKRs, cross-org initiatives, vendor relationships, budget
   - `ai-engineering` — AI tool adoption, AI-powered workflows, AI strategy
   - `growth` — Learning, conferences, training, certifications, knowledge sharing

7. **Write the output file**: Write to `.claude/memory/activity/YYYY-MM-DD-my-activity.md`:

   ```markdown
   # My Activity: YYYY-MM-DD

   ## Status: SUCCESS
   **Sources checked**: Slack, Jira, Confluence, GitHub (gh CLI / N/A), Google Drive (MCP / N/A)

   ## Summary
   [1-2 sentences: what was the focus today]

   ## Activity

   ### [category]
   - **[brief description framed by impact, not just action]**
     - Sources: [Slack permalink], [JIRA-123](url), [PR #45](url)
     - Context: [why this matters — what decision was made, what was unblocked, what risk was mitigated]

   ### [category]
   - ...

   ## Gaps
   - [sources that weren't accessible — e.g., "GitHub: gh CLI not available", "Google Drive: MCP not available", "DMs: not accessible via MCP"]
   ```

8. **Report to user**:

   ```
   Activity collected: YYYY-MM-DD
   ───────────────────────────────
   Items found: [count]
   Sources: Slack ([count]), Jira ([count]), Confluence ([count]), GitHub ([count or N/A]), Drive ([count or N/A])
   Gaps: [list any inaccessible sources]
   File: .claude/memory/activity/YYYY-MM-DD-my-activity.md

   Anything missing? Notable DMs, meetings, or whiteboard sessions to add?
   ```

## Important Rules

- **Every item must have at least one source link.** No exceptions. If you can't link to it, flag it as unverified.
- **Frame by impact, not action.** Not "commented on PLAT-301" but "Provided architectural direction on audit log strategy for Node.js upgrade (PLAT-301)".
- **Don't fabricate activity.** If a day is quiet, say so — that's useful signal.
- **Ask about gaps.** Always ask about DMs, meetings, and offline conversations at the end — these are invisible to MCP tools but often the most impactful work.
- **Respect date boundaries.** Only include activity that occurred within the requested date range. Don't pull in stale tickets just because they exist.
- **Always write the output file** — even on failure. The Status field (SUCCESS/FAILED) lets calling agents check the result programmatically.

## Logging

On completion (success or failure), invoke the `/log` skill:

```
/log run_id=<run_id> skill=collect-my-activity status=<SUCCESS|FAILED> detail=<summary>
```

The `run_id` is passed by the calling agent (e.g., Chief of Staff). Use `manual` if invoked directly by the user.
