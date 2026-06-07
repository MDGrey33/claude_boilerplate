#!/usr/bin/env bash
# run_analysis.sh — full security analysis pipeline (no Claude needed)
#
# Usage:
#   ./run_analysis.sh                        # uses default_scope from config.json
#   ./run_analysis.sh --scope workspace      # write to <workspace>/artifacts/security-snapshot/
#   ./run_analysis.sh --scope <project>      # write to <workspace>/projects/<project>/artifacts/security-snapshot/
#
# Output lives under $REPORTS_DIR resolved from --scope.
# Equivalent to running /security-snapshot in Claude Code.
# Run monthly or on demand. Same-day re-runs overwrite; new day = new snapshot.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC} $*"; }
fail() { echo -e "${RED}✗${NC} $*" >&2; exit 1; }

# ── Locate workspace relative to this script (never from PWD — cwd drifts) ─────
# This script lives at <workspace>/.claude/skills/security-snapshot/scripts/.
WS="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
[ -f "$WS/.claude/.workspace" ] || fail "Workspace marker not found at $WS/.claude/.workspace — is this skill deployed inside a v2 workspace?"

# ── Resolve scope from config.json + optional --scope flag ─────────────────────
SCOPE="$(python3 -c "import json,sys; print(json.load(open('$SCRIPT_DIR/config.json'))['default_scope'])" 2>/dev/null)" \
  || fail "Cannot read default_scope from $SCRIPT_DIR/config.json — file missing, malformed JSON, or key absent. Run /security-snapshot first-run setup."
while [ $# -gt 0 ]; do
  case "$1" in
    --scope)    SCOPE="$2"; shift 2 ;;
    --scope=*)  SCOPE="${1#--scope=}"; shift ;;
    -h|--help)  sed -n '2,12p' "$0"; exit 0 ;;
    *)          fail "Unknown arg: $1" ;;
  esac
done

if [ "$SCOPE" = "workspace" ]; then
  REPORTS_DIR="$WS/artifacts/security-snapshot"
else
  if [ ! -d "$WS/projects/$SCOPE" ]; then
    cat >&2 <<EOF
✗ Project '$SCOPE' not found at $WS/projects/$SCOPE.

This usually means the skill's default_scope in scripts/config.json points at a
project that doesn't exist in this workspace. Two fixes, pick one:

  1. Edit $SCRIPT_DIR/config.json — set owner_project and default_scope to a
     project slug that exists in this workspace (see ls $WS/projects/).
  2. Pass --scope <name> at the CLI to override for a single run, or
     --scope workspace to write outputs at workspace level instead.
EOF
    exit 1
  fi
  REPORTS_DIR="$WS/projects/$SCOPE/artifacts/security-snapshot"
fi

mkdir -p "$REPORTS_DIR"
export SECURITY_SNAPSHOT_REPORTS_DIR="$REPORTS_DIR"

echo "Security Snapshot — $(date '+%Y-%m-%d')"
echo "========================================="
echo "Scope:       $SCOPE"
echo "Reports dir: $REPORTS_DIR"

# ── Prerequisites ──────────────────────────────────────────────────────────────
echo ""
echo "Checking prerequisites..."

python3 -c "import boto3" 2>/dev/null \
  || fail "boto3 not installed. Run: pip3 install boto3 --break-system-packages"
ok "boto3"

gh auth status --hostname github.com &>/dev/null \
  || fail "gh not authenticated. Run: gh auth login"
ok "gh CLI authenticated"

AWS_PROFILE_CFG="$(python3 -c "import json; print(json.load(open('$SCRIPT_DIR/config.json')).get('aws_profile',''))" 2>/dev/null)" \
  || fail "Cannot read aws_profile from $SCRIPT_DIR/config.json — file missing or malformed JSON."
[ -n "$AWS_PROFILE_CFG" ] \
  || fail "aws_profile not set in $SCRIPT_DIR/config.json — run /security-snapshot once for first-run setup, or edit the file."
aws sts get-caller-identity --profile "$AWS_PROFILE_CFG" &>/dev/null \
  || fail "AWS profile $AWS_PROFILE_CFG failed. Check credentials."
ok "AWS profile $AWS_PROFILE_CFG"

# ── Pipeline ───────────────────────────────────────────────────────────────────
echo ""
echo "→ Inspector V2 snapshot (~3 min)..."
python3 "$SCRIPT_DIR/posture_snapshot.py" --save --raw || fail "posture_snapshot.py failed"
ok "Inspector snapshot saved"

echo ""
echo "→ GitHub security snapshot (~2 min)..."
python3 "$SCRIPT_DIR/github_security_snapshot.py" --save --raw || fail "github_security_snapshot.py failed"
ok "GitHub snapshot saved"

echo ""
echo "→ Correlation analysis..."
python3 "$SCRIPT_DIR/correlation.py" --save --raw || fail "correlation.py failed"
ok "Correlation saved"

echo ""
echo "→ Building dashboard..."
python3 "$SCRIPT_DIR/build_dashboard.py" || fail "build_dashboard.py failed"
ok "Dashboard built"

# ── Done ───────────────────────────────────────────────────────────────────────
echo ""
echo "========================================="
ok "All steps complete."
echo "   Dashboard: $REPORTS_DIR/security-dashboard.html"
echo "   To deploy: /google-script-deploy deploy \"$REPORTS_DIR\""
