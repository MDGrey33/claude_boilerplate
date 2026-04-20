# Keybindings

Source: https://code.claude.com/docs/en/keybindings

Requires Claude Code v2.1.18+.

## File

`~/.claude/keybindings.json`. Run `/keybindings` to create or open it.

Hot-reloaded: changes apply without restart.

## Structure

```json
{
  "$schema": "https://www.schemastore.org/claude-code-keybindings.json",
  "$docs": "https://code.claude.com/docs/en/keybindings",
  "bindings": [
    {
      "context": "Chat",
      "bindings": {
        "ctrl+e": "chat:externalEditor",
        "ctrl+u": null
      }
    }
  ]
}
```

- `$schema` — optional JSON Schema URL for editor autocompletion.
- `$docs` — optional doc URL.
- `bindings` — array of context blocks, each with a keystroke→action map.

## Contexts

| Context | Scope |
|:--|:--|
| `Global` | Everywhere |
| `Chat` | Main chat input |
| `Autocomplete` | Autocomplete menu open |
| `Settings` | Settings menu |
| `Confirmation` | Permission / confirmation dialogs |
| `Tabs` | Tab navigation |
| `Help` | Help menu visible |
| `Transcript` | Transcript viewer |
| `HistorySearch` | History search (Ctrl+R) |
| `Task` | Background task running |
| `ThemePicker` | Theme picker |
| `Attachments` | Image navigation in select dialogs |
| `Footer` | Footer indicator nav |
| `MessageSelector` | Rewind / summarize dialog |
| `DiffDialog` | Diff viewer |
| `ModelPicker` | Model picker effort |
| `Select` | Generic select/list |
| `Plugin` | Plugin dialog |
| `Scroll` | Fullscreen conversation scrolling and text selection |
| `Doctor` | `/doctor` diagnostics |

## Action namespaces

Each context has specific actions in `namespace:action` form.

### `app:*` (Global)

| Action | Default |
|:--|:--|
| `app:interrupt` | `Ctrl+C` (reserved, cannot rebind) |
| `app:exit` | `Ctrl+D` (reserved) |
| `app:redraw` | unbound |
| `app:toggleTodos` | `Ctrl+T` |
| `app:toggleTranscript` | `Ctrl+O` |

### `history:*`

| Action | Default |
|:--|:--|
| `history:search` | `Ctrl+R` |
| `history:previous` | `Up` |
| `history:next` | `Down` |

### `chat:*`

| Action | Default |
|:--|:--|
| `chat:cancel` | `Escape` |
| `chat:clearInput` | `Ctrl+L` |
| `chat:killAgents` | `Ctrl+X Ctrl+K` |
| `chat:cycleMode` | `Shift+Tab`* |
| `chat:modelPicker` | `Cmd/Meta+P` |
| `chat:fastMode` | `Meta+O` |
| `chat:thinkingToggle` | `Cmd/Meta+T` |
| `chat:submit` | `Enter` |
| `chat:newline` | `Ctrl+J` |
| `chat:undo` | `Ctrl+_` / `Ctrl+Shift+-` |
| `chat:externalEditor` | `Ctrl+G` / `Ctrl+X Ctrl+E` |
| `chat:stash` | `Ctrl+S` |
| `chat:imagePaste` | `Ctrl+V` (`Alt+V` on Windows) |

*On Windows without VT mode (Node <24.2.0/<22.17.0, Bun <1.2.23),
`chat:cycleMode` defaults to `Meta+M`.

### `autocomplete:*`

`accept` (Tab), `dismiss` (Escape), `previous` (Up), `next` (Down).

### `confirm:*`

`yes` (Y/Enter), `no` (N/Escape), `previous` (Up), `next` (Down),
`nextField` (Tab), `toggle` (Space), `cycleMode` (Shift+Tab),
`toggleExplanation` (Ctrl+E).

### `permission:*` (in Confirmation context)

`permission:toggleDebug` (Ctrl+D).

### Other namespaces

`transcript:*`, `historySearch:*`, `task:*`, `theme:*`, `help:*`,
`tabs:*`, `attachments:*`, `footer:*`, `messageSelector:*`, `diff:*`,
`modelPicker:*`, `select:*`, `plugin:*`, `settings:*`, `doctor:*`,
`voice:*` (voice dictation), `scroll:*` (fullscreen), `selection:*`
(text selection in fullscreen).

Full tables in the docs.

## Keystroke syntax

### Modifiers

| Modifier | Aliases |
|:--|:--|
| Control | `ctrl`, `control` |
| Alt/Option | `alt`, `opt`, `option` |
| Shift | `shift` |
| Meta/Command | `meta`, `cmd`, `command` |

Combine with `+`: `ctrl+k`, `shift+tab`, `meta+p`, `ctrl+shift+c`.

### Uppercase letters

Standalone uppercase implies Shift: `K` = `shift+k`. Useful for vim-style
(uppercase vs lowercase different meanings).

Uppercase + modifier is stylistic and does NOT imply Shift: `ctrl+K` =
`ctrl+k`.

### Chords

Separate keystrokes with spaces: `ctrl+x ctrl+s` means press Ctrl+X,
release, then Ctrl+S.

### Special keys

`escape`/`esc`, `enter`/`return`, `tab`, `space`, `up`/`down`/`left`/
`right`, `backspace`, `delete`.

## Unbinding defaults

Set the action to `null`:

```json
{
  "bindings": [
    { "context": "Chat", "bindings": { "ctrl+s": null } }
  ]
}
```

Works for chord bindings too. Unbinding every chord sharing a prefix frees
that prefix as single-key:

```json
{
  "bindings": [
    {
      "context": "Chat",
      "bindings": {
        "ctrl+x ctrl+k": null,
        "ctrl+x ctrl+e": null,
        "ctrl+x": "chat:newline"
      }
    }
  ]
}
```

If you unbind some-but-not-all chords on a prefix, pressing the prefix
still enters chord-wait mode for the remaining ones.

## Reserved shortcuts

Cannot be rebound:

| Shortcut | Reason |
|:--|:--|
| `Ctrl+C` | Hardcoded interrupt/cancel |
| `Ctrl+D` | Hardcoded exit |
| `Ctrl+M` | Identical to Enter in terminals (both send CR) |

## Terminal conflicts

Some shortcuts may conflict with multiplexers:

| Shortcut | Conflict |
|:--|:--|
| `Ctrl+B` | tmux prefix (press twice to send) |
| `Ctrl+A` | GNU screen prefix |
| `Ctrl+Z` | Unix SIGTSTP |

## Vim mode interaction

Vim mode (`/config` → Editor mode = `vim`) operates at text input level
independently of keybindings:

- Vim handles cursor movement, modes, motions.
- Keybindings handle component-level actions (toggle todos, submit, etc.).
- Escape in vim switches INSERT → NORMAL; does NOT trigger `chat:cancel`.
- Most Ctrl+key shortcuts pass through to the keybinding system.
- In vim NORMAL, `?` shows help menu (vim behavior).

## Validation

Claude Code validates and warns for:
- Parse errors (invalid JSON or structure).
- Invalid context names.
- Reserved shortcut conflicts.
- Terminal multiplexer conflicts.
- Duplicate bindings in the same context.

Run `/doctor` to see warnings.

## Disambiguation

- **Keybinding vs slash command:** keybinding triggers a harness action
  (submit, toggle, navigate); slash command runs a prompt/command. Use
  keybindings for navigation and editor actions; use skills/commands for
  prompts.
- **Keybinding vs hook:** keybindings respond to keyboard input;
  hooks respond to lifecycle events. Different triggers entirely.

## Gotchas

- `Ctrl+C`, `Ctrl+D`, `Ctrl+M` are reserved.
- Chord prefixes must be cleared to use as single keys.
- Vim mode silently swallows some keys from the keybinding system.
- `Ctrl+B` conflicts with tmux; won't trigger in tmux sessions without
  prefix press twice.

## Minimal example

```json
{
  "$schema": "https://www.schemastore.org/claude-code-keybindings.json",
  "bindings": [
    {
      "context": "Chat",
      "bindings": {
        "ctrl+e": "chat:externalEditor",
        "ctrl+u": null,
        "ctrl+x": "chat:newline"
      }
    }
  ]
}
```

Delegate authoring to the `keybindings-help` skill.
