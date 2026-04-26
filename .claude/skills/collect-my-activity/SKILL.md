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

2. **Resolve identity — MCP first, identity.md as cache, user input as last fallback**:

   General principle: always probe the connected MCPs for any platform-derived value before reading `identity.md`, and only ask the user when both fail. `identity.md` is a cache, not a gate.

   - **Slack user ID** → `slack_read_user_profile`
   - **Atlassian account ID** → `atlassianUserInfo`
   - **Jira cloud ID** → `getAccessibleAtlassianResources` (returns the cloudId for accessible Atlassian sites)
   - **Google Workspace email** — resolve from the most reliable source available:
     1. `atlassianUserInfo.email` (primary — works for any engineering shop with Jira/Confluence access).
     2. `slack_read_user_profile.profile.email` (fallback if Atlassian is unavailable).
     3. `mcp__claude_ai_Google_Drive__list_recent_files` → `owners[0].emailAddress` (last automated fallback; only works if the user owns at least one file).
     4. Ask the user.
   - **GitHub username** — `gh` supports multiple authenticated accounts. The skill enforces determinism by switching the active session to the cached handle before queries and restoring it afterwards. Resolve as follows:
     - If cached in `## Profile`, use it. Verify it's still authenticated via `gh auth status` (parse for `Logged in to github.com account <handle>`). If the cached handle isn't in `gh auth status`, **fail loud** (FAILED) with re-auth instructions: `gh auth login --hostname github.com`.
     - If not cached, parse `gh auth status` for `Logged in to github.com account <handle>` lines:
       - **One account** → resolve via `gh api user --jq .login`, write back to `## Profile`.
       - **Multiple accounts** → **fail loud** (FAILED): *"Multiple `gh` accounts detected. Set `GitHub username` manually in `~/.claude/me/identity.md` `## Profile` before re-running. Agents cannot disambiguate which is the business account."*
     - **Active-session flip-flop**: env-var token-passing (`GH_TOKEN=$(gh auth token --user X) gh ...`) does not work reliably in the Claude Code sandbox — `$(...)` substitution gets blocked at a layer below the allowlist. Instead, the skill uses `gh auth switch --user <handle>` to flip the active session before queries, runs plain `gh` commands, and switches back at the end. See step 4 GitHub section for the exact pattern.

   **Write-back rule**: when MCP resolves a field that is missing from `identity.md`'s `## Profile` section, append it there. **Fill missing only — never overwrite an existing value.** A stale MCP handle could otherwise clobber the user's curated identity. If a resolved value differs from what's already there, log a `WARNING`, skip the write, and surface the discrepancy at the end of the run.

   If `identity.md` doesn't yet have a `## Profile` section, create it using the template at the end of this skill and append after any existing top-of-file content. Never modify other sections (Preferences, Writing Style, Growth areas, etc.) — they are user-curated.

3. **Determine date range and timezone**: Use the argument if provided, otherwise default to today.

   **Timezone model:**
   - Interpret the requested date(s) in the user's **local timezone**, read from `identity.md`'s `## Profile` section, field `Timezone` (IANA name, e.g., `Asia/Dubai`). Fall back to the system timezone if missing.
   - Convert to **UTC** when querying Slack and `gh` (both accept UTC ISO timestamps).
   - Pass `YYYY-MM-DD` to Jira and Confluence. **Caveat**: Jira evaluates JQL date literals in the *Jira user's profile timezone*, not UTC — if the Jira profile is on UTC while the user is on another TZ (e.g., Asia/Dubai), results drift by hours. Recommend aligning the Jira profile TZ to the user's local TZ.
   - Output filenames use the user's **local date** — matches how the user thinks about the day.

   **Multi-day ranges**: Loop internally over dates, executing steps 4–7 once per date. Produce one output file per date. One day's MCP responses fit in a single context window; multiple days may not.

4. **Collect from sources in parallel**:

   **Pagination — required for every source.** Loop until exhausted; never trust the first page as the full result.

   | Source | Mechanism |
   |---|---|
   | Slack | `cursor` — loop until no next cursor |
   | Jira | `startAt` + `maxResults` — loop until `isLast: true` or returned count `< maxResults` |
   | Confluence | Same as Jira via the Atlassian MCP |
   | GitHub (`gh`) | `--limit 100` per query is effectively always enough for a single day; warn-if-hit rather than paginate further |
   | Drive | `pageToken` — loop until no next page |

   **Stop-and-flag rule**: this skill always operates at single-day, single-user granularity (multi-day args loop one day at a time). At that scope, if pagination hits 5+ pages on any single source — stop and flag. 500 events from one source on one day for one person is anomalous — almost always a wrong date boundary or a missing identity filter. Don't carry the assumption beyond this scope.

   **On partial failure**: if a source fails after others have already returned data (e.g., Jira works, Confluence times out on page 2), capture what's available, mark the failed source under `## Gaps` with the error reason, set the file's `Status` to `PARTIAL`, and log `status=WARNING` via `/log`. Do not abort the whole run.

   **Slack:**
   - Search for messages from the user in the date range using their Slack user ID
   - Use `detailed` response format (never `concise` — it drops timestamps and permalinks). Set `include_context: false` to keep response size manageable; use `slack_read_thread` selectively for context.
   - Capture: channel, timestamp, message summary, permalink
   - Check threads where the user participated — decisions, guidance, approvals
   - Fold low-signal items (reactions, acks) into the related activity they refer to
   - Paginate using the `cursor` parameter when results hit the page limit
   - DMs are not accessible via MCP — ask the user about notable DMs at the end

   **Jira:**
   - Search for issues touched by the user in the date range using JQL. Two queries (no comment-specific query — `issueFunction in commented(...)` is not portable across Jira instances; assignee/reporter/creator/updated paths cover the common cases).
     1. **Updated**: `(assignee = currentUser() OR reporter = currentUser()) AND updated >= "YYYY-MM-DD" AND updated < "next_day"` — captures issues the user owns or reports that moved during the day.
     2. **Created**: `creator = "<accountId>" AND created >= "YYYY-MM-DD" AND created < "next_day"` — captures new issues the user filed.
   - **Date boundary**: use `>= "YYYY-MM-DD" AND < "next_day"` (not `<=` — Jira treats `<= "04-10"` as "before start of 04-10").
   - **Timezone caveat**: JQL date literals evaluate in the Jira user's profile timezone, not UTC. Confirm the Jira profile TZ matches the user's local TZ or expect drift.
   - Request minimal fields: `summary, status, issuetype, priority, updated`.
   - Capture: key, summary, status, what changed, issue URL.

   **GitHub:**
   - **Active-session flip-flop pattern**: env-var token-passing (`GH_TOKEN=$(...) gh ...`) is blocked by the sandbox's `$(...)` substitution guard. Instead, switch the active gh session to the cached business handle, run plain `gh` commands, then restore. Each step is a separate Bash call (allowlist-friendly):

     ```bash
     # Step 1: capture the previously-active user, in case it differs from the cached handle
     gh auth status   # parse the line preceding "Active account: true" — extract the handle

     # Step 2: switch to the cached business handle (skip if already active)
     gh auth switch --user <cached-handle>

     # Step 3: run the four searches as plain commands
     gh search prs --author "@me" --created "YYYY-MM-DD..YYYY-MM-DD" \
       --limit 100 --json number,title,url,repository,state,createdAt,updatedAt
     gh search prs --reviewed-by "@me" --updated "YYYY-MM-DD..YYYY-MM-DD" \
       --limit 100 --json number,title,url,repository,state
     gh search issues --author "@me" --created "YYYY-MM-DD..YYYY-MM-DD" \
       --limit 100 --json number,title,url,repository,state
     gh search issues --commenter "@me" --updated "YYYY-MM-DD..YYYY-MM-DD" \
       --limit 100 --json number,title,url,repository

     # Step 4: restore the previously-active user (try-finally semantics — always run, even on partial failure)
     gh auth switch --user <previously-active>
     ```

   - **Range syntax `A..B` is inclusive on both ends** — different from Jira's half-open convention above.
   - With the cached handle active, `@me` resolves to the business user. Authentication and visibility (private repos) are correct for the work account.
   - **Crash-safety**: if the skill exits between steps 2 and 4, the user is left on the cached handle. Add a one-line note to `## Gaps`: *"gh active session left as `<cached-handle>`; original session was `<previously-active>` — restore manually with `gh auth switch --user <previously-active>` if needed."*
   - For each result: capture the repo, number, title, and URL.
   - If `gh` is not available, note this gap and continue.

   **Confluence:**
   - Uses the same Atlassian MCP as Jira — no separate pre-flight check needed
   - Search for pages created or updated by the user in the date range using `searchConfluenceUsingCql` with CQL: `contributor = "{accountId}" AND lastmodified >= "YYYY-MM-DD" AND lastmodified < "next_day"` (same date boundary logic as Jira)
   - For each page: capture the space, title, type of contribution (created vs. updated), and the page URL
   - Also search for comments the user added on Confluence pages in the date range

   **Google Drive:**
   - **The MCP's query language only supports `title`, `fullText`, `mimeType`, `modifiedTime`, `viewedByMeTime` as query terms.** `owners` is **not** a supported field — neither `'email' in owners` nor `'me' in owners` works (both return *"Unsupported query field"*). Use a two-pronged approach instead:

     1. **Owned + edited by user** — call `mcp__claude_ai_Google_Drive__list_recent_files` with `orderBy: lastModifiedByMe`, paginate on `nextPageToken`, post-filter results in code by the local-day window (`createdTime`/`modifiedTime` falling in `[YYYY-MM-DDT00:00:00Z, NEXT_DAYT00:00:00Z)`). This catches files the user authored or modified.
     2. **Touched (viewed/co-edited) by user** — call `mcp__claude_ai_Google_Drive__search_files` with:

        ```
        query: "viewedByMeTime >= 'YYYY-MM-DDT00:00:00Z'
                and viewedByMeTime < 'NEXT_DAYT00:00:00Z'"
        pageSize: 100
        ```

        Paginate on `pageToken`. Use UTC bounds. Single quotes around values; escape inner singles as `\'`.

     Deduplicate the union by `id`.
   - For each result: capture title, MIME type, action (created vs. modified, inferred from `createdTime` vs. `modifiedTime`), and the file URL.
   - **Note on authorship inference**: the search response doesn't reliably name the writer for non-owned files. For items only surfaced via query (2), the user *touched* the file but may not have edited it. Flag uncertain items in `## Gaps` (e.g., *"Drive items {ids} surfaced via viewedByMeTime — authorship not confirmed"*) rather than asserting they edited.

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

7. **Capture a timestamp per item**: For each activity item, record the **earliest underlying event's timestamp** as ISO 8601 with timezone offset (e.g., `2026-04-12T14:32:00+04:00`). Use the user's timezone from `~/.claude/me/identity.md`. When an item spans multiple events (e.g., Slack thread + Jira update + PR), use the earliest. This enables downstream synthesis of time-based patterns (late-hour work, reactive windows, deferral over time).

8. **Write the output file**: Write to `.claude/memory/activity/collect-my-activity/YYYY-MM-DD-activity.md` (using the user's local date). Create parent directories if missing.

   **Re-run on the same date**: overwrite the file. Add a header line `**Re-collection**: previous run superseded YYYY-MM-DD HH:MM:SS` (UTC) below the title so the user can see this is a re-collection, not a fresh first run.

   ```markdown
   # My Activity: YYYY-MM-DD

   ## Status: SUCCESS
   **Sources checked**: Slack, Jira, Confluence, GitHub (gh CLI / N/A), Google Drive (MCP / N/A)

   ## Summary
   [1-2 sentences: what was the focus today]

   ## Activity

   ### [category]
   - **[brief description framed by impact, not just action]**
     - Time: 2026-04-12T14:32:00+04:00
     - Sources: [Slack permalink], [JIRA-123](url), [PR #45](url)
     - Context: [why this matters — what decision was made, what was unblocked, what risk was mitigated]

   ### [category]
   - ...

   ## Gaps
   - [sources that weren't accessible — e.g., "GitHub: gh CLI not available", "Google Drive: MCP not available", "DMs: not accessible via MCP"]
   ```

9. **Report to user**:

   ```
   Activity collected: YYYY-MM-DD
   ───────────────────────────────
   Items found: [count]
   Sources: Slack ([count]), Jira ([count]), Confluence ([count]), GitHub ([count or N/A]), Drive ([count or N/A])
   Gaps: [list any inaccessible sources]
   File: .claude/memory/activity/collect-my-activity/YYYY-MM-DD-activity.md

   Anything missing? Notable DMs, meetings, or whiteboard sessions to add?
   ```

## Important Rules

- **For team members' activity, use `/collect-team-activity`. This skill only collects the user's own.**
- **Every item must have at least one source link.** No exceptions. If you can't link to it, flag it as unverified.
- **Frame by impact, not action.** Not "commented on PLAT-301" but "Provided architectural direction on audit log strategy for Node.js upgrade (PLAT-301)".
- **Don't fabricate activity.** If a day is quiet, say so — that's useful signal.
- **Ask about gaps.** Always ask about DMs, meetings, and offline conversations at the end — these are invisible to MCP tools but often the most impactful work.
- **Respect date boundaries.** Only include activity that occurred within the requested date range. Don't pull in stale tickets just because they exist.
- **Always write the output file** — even on failure. The Status field (SUCCESS/PARTIAL/FAILED) lets calling agents check the result programmatically.
- **Identity write-back is fill-missing-only.** Never overwrite an existing value in `identity.md` from MCP — log a `WARNING` and surface the discrepancy instead.

## Logging

On completion (success or failure), invoke the `/log` skill:

```
/log run_id=<run_id> skill=collect-my-activity status=<SUCCESS|WARNING|FAILED> detail=<summary>
```

The `run_id` is passed by the calling agent (e.g., Chief of Staff). Use `manual` if invoked directly by the user.

## Expected `~/.claude/me/identity.md` format

The skill reads structured fields from a single `## Profile` section. Everything else in `identity.md` — Preferences, Writing Style, Growth areas, anything that surfaces during sessions — is human-curated and skills never touch it.

```markdown
# Identity

## Profile
- **Name**: {full name}
- **Git user**: {git username}
- **Role**: {e.g., Software Engineer, Engineering Manager, Director}
- **Timezone**: {IANA TZ, e.g., Asia/Dubai}
- **Slack user ID**: {e.g., U01ABC123}
- **Atlassian account ID**: {e.g., 712020:abcdef-1234-...}
- **Jira cloud ID**: {UUID}
- **GitHub username**: {handle}
- **Google Workspace email**: {email}

## Preferences
{Free-form — user-curated}

## Writing Style
{Free-form — user-curated}

## Growth areas
{Free-form — maintained by /bye}

{any other sections that surface during sessions}
```

**Skill contract:**
- **Read** any field by name from `## Profile`. Layout above and below this section is the user's.
- **Write back missing fields only** — append a new bullet under `## Profile` when MCP resolves a field that isn't already there. **Never overwrite an existing value.**
- **Never modify other sections** — Preferences, Writing Style, Growth areas, and any organic content remain user-owned.
