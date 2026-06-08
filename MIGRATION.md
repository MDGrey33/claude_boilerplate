# Migration Notes

`/setup-workspace sync` copies new and updated upstream files into your workspace,
but it **never deletes**. It can't safely auto-prune, because a file present in
your workspace but absent upstream is ambiguous — it might be a skill/agent you
added locally, or one that upstream removed or renamed. `sync` lists these under
`local-only` (`?`) and leaves them in place.

So when upstream **removes or renames** a skill, an existing workspace keeps the
old copy until you delete it by hand. This page records those removals/renames so
you know what is safe to delete after syncing.

## How to apply

After `/setup-workspace sync`, review the `local-only` list. Anything below that
still exists in your workspace can be removed:

```bash
# from your workspace root
rm -rf .claude/skills/<removed-or-old-skill-name>
```

## Removed / renamed skills

| Change | Action in an existing workspace |
|---|---|
| **Removed** `setup-nemoclaw` | `rm -rf .claude/skills/setup-nemoclaw` |
| **Renamed** `voice-setup` → `setup-voice` | `rm -rf .claude/skills/voice-setup` (the new `setup-voice` deploys on sync) |

`/setup-nemoclaw` was removed because it instructed users to run an install
script from a non-existent URL and carried environment-specific content unfit for
Memnyx. If you deployed it before, delete the leftover directory as
above.
