#!/usr/bin/env bash
# discover-setup.sh — claude-expert environment introspection.
#
# Self-tuning companion to the claude-expert skill. The skill's
# discovery-dependent docs reference THIS script's output instead of
# hardcoding any one person's setup, so the reference adapts to whoever
# installs the boilerplate.
#
# Contract: READ-ONLY introspection. The ONLY thing it may create is the
# staging dir (see STAGING_DIR). It is $HOME-based, POSIX-ish bash, and
# FAILS SOFT — a missing dir/tool reports "none"/"not found", never errors.
#
# Usage:  bash discover-setup.sh        (chmod +x to run as ./discover-setup.sh)
# Output: a header, then a greppable KEY=VALUE map plus a per-type manager table.

# Note: no `set -e` on purpose — discovery must survive missing dirs/tools.
set -u

# ---- helpers ---------------------------------------------------------------
# List immediate subdir names of $1, or "none" if absent/empty. Read-only.
list_subdirs() {
  [ -d "$1" ] || { printf 'none'; return; }
  local out; out=$(find "$1" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; 2>/dev/null \
    | sort | paste -sd, - 2>/dev/null)
  printf '%s' "${out:-none}"
}

# Does any installed skill's name OR description manage artifact-type $1?
# Strategy: (a) conventional manager names for the type, then (b) scan SKILL.md
# descriptions for "<type> ... (lifecycle )?manager". Prints PRESENT|<hit> or ABSENT.
detect_manager() {
  local type="$1"; shift
  local conventional="$*"        # space-separated conventional skill dir-names
  local d skill name
  for d in "${SKILL_SEARCH[@]}"; do
    [ -d "$d" ] || continue
    for name in $conventional; do
      [ -d "$d/$name" ] && { printf 'PRESENT|%s' "$name"; return; }
    done
    # description scan across every SKILL.md under this skills dir
    for skill in "$d"/*/SKILL.md; do
      [ -f "$skill" ] || continue
      if grep -qiE "${type}[a-z ]*(lifecycle )?manager" "$skill" 2>/dev/null; then
        printf 'PRESENT|%s' "$(basename "$(dirname "$skill")")"; return
      fi
    done
  done
  printf 'ABSENT'
}

# Pull hook events + commands out of a settings.json without requiring jq.
parse_hooks() {
  local f="$1"; [ -f "$f" ] || return
  if command -v jq >/dev/null 2>&1; then
    jq -r '(.hooks // {}) | to_entries[] | .key as $e
           | (.value[]?.hooks[]? | "\($e)=\(.command // .type // "?")")' "$f" 2>/dev/null
  elif command -v python3 >/dev/null 2>&1; then
    python3 - "$f" 2>/dev/null <<'PY'
import json,sys
try: h=json.load(open(sys.argv[1])).get("hooks",{})
except Exception: sys.exit(0)
for ev,arr in (h or {}).items():
    for m in arr or []:
        for hk in m.get("hooks",[]) or []:
            print(f'{ev}={hk.get("command", hk.get("type","?"))}')
PY
  else
    grep -oE '"(PreToolUse|PostToolUse|UserPromptSubmit|SessionStart|SessionEnd|Stop|SubagentStop|PreCompact)"' \
      "$f" 2>/dev/null | tr -d '"' | sort -u
  fi
}

# ---- search roots (user + project; $HOME-based, never a hardcoded path) -----
USER_SKILLS="$HOME/.claude/skills"; PROJ_SKILLS="./.claude/skills"
USER_AGENTS="$HOME/.claude/agents"; PROJ_AGENTS="./.claude/agents"
USER_SETTINGS="$HOME/.claude/settings.json"; PROJ_SETTINGS="./.claude/settings.json"
SKILL_SEARCH=("$USER_SKILLS" "$PROJ_SKILLS")

# ---- STAGING_DIR: where self-update writes reports (never a personal inbox) --
# Resolve order: $CLAUDE_EXPERT_STAGING → ./.claude-expert.staging file → default.
SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd)"
if [ -n "${CLAUDE_EXPERT_STAGING:-}" ]; then
  STAGING_DIR="$CLAUDE_EXPERT_STAGING"
elif [ -f "./.claude-expert.staging" ]; then
  STAGING_DIR="$(head -n1 ./.claude-expert.staging 2>/dev/null)"
else
  STAGING_DIR="${SELF_DIR:-.}/.staging"
fi
mkdir -p "$STAGING_DIR" 2>/dev/null || true   # the one permitted write

# ---- PYTHON_PORT: local clone of the open community Python reimplementation --
# Search $CLAUDE_PYTHON_PORT then ~/code for known dir names. Read-only.
PYTHON_PORT="not found -> clone the open SafeRL-Lab Python reimplementation of Claude Code to enable under-the-hood verification"
for cand in "${CLAUDE_PYTHON_PORT:-}" \
            "$HOME/code/nano-claude-code" "$HOME/code/cheetahclaws"; do
  [ -n "$cand" ] && [ -d "$cand" ] && { PYTHON_PORT="$cand"; break; }
done
if [ "${PYTHON_PORT:0:9}" = "not found" ] && [ -d "$HOME/code" ]; then
  hit=$(find "$HOME/code" -maxdepth 1 -type d \( -iname '*nano-claude*' -o -iname '*cheetahclaws*' \) 2>/dev/null | head -n1)
  [ -n "$hit" ] && PYTHON_PORT="$hit"
fi

# ---- emit: header + KEY=VALUE map ------------------------------------------
echo "# claude-expert setup discovery — $(date '+%Y-%m-%d %H:%M') — HOME=$HOME"
echo "# (read-only introspection; self-tuning. Re-run after changing your setup.)"
echo
echo "SKILLS_DIRS=$USER_SKILLS,$PROJ_SKILLS"
echo "SKILLS_INSTALLED_USER=$(list_subdirs "$USER_SKILLS")"
echo "SKILLS_INSTALLED_PROJECT=$(list_subdirs "$PROJ_SKILLS")"
echo "AGENTS_DIRS=$USER_AGENTS,$PROJ_AGENTS"
echo "AGENTS_INSTALLED_USER=$(list_subdirs "$USER_AGENTS")"
echo "AGENTS_INSTALLED_PROJECT=$(list_subdirs "$PROJ_AGENTS")"
echo "STAGING_DIR=$STAGING_DIR"
echo "PYTHON_PORT=$PYTHON_PORT"

# Hooks (user + project settings merged; "none" if neither configures any).
hooks_out=$( { parse_hooks "$USER_SETTINGS"; parse_hooks "$PROJ_SETTINGS"; } | sort -u | paste -sd';' - )
echo "HOOKS=${hooks_out:-none}"

# ---- emit: per-artifact-type MANAGERS table --------------------------------
# Each row: does a lifecycle manager exist for this artifact TYPE? Conventional
# names are EXAMPLES (your roster may differ); ABSENT flags a coverage gap.
echo
echo "## MANAGERS (per artifact type — PRESENT means a lifecycle manager was detected)"
echo "| type | status | matched-skill |"
echo "|:--|:--|:--|"
emit_row() {  # $1=type-label  $2=type-keyword  $3...=conventional names
  local label="$1" kw="$2"; shift 2
  local r; r=$(detect_manager "$kw" "$@")
  if [ "$r" = "ABSENT" ]; then
    echo "| $label | ABSENT (gap) | — |"
  else
    echo "| $label | PRESENT | ${r#PRESENT|} |"
  fi
}
emit_row "skills"      "skill"    skills-manager
emit_row "agents"      "agent"    agent-manager
emit_row "hooks"       "hook"     hooks-manager
emit_row "loops"       "loop"     loops-manager
emit_row "schedules"   "schedule" schedules-manager
emit_row "plugins"     "plugin"   plugins-manager
emit_row "logs"        "log"      logs-manager
emit_row "memory"      "memory"   memory-hygiene memory-manager
emit_row "mcp"         "mcp"      mcp-doctor mcp-manager
emit_row "settings"    "setting"  update-config
emit_row "keybindings" "keybind"  keybindings-help
emit_row "secrets"     "secret"   key-manager
emit_row "files"       "file"     files-manager record-manager
emit_row "cost"        "cost"     finance-controller cost-manager

echo
echo "# END discovery. ABSENT rows = artifact types with no detected manager (candidate to build)."
