# Auto-Memory System (Optional)

A user-scope, typed-atomic-file memory system that complements the boilerplate's project-scope memory.

> **TL;DR:** Run `/setup-auto-memory` from any project to wire it into your `~/.claude/`. Nothing changes until you do.

## What this is

Claude Code's built-in auto-memory directory (`~/.claude/projects/<slug>/memory/`) is a per-project user-scope store of small typed markdown files that survive across sessions. The harness already drives reads and writes — but it ships with no template, no example, and no curation skill. This package fills that gap.

## How it differs from project memory

| | Project memory (already in boilerplate) | Auto-memory (this package) |
|---|---|---|
| Scope | Inside the repo (`repo/.claude/memory/`) | Per-project user dir (`~/.claude/projects/<slug>/memory/`) |
| Shared with collaborators | Yes — committed to git | No — local to this user |
| Format | Curated long-form (`lessons-learned.md`, `project-context.md`, `workstreams/`) | Many small typed files (`feedback_*.md`, `user_*.md`, `project_*.md`, `reference_*.md`) + `MEMORY.md` index |
| Loading | Always loaded via project CLAUDE.md | Always loaded via the harness, with `MEMORY.md` as index |
| Best for | Repo-level conventions, architecture, domain context | Personal preferences, behavioral feedback, identity that follows you across projects |

The two coexist. Project memory is curated knowledge about the *codebase*. Auto-memory is reflexes about the *user*.

## When to enable

Turn this on if:
- You repeatedly correct Claude on the same behavioral preferences ("don't summarize", "use type hints", "ask before deleting") and want them to stick
- You work across multiple repos and want personal context to follow you
- You've noticed Claude already creates files under `~/.claude/projects/<slug>/memory/` and you want a curation discipline around them

Skip this if:
- You only work in one repo and the project-scope memory is enough
- You don't want personal preferences persisted to disk

## What gets installed

Running `/setup-auto-memory`:

1. Creates `~/.claude/projects/<active-slug>/memory/` if missing
2. Copies a header-only `MEMORY.md` (the index)
3. Optionally seeds four sanitized example files (one per type)
4. Installs the `memory-hygiene` skill into `~/.claude/skills/memory-hygiene/`
5. Offers (does not auto-apply) a `claude-md-fragment.md` you can splice into your `~/CLAUDE.md` to make the type system visible on disk

Each step is gated. Nothing happens silently.

## Files in this package

```
auto-memory/
├── README.md                          # this file
├── MEMORY.md.template                 # header-only index, copied into your memory dir
├── claude-md-fragment.md              # optional CLAUDE.md splice
├── docs/
│   ├── type-system.md                 # the four memory types
│   ├── when-to-save.md                # save/skip rules + frontmatter format
│   └── examples/                      # one sanitized example per type
│       ├── feedback_example.md
│       ├── user_example.md
│       ├── project_example.md
│       └── reference_example.md
└── skills/
    └── memory-hygiene/                # curation skill (audit/promote/archive/compact)
        └── SKILL.md
```

## Uninstall

To remove: delete `~/.claude/skills/memory-hygiene/` and `~/.claude/projects/<slug>/memory/`. Roll back the CLAUDE.md fragment with `git diff` if you spliced it. The boilerplate's project-scope memory is unaffected — this package never touches it.

## See also

- `docs/type-system.md` — what each type is for
- `docs/when-to-save.md` — when Claude should write a memory and when not
- `skills/memory-hygiene/SKILL.md` — monthly cadence audit and promotion flow
