---
name: setup-auto-memory
description: Wire the optional auto-memory system into the user's ~/.claude/. Creates the per-project memory directory, copies templates and examples, installs the memory-hygiene curation skill, and offers a CLAUDE.md fragment that documents the type system on disk. Trigger "set up auto-memory", "enable auto-memory", "wire in auto-memory", "/setup-auto-memory".
user_invocable: true
---

# Setup Auto-Memory

## What this does

Wires the optional auto-memory system from `auto-memory/` (in this boilerplate) into the user's `~/.claude/`. After running this, the user has:

- `~/.claude/projects/<active-slug>/memory/MEMORY.md` — header-only index
- (optionally) four sanitized example memory files seeded into the same directory
- `~/.claude/skills/memory-hygiene/` — the curation skill
- (optionally) a `## Auto-Memory System` section appended to `~/CLAUDE.md` documenting the type system on disk

Nothing happens silently. Each step is gated.

## When to use

- User says "set up auto-memory", "enable auto-memory", "wire in auto-memory", "/setup-auto-memory"
- User asks how to make Claude remember things across sessions in a structured way
- User has read `auto-memory/README.md` and wants to opt in

## Prerequisites

- Run from inside a clone of the boilerplate (so `auto-memory/` is reachable)
- Active Claude Code project (so we can resolve `<active-slug>`)

## Steps

### 1. Resolve paths

Determine:
- `<boilerplate-root>` — find the directory containing `auto-memory/` and `.claude/`. If running from inside the boilerplate, this is the working directory; otherwise ask.
- `<active-slug>` — the active Claude Code project's slug under `~/.claude/projects/`. Get it by listing `~/.claude/projects/` and showing the user the candidates. If only one exists, use it. Otherwise ask which one.
- `<memory-dir>` = `~/.claude/projects/<active-slug>/memory/`

Confirm both with the user before proceeding.

### 2. Create the memory directory

```
mkdir -p <memory-dir>
mkdir -p <memory-dir>/archive
```

If `<memory-dir>` already exists with content, list what's there and ask whether to proceed. **Never overwrite** existing memory files.

### 3. Install MEMORY.md (if missing)

If `<memory-dir>/MEMORY.md` does not exist:

```
cp <boilerplate-root>/auto-memory/MEMORY.md.template <memory-dir>/MEMORY.md
```

If it already exists, skip — but show the user the existing file size and entry count so they know nothing was clobbered.

### 4. Offer to seed example memories

Ask the user: "Seed four sanitized example files (one per type) into the memory dir? They show the file shape and frontmatter."

Options:
- **Yes** → copy `auto-memory/docs/examples/*.md` into `<memory-dir>/`. Tell the user they can delete or edit them anytime.
- **No** → skip. The user will write memories from scratch.

### 5. Install the memory-hygiene skill

Ask: "Install the `memory-hygiene` skill at `~/.claude/skills/memory-hygiene/`?"

If `~/.claude/skills/memory-hygiene/` already exists, show its size + last-modified date and ask whether to overwrite, skip, or rename the existing one to `memory-hygiene.bak/`.

If yes:
```
mkdir -p ~/.claude/skills/memory-hygiene
cp <boilerplate-root>/auto-memory/skills/memory-hygiene/SKILL.md ~/.claude/skills/memory-hygiene/SKILL.md
```

### 6. Offer the CLAUDE.md fragment

Show the user the contents of `<boilerplate-root>/auto-memory/claude-md-fragment.md` (or the first ~30 lines + a "...full file at <path>" pointer) and ask:

> "Append this fragment to your `~/CLAUDE.md`? It re-states the auto-memory type system on disk so the rules are visible and editable, not just harness-resident."

Options:
- **Append to ~/CLAUDE.md** — read existing CLAUDE.md, append the fragment with a separating blank line. Show diff before writing.
- **Append to project CLAUDE.md** — same but to `./CLAUDE.md` if one exists.
- **Skip** — user will splice it manually later.

Never auto-append. Always show the diff and require confirmation.

### 7. Print verification commands

Output a block the user can run to confirm setup:

```
ls -la <memory-dir>
cat <memory-dir>/MEMORY.md
ls ~/.claude/skills/memory-hygiene/
```

And:

> "To exercise the system: in your next session, give Claude a feedback-shaped instruction (e.g. 'don't summarize at the end of every response'). Confirm a new `feedback_*.md` file appears in `<memory-dir>` and that `MEMORY.md` gets a new index line."

> "Run `/memory-hygiene audit` monthly (or when MEMORY.md exceeds 30 entries)."

## Idempotency

Re-running this skill on an already-set-up directory must:
- Not overwrite `MEMORY.md` if it has any entries
- Not overwrite any topic file
- Not silently overwrite the `memory-hygiene` skill — always ask first
- Not duplicate the CLAUDE.md fragment — grep for a marker line ("## Auto-Memory System") before offering

## Don't

- Don't run any of these steps without per-step confirmation.
- Don't write to `~/CLAUDE.md` without showing the diff first.
- Don't touch the boilerplate's project-scope memory at `repo/.claude/memory/` — this skill is exclusively about user-scope auto-memory.
- Don't enable any hook, scheduled task, or automation as part of setup. The user opts into those separately.

## Uninstall

Document for the user: to remove,
- Delete `~/.claude/skills/memory-hygiene/`
- Delete or rename `~/.claude/projects/<slug>/memory/`
- Roll back the CLAUDE.md fragment via `git diff ~/CLAUDE.md` (if their CLAUDE.md is in git) or by editing it manually
