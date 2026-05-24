---
name: linkedin-pitch-deflector
description: Sweep the user's unread LinkedIn DMs, identify sales pitches (direct or indirect), and reply with an assertive, door-closing deflection so the sender goes away and doesn't come back. Drives the real logged-in Chrome via the chrome-control MCP. Trigger on "clear my sales pitches", "deflect pitches", "linkedin sales sweep", "kill the incoming sales", "/linkedin-pitch-deflector".
user_invocable: true
args: Optional. "review" (default — show batch, confirm once, then send) or "auto" (classify and send without per-batch confirmation). Optional cap like "10" to limit how many unread threads to scan.
allowed-tools: ToolSearch, mcp__chrome-control__tabs_context_mcp, mcp__chrome-control__navigate, mcp__chrome-control__computer, mcp__chrome-control__browser_batch, mcp__chrome-control__find, mcp__chrome-control__read_page, mcp__chrome-control__get_page_text, AskUserQuestion
---

## Purpose

Cold sales outreach on LinkedIn is high-volume and low-signal. This skill finds the unread DMs that are pitches and shuts each one down with a single assertive, polite-but-final reply — a blanket no-incoming-sales policy that leaves no hook to follow up on.

The reply is transparent about being automated; it does not pretend to be hand-typed. That transparency reinforces the "this won't progress" message and — as a friendly twist — points the sender at the open-source toolkit that just deflected them, inviting them to upgrade their own AI setup.

## Prerequisites

The `chrome-control` MCP must be available (tools named `mcp__chrome-control__*`). Claude Code ships the Chrome integration but only loads it when registered. Register it once (it persists in `~/.claude.json`):

```
claude mcp add chrome-control --scope user -- claude --claude-in-chrome-mcp
```

Notes:
- The reserved name `claude-in-chrome` is blocked; register under another name (e.g. `chrome-control`).
- MCP servers load at session start — after registering, start a fresh Claude Code session before the tools appear.
- Chrome must be open and logged into LinkedIn as the user, with the Claude browser extension installed.
- If `ToolSearch` for `mcp__chrome-control__*` returns nothing, the session predates the registration — restart Claude Code.

## Model Selection

- **Classification (pitch vs not):** Sonnet — the recruiter-vs-vendor distinction is nuanced and a false positive is costly.
- **Drafting the deflection:** Haiku — templated with light variation.
- **Promote to Opus** only for a genuinely ambiguous thread the user asks you to judge.

## Triggers

- "clear my sales pitches", "deflect the pitches", "send the salespeople away"
- "linkedin sales sweep", "kill the incoming sales", "clean my linkedin DMs of sales"
- "/linkedin-pitch-deflector"

## The flow

1. **Context.** Call `mcp__chrome-control__tabs_context_mcp` (`createIfEmpty: true`) — mandatory first call. Use the returned tabId throughout.
2. **Open unread.** `navigate` to `https://www.linkedin.com/messaging/`, click the **Unread** filter chip, screenshot to read the list.
3. **Triage from previews first.** Sender name + headline + last-message snippet is often enough to classify without opening. Only open ambiguous threads. **Opening a thread marks it read** — for any thread you open that is NOT a pitch, re-mark it unread via the thread's `•••` → "Mark as unread" to preserve the user's real unread state.
4. **Classify** each unread thread against the rubric below.
5. **Draft** an assertive deflection per confirmed pitch (templates below), varying wording lightly.
6. **Gate (default `review` mode):** present a compact table — sender · company · why-it's-a-pitch · drafted reply — and take one confirmation via `AskUserQuestion` before sending any. In `auto` mode, skip the gate, send, then report.
7. **Send** each approved reply: click the message box, type the reply, click **Send**, screenshot to confirm it posted (reply appears under the user's name with the sent check-mark).
8. **Report**: who was deflected, who was left alone and why, and any threads you couldn't classify.

## Classification rubric

The deciding question is **"who is the buyer?"**

### DEFLECT — it's a sales pitch (direct or indirect)
- Cold outreach selling a product, tool, platform, SaaS, agency, consulting, dev shop, or staffing/placement service **to the user or their company**.
- Discovery-question openers aimed at a product: *"what's your biggest challenge with X?"*, *"how are you handling Y today?"* followed by a solution.
- Credibility drop + calendar CTA: *"we raised $X / YC / N GitHub stars … grab 15/30 min: cal.com/…"*.
- "Offering our engineers / experts / talent" (vendor staffing — they want the user to *buy* headcount).
- Agency / lead-gen / "we'll get you meetings, leads, pipeline" offers.
- Indirect pitches: free audit / teardown / trial that exists to book a sales call.

### LEAVE ALONE — not a pitch (never deflect these)
- **Recruiters with a concrete role for the user.** If the user is job-hunting, an inbound role is valuable — the opposite of spam. Buyer test: they want to *hire the user*, not sell to them.
- Genuine networking, warm intros, "loved your post", reconnects from real contacts.
- Conference / podcast / panel / speaker invitations.
- Investors, founders, or peers discussing the user's own ventures.
- Anyone the user has already had genuine back-and-forth with.
- Known contacts, ex-colleagues, friends.

**When genuinely unsure → DO NOT deflect.** Leave it unread and list it under "left for review." A missed pitch costs nothing; a deflected recruiter or warm intro is a real loss.

## The deflection message

Assertive, blanket-policy, no future hook, short (2–4 sentences). It is openly automated and includes the open-source link with an invite. Vary wording across recipients. Slot in `{Name}` and `{Company}` (omit `{Company}` if you can't read it).

Boilerplate URL to include: **https://github.com/MDGrey33/claude_boilerplate**

Templates:

1. **Mirror / advertise (default):**
   > Hi {Name} — automated reply. This account auto-deflects incoming sales, so this one won't progress. No hard feelings: since you're clearly running outreach, the open-source toolkit that just declined you is here → https://github.com/MDGrey33/claude_boilerplate — worth a look to level up your own AI setup. Best with {Company}.

2. **Policy-first, then mirror:**
   > Thanks {Name} — blanket no-incoming-sales policy here, so no need to follow up. If it's useful, the AI assistant that handles this (and a lot more) is open source: https://github.com/MDGrey33/claude_boilerplate. Genuinely wishing {Company} well.

3. **Tighter:**
   > {Name} — automated: hard no on incoming sales, nothing personal. The bot that sent this is open source if you want to sharpen your own stack → https://github.com/MDGrey33/claude_boilerplate. Best of luck.

Pick per-thread; lean warmer for courteous senders, firmer for aggressive or repeat ones.

## Hard rules / Don'ts

- **Never deflect a recruiter pitching a role, a warm intro, a real peer, or an event invite.** Buyer test first, every time.
- **Read-only until the gate.** In `review` mode, send nothing until the user confirms the batch with `AskUserQuestion`.
- **Never send the same person twice** — if the last message in the thread is already from the user (a prior deflection), skip it.
- **Preserve unread state** — re-mark as unread any non-pitch thread you had to open.
- **No edits beyond replying.** Don't archive, block, report, delete, or change connection status.
- **Don't fabricate** company names or details; omit `{Company}` if unknown.
- **One sweep, then stop.** Don't loop or re-scan unless asked.

## Report format

```
Deflected (N):
  • {Name} — {Company} — [pitch type] — reply sent ✓
Left alone (M):
  • {Name} — [recruiter / warm intro / event / unsure] — not touched
Could not classify (K):
  • {Name} — [reason] — left unread for review
```
