# Memory — CLAUDE.md and auto-memory

Source: https://code.claude.com/docs/en/memory

## Two complementary systems

|                   | CLAUDE.md          | Auto memory                      |
|:------------------|:-------------------|:---------------------------------|
| Written by        | You                | Claude                           |
| Content           | Instructions/rules | Learnings/patterns               |
| Scope             | Project/user/org   | Per working tree                 |
| Loaded            | Every session (full) | First 200 lines / 25 KB of `MEMORY.md` |
| Use for           | Coding standards, architecture, workflows | Build commands, debugging notes, recurring patterns |

**Both are context, not enforced configuration.** For enforcement, use
hooks or permission rules.

## CLAUDE.md

### Locations (specific → broad)

| Scope | Path |
|:--|:--|
| Managed | macOS `/Library/Application Support/ClaudeCode/CLAUDE.md`; Linux/WSL `/etc/claude-code/CLAUDE.md`; Windows `C:\Program Files\ClaudeCode\CLAUDE.md` |
| Project | `./CLAUDE.md` or `./.claude/CLAUDE.md` |
| User | `~/.claude/CLAUDE.md` |
| Local (project-local) | `./CLAUDE.local.md` (gitignored) |

### How they load

Claude Code walks up from cwd, loading every CLAUDE.md and CLAUDE.local.md
it finds. All discovered files are **concatenated** into context, not
overridden. Within each directory, `CLAUDE.local.md` is appended after
`CLAUDE.md`.

Subdirectory CLAUDE.md files DO exist — they load **on demand** when Claude
reads a file in that subdirectory, not at session start.

Block-level HTML comments (`<!-- ... -->`) are stripped before injection.
Comments inside code blocks are preserved.

### Imports

`@path/to/file` in any CLAUDE.md imports another file. Relative (to the
file, not cwd) or absolute. Max recursion depth 5. External (outside
project) imports trigger a one-time approval dialog.

Pattern for per-worktree personal preferences:

```
# in CLAUDE.md
@~/.claude/my-project-instructions.md
```

### AGENTS.md

Claude does NOT read AGENTS.md by default. Pattern:

```markdown
# CLAUDE.md
@AGENTS.md

## Claude Code specific
Use plan mode for changes under src/billing/.
```

### Size guidance

Target under 200 lines per CLAUDE.md. Longer files reduce adherence and
burn context. Split via `@`-imports or `.claude/rules/*.md`.

### `--add-dir` and CLAUDE.md

CLAUDE.md files from `--add-dir` directories are **NOT** loaded by default.
Set `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1` to load them. Also
loads `.claude/CLAUDE.md`, `.claude/rules/*.md`, `CLAUDE.local.md` (local
requires `local` setting source, enabled by default).

## `.claude/rules/`

Modular, topic-specific instruction files. All `.md` discovered
recursively. Each can have optional frontmatter `paths:` with glob
patterns scoping the rule to matching files.

```markdown
---
paths:
  - "src/api/**/*.ts"
---

# API Development Rules

- All endpoints must include input validation
- Use the standard error response format
- Include OpenAPI documentation comments
```

Unconditional rules (no `paths:`) load at session start with same priority
as `.claude/CLAUDE.md`. Path-scoped rules trigger when Claude reads
matching files.

User-level: `~/.claude/rules/` applies to every project. Symlinks
supported (circular detected).

## Managed CLAUDE.md (org-wide)

Deploy via MDM, Group Policy, or Ansible to the platform-specific path.
Cannot be excluded by `claudeMdExcludes`. Pairs with managed settings:

| Concern | Configure in |
|:--|:--|
| Block tools/commands/paths | Managed settings `permissions.deny` |
| Sandbox enforcement | Managed settings `sandbox.enabled` |
| Auth/API routing/env | Managed settings |
| Code style guidelines | Managed CLAUDE.md |
| Compliance reminders | Managed CLAUDE.md |
| Behavioral instructions | Managed CLAUDE.md |

## `claudeMdExcludes`

In `.claude/settings.local.json`:

```json
{
  "claudeMdExcludes": [
    "**/monorepo/CLAUDE.md",
    "/home/user/monorepo/other-team/.claude/rules/**"
  ]
}
```

Glob on absolute paths. Arrays merge across settings layers. Managed
CLAUDE.md is NOT excludable.

## Auto-memory

### Toggle

Default on. Disable:
- `/memory` → auto-memory toggle.
- `"autoMemoryEnabled": false` in settings.
- `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` env var.

Requires Claude Code v2.1.59+.

### Storage

Default: `~/.claude/projects/<project>/memory/`. The `<project>` path is
derived from git repo, so worktrees/subdirs of the same repo share one
directory. Outside git, project root is used.

Override: `autoMemoryDirectory` in user/policy/local settings. NOT
accepted in project settings (to prevent shared repos from redirecting
writes to sensitive paths).

### Structure

```
~/.claude/projects/<project>/memory/
├── MEMORY.md          # index, first 200 lines / 25 KB loaded at session start
├── debugging.md       # topic file, loaded on demand
├── api-conventions.md
└── ...
```

`MEMORY.md` is the index. Claude reads/writes files throughout a session,
keeping `MEMORY.md` concise by moving detail into topic files.

Auto-memory is **machine-local**. Not synced across machines.

### Privacy

Files are plain markdown — open in your editor. Run `/memory` to browse.
When you say "remember that the API tests need Redis", Claude saves to
auto-memory. To add to CLAUDE.md instead, ask "add this to CLAUDE.md" or
edit yourself.

## Compaction behavior

- Project-root CLAUDE.md **survives** compaction (re-injected).
- Nested CLAUDE.md files do NOT auto-re-inject; they reload next time
  Claude reads a file in that subdir.
- If an instruction disappeared after `/compact`, it was either only in
  conversation or in a nested CLAUDE.md that hasn't reloaded. Move it to a
  loaded CLAUDE.md.

## `/init`

Run `/init` to generate a starting CLAUDE.md from codebase analysis.
Existing CLAUDE.md → `/init` suggests improvements instead.

`CLAUDE_CODE_NEW_INIT=1` enables an interactive multi-phase flow: picks
which artifacts (CLAUDE.md, skills, hooks, personal memory), explores with
a subagent, asks follow-ups, presents reviewable proposal.

## `/memory`

Lists all CLAUDE.md + CLAUDE.local.md + `.claude/rules/` files loaded in
current session. Toggle auto-memory. Link to auto-memory folder. Select
any file to open in your editor.

## Troubleshooting

- **"Claude isn't following my CLAUDE.md"** — CLAUDE.md is delivered as a
  user message after the system prompt. Not enforced. Debug:
  `/memory` to verify loading; check location is loaded; make instructions
  specific and concrete; look for conflicts across scopes. For
  system-prompt-level instructions, use `--append-system-prompt` (passed
  every invocation, not persistent).
- **InstructionsLoaded hook** — logs which files load and why. Useful for
  debugging path-scoped rules.
- **Too large?** Move detail to `@`-imports or `.claude/rules/`.
- **Stale after /compact** — project root CLAUDE.md re-injects; conversation-only
  instructions get dropped.

## Gotchas

- Memory is **context, not enforcement.** For "always do X", write a hook.
- `autoMemoryDirectory` does NOT work from project settings.
- `--add-dir` doesn't load CLAUDE.md unless env var is set.
- `@` imports a file at load time, not at reference time.
- Comments outside code blocks are stripped.

## Disambiguation

- **Memory vs skill:** memory always in context; skill body only when
  invoked. Use CLAUDE.md for facts always true; skill for procedures.
- **Memory vs hook:** memory is interpreted; hook is executed. "From now
  on, always X" → hook, not memory.
- **Memory vs settings:** both are config-ish, but settings are enforced
  (permissions, env, hooks); memory is behavioral guidance.
- **Auto-memory vs CLAUDE.md:** auto-memory is Claude's own notes — what
  it learned. CLAUDE.md is your rules — what you wrote.

## Minimal example

```markdown
# CLAUDE.md (project root)

## Build commands
- `npm run lint` before committing
- `npm test` — full suite, ~2 minutes
- `npm run test:unit` — unit only, ~10s

## Architecture
- API handlers live in `src/api/handlers/`
- Shared utilities in `src/lib/`

## Conventions
- 2-space indentation
- Prefer arrow functions for callbacks
- No console.log in committed code

## Rules
@.claude/rules/security.md
@.claude/rules/testing.md
```
