---
name: setup-voice
description: Install a local neural voice interface for Claude Code on macOS Apple Silicon. Wires mlx-whisper (STT) + Kokoro TTS (offline neural voices) into voice-claude and vtranscribe CLI scripts. Two voice contexts — personal (af_heart) and tech (af_bella). No cloud APIs, no API keys.
user_invocable: true
---

# Setup Voice — Local Neural Voice Interface (macOS Apple Silicon)

Installs a fully local voice pipeline:

- **STT:** `mlx-whisper` — OpenAI Whisper on Apple MLX, Metal-accelerated
- **TTS:** `kokoro-onnx` — Kokoro 82M neural TTS, offline, two context voices
- **Recording:** `sox` (`rec`) — microphone capture with silence detection
- **Scripts:** `voice-claude`, `vtranscribe`, `kokoro-say` in `~/bin/`

---

## Prerequisites

- macOS on Apple Silicon (M1 or later)
- Homebrew (`brew`)
- `uv` — `brew install uv`
- Python 3.12 — `brew install python@3.12`
- `ffmpeg` — `brew install ffmpeg`
- `~/bin/` exists and is on `$PATH`
- `claude` CLI installed and authenticated

---

## Step 1 — Install system dependencies

```bash
brew install sox ffmpeg
```

`sox` provides the `rec` command for microphone capture. `ffmpeg` is required by mlx-whisper for audio conversion.

---

## Step 2 — Install mlx-whisper (STT)

```bash
uv tool install --python 3.12 mlx-whisper
```

Installs `mlx_whisper` CLI globally via uv. Uses Apple MLX for Metal-accelerated transcription.

**Verify:**

```bash
mlx_whisper --help
```

Model (`mlx-community/whisper-turbo`) downloads automatically on first transcription (~1.5 GB, one-time).

---

## Step 3 — Install Kokoro TTS (offline neural voices)

```bash
uv venv --python 3.12 ~/.local/share/kokoro-venv
~/.local/share/kokoro-venv/bin/python -m ensurepip
~/.local/share/kokoro-venv/bin/python -m pip install kokoro-onnx soundfile
```

Download model files (~337 MB total, one-time):

```bash
mkdir -p ~/.cache/kokoro
curl -L -o ~/.cache/kokoro/kokoro-v1.0.onnx \
  "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
curl -L -o ~/.cache/kokoro/voices-v1.0.bin \
  "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"
```

---

## Step 4 — Create `kokoro-say`

Create `~/bin/kokoro-say` with the content below, then `chmod +x ~/bin/kokoro-say`.

```
#!/usr/bin/env bash
# Speak text using Kokoro TTS (local neural, no internet).
# Usage: kokoro-say [-v VOICE] "text"
#   Voices: af_heart (personal/default)  af_bella (tech)
#           af_sky  bf_emma  bf_isabella  am_adam  am_michael
set -euo pipefail

VOICE="${KOKORO_VOICE:-af_heart}"
while getopts ":v:h" opt; do
  case "$opt" in
    v) VOICE="$OPTARG" ;;
    h) printf 'Usage: kokoro-say [-v voice] "text"\n'; exit 0 ;;
    :) printf 'Option -%s requires an argument.\n' "$OPTARG" >&2; exit 1 ;;
    *) printf 'Unknown option: -%s\n' "$OPTARG" >&2; exit 1 ;;
  esac
done
shift $((OPTIND - 1))

TEXT="${*}"
if [[ -z "$TEXT" ]]; then
  read -r -d '' TEXT || true
fi

TMP=$(mktemp /tmp/kokoro.XXXXXX.wav)
trap 'rm -f "$TMP"' EXIT

~/.local/share/kokoro-venv/bin/python - "$VOICE" "$TEXT" "$TMP" << 'PYEOF'
import sys, warnings
warnings.filterwarnings("ignore")
import soundfile as sf
from kokoro_onnx import Kokoro

voice, text, outfile = sys.argv[1], sys.argv[2], sys.argv[3]
import os
cache = os.path.expanduser("~/.cache/kokoro")
kokoro = Kokoro(f"{cache}/kokoro-v1.0.onnx", f"{cache}/voices-v1.0.bin")
samples, sr = kokoro.create(text, voice=voice, speed=1.0, lang="en-us")
sf.write(outfile, samples, sr)
PYEOF

afplay "$TMP"
```

**Verify:**

```bash
kokoro-say "Hello, voice interface ready."
```

---

## Step 5 — Create `vtranscribe`

Create `~/bin/vtranscribe` with the content below, then `chmod +x ~/bin/vtranscribe`.

```
#!/usr/bin/env bash
# Record from mic until silence, print transcript to stdout.
# Env override: WHISPER_MODEL (default: mlx-community/whisper-turbo)
set -euo pipefail

MODEL="${WHISPER_MODEL:-mlx-community/whisper-turbo}"
TMP=$(mktemp -d /tmp/vtranscribe.XXXXXX)
trap 'rm -rf "$TMP"' EXIT

printf '🎤 Listening... (stop speaking to send)\n' >&2
rec -r 16000 -c 1 -b 16 "$TMP/audio.wav" \
  silence 1 0.1 3% 1 1.5 3% 2>/dev/null

SIZE=$(wc -c < "$TMP/audio.wav")
if (( SIZE < 10000 )); then
  printf '⚠️  No audio detected.\n' >&2
  exit 1
fi

printf '📝 Transcribing...\n' >&2
mlx_whisper "$TMP/audio.wav" \
  --model "$MODEL" \
  --output-format txt \
  --output-dir "$TMP" \
  --output-name transcript \
  2>/dev/null

tr -d '\n' < "$TMP/transcript.txt" | xargs
```

**Verify:**

```bash
vtranscribe   # speak a sentence, check output
```

---

## Step 6 — Create `voice-claude`

Create `~/bin/voice-claude` with the content below, then `chmod +x ~/bin/voice-claude`.

```
#!/usr/bin/env bash
# Voice interface for Claude Code.
# Usage: voice-claude [-l] [-c CONTEXT] [-m MODEL]
#   -l  loop mode (Ctrl-C to exit)
#   -c  context: personal (default) | tech
#       personal → af_heart  (warm, everyday)
#       tech     → af_bella  (clear, technical)
#   -m  Whisper model (env: VC_MODEL)
set -euo pipefail

MODEL="${VC_MODEL:-mlx-community/whisper-turbo}"
CONTEXT="${VC_CONTEXT:-personal}"
LOOP=false
SAY_PID=""

declare -A VOICE_MAP
VOICE_MAP[personal]="af_heart"
VOICE_MAP[tech]="af_bella"

while getopts ":lc:m:h" opt; do
  case "$opt" in
    l) LOOP=true ;;
    c) CONTEXT="$OPTARG" ;;
    m) MODEL="$OPTARG" ;;
    h) printf 'Usage: voice-claude [-l] [-c personal|tech] [-m model]\n'; exit 0 ;;
    :) printf 'Option -%s requires an argument.\n' "$OPTARG" >&2; exit 1 ;;
    *) printf 'Unknown option: -%s\n' "$OPTARG" >&2; exit 1 ;;
  esac
done

speak() {
  local voice="${VOICE_MAP[$CONTEXT]:-af_heart}"
  kokoro-say -v "$voice" "$1" 2>/dev/null &
  SAY_PID=$!
}

cleanup() {
  [[ -n "$SAY_PID" ]] && kill "$SAY_PID" 2>/dev/null || true
  printf '\nBye.\n'
  exit 0
}
trap cleanup INT TERM

detect_context_switch() {
  local p
  p=$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')
  if echo "$p" | grep -qE "switch to tech|coding mode|tech mode"; then
    [[ "$CONTEXT" != "tech" ]] && { CONTEXT="tech"; printf '  [switching to Bella]\n'; }
  elif echo "$p" | grep -qE "switch to personal|personal mode"; then
    [[ "$CONTEXT" != "personal" ]] && { CONTEXT="personal"; printf '  [switching to Heart]\n'; }
  fi
}

one_turn() {
  [[ -n "$SAY_PID" ]] && kill "$SAY_PID" 2>/dev/null || true
  SAY_PID=""

  local TMP
  TMP=$(mktemp -d /tmp/vc.XXXXXX)

  printf '\n🎤 Listening... (stop speaking to send)\n'
  rec -r 16000 -c 1 -b 16 "$TMP/audio.wav" \
    silence 1 0.1 3% 1 1.5 3% 2>/dev/null

  local SIZE
  SIZE=$(wc -c < "$TMP/audio.wav")
  if (( SIZE < 10000 )); then
    printf '⚠️  No audio detected, try again.\n'
    rm -rf "$TMP"
    return 0
  fi

  printf '📝 Transcribing...\n'
  mlx_whisper "$TMP/audio.wav" \
    --model "$MODEL" \
    --output-format txt \
    --output-dir "$TMP" \
    --output-name transcript \
    2>/dev/null

  local PROMPT
  PROMPT=$(tr -d '\n' < "$TMP/transcript.txt" | xargs)
  rm -rf "$TMP"

  if [[ -z "$PROMPT" ]]; then
    printf '⚠️  Nothing heard, try again.\n'
    return 0
  fi

  detect_context_switch "$PROMPT"

  printf '\nYou: %s\n\n' "$PROMPT"
  printf '🤖 ...\n'

  local RESPONSE
  RESPONSE=$(claude -p "$PROMPT" 2>/dev/null)

  printf '\nClaude [%s]: %s\n' "$CONTEXT" "$RESPONSE"
  speak "$RESPONSE"
}

if $LOOP; then
  printf 'Voice loop active — Ctrl-C to exit.\n'
  printf 'Context: %s (%s)\n\n' "$CONTEXT" "${VOICE_MAP[$CONTEXT]}"
  while true; do
    one_turn
  done
else
  one_turn
  [[ -n "$SAY_PID" ]] && wait "$SAY_PID" 2>/dev/null || true
fi
```

---

## Voices reference

| Voice | ID | Character |
|---|---|---|
| Heart | `af_heart` | Warm, natural — everyday conversations |
| Bella | `af_bella` | Clear, precise — technical/coding sessions |
| Sky | `af_sky` | Bright, energetic — alternative option |
| Emma | `bf_emma` | British female |
| Isabella | `bf_isabella` | British female, warmer |
| Adam | `am_adam` | American male |
| Michael | `am_michael` | American male, deeper |

---

## Usage

| Command | What it does |
|---|---|
| `voice-claude` | Single voice turn, personal context |
| `voice-claude -l` | Continuous loop, Ctrl-C to exit |
| `voice-claude -c tech` | Loop or single turn in tech context |
| `voice-claude -c tech -l` | Loop in tech context |
| `vtranscribe` | Record and print transcript only |

**Mid-loop context switching** — just say it:

- "switch to tech" or "coding mode" → Bella
- "switch to personal" or "personal mode" → Heart

**Within a Claude Code session:**

```
! vtranscribe
```

Runs `vtranscribe` inline so the transcript lands directly in the conversation.

---

## Environment variables

| Variable | Default | Effect |
|---|---|---|
| `VC_CONTEXT` | `personal` | Starting context |
| `VC_MODEL` | `mlx-community/whisper-turbo` | Whisper model |
| `WHISPER_MODEL` | `mlx-community/whisper-turbo` | For `vtranscribe` |
| `KOKORO_VOICE` | `af_heart` | For `kokoro-say` direct calls |

---

## Troubleshooting

**No audio detected** — sox mic permission: System Settings → Privacy & Security → Microphone → enable Terminal / your shell.

**mlx_whisper not found** — run `uv tool update mlx-whisper` or check `~/.local/bin` is on `$PATH`.

**Kokoro model missing** — re-run the `curl` downloads in Step 3; check `~/.cache/kokoro/` contains both files.

**`rec` not found** — `brew install sox` (sox provides `rec`).

**First transcription is slow** — the Whisper model downloads (~1.5 GB) on first run. Subsequent runs are fast.
