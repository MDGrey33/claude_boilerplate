---
name: linkedin-pitch-deflector
description: Sweep the user's unread LinkedIn DMs and handle cold outreach in two modes — deflect overt sales pitches with an assertive door-closing reply, and socially probe fresh ambiguous openers with a question that demands a genuine answer (real peers answer, sales personas pivot → then deflect); stay social through the sender's 3rd message, then hand genuine threads to the user. Drives the real logged-in Chrome via the chrome-control MCP. Trigger on "clear my sales pitches", "deflect pitches", "linkedin sales sweep", "kill the incoming sales", "check my linkedin messages", "/linkedin-pitch-deflector".
user_invocable: true
args: Optional. "review" (default — show batch, confirm once, then send) or "auto" (classify and send without per-batch confirmation). Optional cap like "10" to limit how many unread threads to scan.
allowed-tools: ToolSearch, mcp__chrome-control__tabs_context_mcp, mcp__chrome-control__navigate, mcp__chrome-control__computer, mcp__chrome-control__browser_batch, mcp__chrome-control__find, mcp__chrome-control__read_page, mcp__chrome-control__get_page_text, AskUserQuestion
---

# LinkedIn Pitch Deflector

## Purpose

Cold outreach on LinkedIn is high-volume. Most of it turns into a sales pitch by the sender's 2nd or 3rd message — but not all of it, and a blanket deflect-on-sight would also kill genuine peer conversations and inbound role offers. So this skill does **two** things:

1. **Deflects overt pitches** — anything already selling on message 1 gets one assertive, polite-but-final reply: a blanket no-incoming-sales policy with no hook to follow up on.
2. **Socially probes fresh, ambiguous openers** — a new conversation that's cold but hasn't shown its hand yet gets a warm reply that *demands a genuine, specific answer*. A real peer answers with substance; a sales persona pivots to its pitch — which exposes it, and then it gets deflected. Stay social through the sender's **3rd** message; if by then it still isn't a pitch, hand it to the user to engage honestly.

The user is fine with recipients realizing a deflection was machine-sent. **Do not hide the em-dash (—) or otherwise launder the writing to look hand-typed.** Transparency about the automated filter (on deflections) is acceptable and even reinforces the "this won't progress" message. The social probes, by contrast, are in the user's genuine voice — keep them honest and human (see rules).

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

- **Classification (pitch vs probe vs leave):** Sonnet — the recruiter-vs-vendor and pitch-vs-not-yet distinctions are nuanced and a false positive is costly.
- **Drafting the deflection:** Haiku — templated with light variation.
- **Drafting the social probe:** Sonnet — it must be genuinely human and domain-specific without fabricating the user's opinions.
- **Promote to Opus** only for a genuinely ambiguous thread the user asks you to judge.

## Triggers

- "clear my sales pitches", "deflect the pitches", "send the salespeople away"
- "linkedin sales sweep", "kill the incoming sales", "check my linkedin messages"
- "/linkedin-pitch-deflector"

## The flow

1. **Context.** Call `mcp__chrome-control__tabs_context_mcp` (`createIfEmpty: true`) — mandatory first call. Use the returned tabId throughout.
2. **Open unread.** `navigate` to `https://www.linkedin.com/messaging/`, click the **Unread** filter chip, screenshot to read the list.
3. **Triage from previews first.** Sender name + headline + last-message snippet is often enough. Only open ambiguous threads. **Opening a thread marks it read** — for any thread you open but don't reply to, re-mark it unread via the thread's `•••` → "Mark as unread".
4. **Classify** each thread into one of four outcomes: **DEFLECT**, **PROBE**, **LEAVE ALONE**, **HAND OFF**. Count the sender's messages — turn-count drives PROBE vs HAND OFF.
5. **Draft** the right reply: a deflection (templates below) for DEFLECT, a social probe (section below) for PROBE. Nothing for LEAVE ALONE / HAND OFF.
6. **Gate (default `review` mode):** present a compact table — sender · company · outcome · why · drafted reply — and take one confirmation via `AskUserQuestion` before sending. In `auto` mode, send then report.
7. **Send** each approved reply: click the message box, type, click **Send**, screenshot to confirm it posted (reply under the user's name with the sent check-mark).
8. **Report**: deflected / probed / handed off / left alone — and why.

## Classification rubric

The deciding question is **"who is the buyer?"** — but timing matters too. Count the sender's messages and whether they've shown their hand.

### DEFLECT — an overt sales pitch (any turn)
- Cold outreach selling a product, tool, platform, SaaS, agency, consulting, dev shop, or staffing/placement service **to the user or their company**.
- Discovery-question opener immediately followed by a solution / the product.
- Credibility drop + calendar CTA: *"we raised $X / YC / N GitHub stars … grab 15/30 min: cal.com/…"*.
- "Offering our engineers / experts / talent" (vendor staffing — they want the user to *buy* headcount).
- Agency / lead-gen / "we'll get you meetings, leads, pipeline" offers.
- Indirect pitches: free audit / teardown / trial that exists to book a sales call.
- **Also DEFLECT** a thread previously in PROBE the moment the sender's reply turns into any of the above — the probe did its job.

### PROBE — fresh, ambiguous cold opener (sender on message 1–3, not yet an overt pitch)
A new conversation from someone unknown that reads like cold outreach (founder/vendor "let's connect, my topics are X" intro, vague "would love to pick your brain", soft relationship-building) **but has not yet pitched anything**. Send a **social probe** (below) that demands a genuine, specific answer — the honesty test. Real peers answer with substance; sales personas pivot to their pitch (→ DEFLECT).
- Only while the sender is on their **1st, 2nd, or 3rd** message. Count messages *from them*.

### HAND OFF — genuine after 3 messages
If the sender has sent **3 messages and it still isn't a pitch**, the probe cleared them. Stop auto-replying; flag as "ready for the user to engage honestly." Never probe indefinitely.

### LEAVE ALONE — not cold outreach at all (never touch)
- **Recruiters with a concrete role for the user** — an inbound role offer is the opposite of spam (buyer test: they want to *hire* the user, not sell to them).
- Genuine networking, warm intros, "loved your post", reconnects from real contacts.
- Conference / podcast / panel / speaker invitations.
- Investors, founders, or peers discussing the user's own ventures.
- Anyone the user has already had genuine back-and-forth with; known contacts, ex-colleagues, friends.

**When unsure between PROBE and LEAVE ALONE**, lean PROBE (a warm question costs nothing). **When unsure whether something is even outreach**, leave it and list it for review. A missed pitch costs nothing; a deflected recruiter is a real loss.

## The deflection message

Assertive, blanket-policy, no future hook, short (2–4 sentences). Openly automated, **keep the em-dash**. Every deflection ends with the **mirror**: the open-source toolkit that just deflected them, with an invite to upgrade their own AI setup. Slot in `{Name}` / `{Company}` (omit `{Company}` if you can't read it).

Boilerplate URL to include: **https://github.com/MDGrey33/claude_boilerplate**

Templates:

1. **Mirror / advertise (default):**
   > Hi {Name} — automated reply. This account auto-deflects incoming sales, so this one won't progress. No hard feelings: since you're clearly running outreach, the open-source toolkit that just declined you is here → https://github.com/MDGrey33/claude_boilerplate — worth a look to level up your own AI setup. Best with {Company}.

2. **Policy-first, then mirror:**
   > Thanks {Name} — blanket no-incoming-sales policy here, so no need to follow up. If it's useful, the AI assistant that handles this (and a lot more) is open source: https://github.com/MDGrey33/claude_boilerplate. Genuinely wishing {Company} well.

3. **Tighter:**
   > {Name} — automated: hard no on incoming sales, nothing personal. The bot that sent this is open source if you want to sharpen your own stack → https://github.com/MDGrey33/claude_boilerplate. Best of luck.

Pick per-thread; lean warmer for courteous senders, firmer for aggressive or repeat ones.

## The social probe (for PROBE threads)

The goal: a warm, peer-level reply that **requires a genuine, specific answer** — one a real practitioner answers with a concrete war-story, and a sales persona can only answer by pivoting to its pitch. That pivot is the signal to deflect next round.

How to build one:
- **Anchor on their stated domain** and ask an open, specific question about *real problems in that domain* — not their product. "What's the hardest thing teams hit in production with X right now?" / "Where do you see most people get Y wrong?"
- **Stay genuinely curious and human.** Short, warm, peer-to-peer. One question, not an interview.
- **No commitment** — don't agree to calls, demos, or intros that advance *their* funnel.
- **Default to English** unless the user prefers mirroring the sender's language; don't commit the user to a language they may not want to continue in.

What their next message tells you:
- Substantive, specific answer about real work → genuine; keep probing (until msg 3) or HAND OFF.
- Pivot to "funny you ask, that's exactly what we built — got 20 min?" / any product or CTA → DEFLECT.

## Hard rules / Don'ts

- **Never deflect a recruiter pitching a role, a warm intro, a real peer, or an event invite.** Buyer test first, every time.
- **Probe, don't deflect, a fresh ambiguous opener.** Only deflect once a pitch is actually on the table.
- **Social probes are the user's real voice — never fabricate.** Ask open questions; do NOT put specific opinions, claims, experiences, or commitments in their mouth. Curiosity is safe; invented positions are not.
- **Respect the 3-message ceiling.** Stop auto-replying once the sender has sent 3 non-pitch messages — HAND OFF. Never run an endless probe loop.
- **Read-only until the gate.** In `review` mode, send nothing (deflection or probe) until the user confirms via `AskUserQuestion`.
- **Never send the same person twice in one sweep** — if the last message is already from the user, skip it.
- **Preserve unread state** — re-mark as unread any thread you opened but didn't reply to.
- **No edits beyond replying.** Don't archive, block, report, delete, or change connection status.
- **Don't fabricate** company names or details; omit `{Company}` if unknown.
- **One sweep, then stop.** Don't loop or re-scan unless asked.

## Report format

```
Deflected (N):
  • {Name} — {Company} — [pitch type] — reply sent ✓
Probed (P):       (fresh openers — sent a draw-them-out question, awaiting reply)
  • {Name} — {Company} — [their msg #] — probe sent ✓
Handed off (H):   (genuine after 3 messages — the user's to take honestly)
  • {Name} — [why genuine] — not auto-replied
Left alone (M):
  • {Name} — [recruiter / warm intro / event / known contact] — not touched
Could not classify (K):
  • {Name} — [reason] — left unread for review
```
