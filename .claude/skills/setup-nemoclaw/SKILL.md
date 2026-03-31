---
name: setup-nemoclaw
description: Install and configure NVIDIA NemoClaw (secure agent runtime) with OpenClaw + Anthropic inference + Telegram bridge
user_invocable: true
args: Optional provider (anthropic, openai, ollama, nvidia). Defaults to anthropic.
---

# Setup NemoClaw — Install & Configure Secure Agent Runtime

You are installing NVIDIA NemoClaw on this machine. NemoClaw is an open-source (Apache 2.0) reference stack that runs OpenClaw agents inside sandboxed environments with kernel-level isolation.

**Critical**: Every output must be verified before presenting to the user. Never claim something works without proof (Playwright for URLs, real commands for CLIs, real requests for APIs).

## Prerequisites

| Requirement | Minimum |
|------------|---------|
| Node.js | 22.16+ |
| npm | 10+ |
| Docker | Running (Docker Desktop on macOS) |
| RAM | 8 GB+ |
| Disk | 20 GB free |

## Steps

### 1. Check Environment

Run these in parallel:
```bash
node --version          # Need 22.16+
npm --version           # Need 10+
docker --version
docker info --format '{{.ServerVersion}}' 2>/dev/null || echo "docker-not-running"
```

**If Node.js < 22.16**: Upgrade via nvm:
```bash
source ~/.zshrc; nvm install 22; nvm use 22
```

**If Docker not running**: Start Docker Desktop:
```bash
open -a Docker
# Wait for it to be ready, then verify:
docker info --format '{{.ServerVersion}}'
```

### 2. Locate Anthropic API Key

Search for a funded Anthropic API key:
```bash
grep -ril "ANTHROPIC_API_KEY\|sk-ant" ~/.credentials/ 2>/dev/null
```

Verify the key has credits by checking its prefix (`sk-ant-api03-...`) and testing:
```bash
source <env-file-with-key>
curl -s -X POST https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-sonnet-4-6","max_tokens":5,"messages":[{"role":"user","content":"hi"}]}' \
  | head -c 200
```

If the key returns a credit error, ask the user to top up at console.anthropic.com before proceeding.

### 3. Install NemoClaw CLI

```bash
source ~/.zshrc; nvm use 22
curl -fsSL https://www.nvidia.com/nemoclaw.sh | bash 2>&1
```

**Expected**: This installs the CLI and starts an interactive onboarding wizard. The wizard WILL FAIL in a non-TTY environment (Claude Code) with:
```
[ERROR] Interactive onboarding requires a TTY.
```

This is normal — the CLI itself is installed. Verify:
```bash
source ~/.zshrc; nvm use 22; nemoclaw --version
# Expected: nemoclaw v0.1.0
```

### 4. Patch Anthropic Provider for Skip-Verify

**Known issue**: The onboarding's `openshell inference set` verification fails because the openshell pod inside k3s can't reach `api.anthropic.com` during the verify step (DNS routing issue inside Docker Desktop k3s). The workaround is to add `skipVerify: true` to the Anthropic provider config.

Edit `~/.nemoclaw/source/bin/lib/onboard.js`:

Find the `anthropic` entry in `REMOTE_PROVIDER_CONFIG` (around line 84) and add `skipVerify: true`:

```javascript
anthropic: {
    label: "Anthropic",
    providerName: "anthropic-prod",
    providerType: "anthropic",
    credentialEnv: "ANTHROPIC_API_KEY",
    endpointUrl: ANTHROPIC_ENDPOINT_URL,
    helpUrl: "https://console.anthropic.com/settings/keys",
    modelMode: "curated",
    defaultModel: "claude-sonnet-4-6",
    skipVerify: true,   // <-- ADD THIS LINE
},
```

**Why**: OpenAI and Gemini providers already have this flag. Anthropic doesn't because the NemoClaw team expects NVIDIA GPU setups where k3s DNS works natively. On Docker Desktop (macOS), the k3s CoreDNS can't resolve external domains until patched.

### 5. Run Non-Interactive Onboarding

```bash
source ~/.zshrc; nvm use 22
source <env-file-with-anthropic-key>
export ANTHROPIC_API_KEY
export NEMOCLAW_NON_INTERACTIVE=1
export NEMOCLAW_SANDBOX_NAME="cos-agent"
export NEMOCLAW_PROVIDER="anthropic"
nemoclaw onboard --non-interactive 2>&1
```

**Gotcha**: `NEMOCLAW_PROVIDER` must be `"anthropic"` (the provider *type*), NOT `"anthropic-prod"` (the provider *name* used by OpenShell). Using the wrong value gives: `Unsupported NEMOCLAW_PROVIDER: anthropic-prod`.

**Expected stages**:
1. `[1/7] Preflight checks` — Docker, openshell CLI install
2. `[2/7] Starting OpenShell gateway` — Pulls ~2.4GB gateway image, starts k3s
3. `[3/7] Configuring inference` — Selects Anthropic provider
4. `[4/7] Setting up inference provider` — Creates provider, sets route (skips verify)
5. `[5/7] Creating sandbox` — Builds custom Dockerfile (~3-5 min first time), pushes ~1.3GB image
6. `[6/7] Setting up OpenClaw` — Configures agents inside sandbox
7. `[7/7] Policy presets` — Applies network policies

**Known failure at step 7**: If a global policy was previously set, step 7 fails with:
```
policy is managed globally; delete global policy before sandbox policy update
```
Fix: `openshell policy delete --global --yes` then re-run onboarding with `--resume`.

### 6. Fix CoreDNS (Docker Desktop / macOS)

**Known issue**: The onboarding patches CoreDNS to forward to the host's DNS, but on macOS it may pick an unreachable IPv6 address. Verify:

```bash
source ~/.zshrc; nvm use 22
openshell doctor exec -- kubectl -n kube-system get configmap coredns -o yaml | grep "forward ."
```

If it shows an IPv6 address (like `forward . 2a03:...`), patch it:

```bash
openshell doctor exec -- sh -c \
  "kubectl -n kube-system get configmap coredns -o json | \
   sed 's|forward \. [^ ]*|forward . 192.168.65.7 8.8.8.8|' | \
   kubectl apply -f -"
openshell doctor exec -- kubectl -n kube-system rollout restart deployment coredns
```

Wait 15 seconds, then verify DNS works from the openshell pod:
```bash
openshell doctor exec -- kubectl -n openshell exec openshell-0 -- \
  sh -c "echo | timeout 5 openssl s_client -connect api.anthropic.com:443 2>&1 | head -3"
```
**Expected**: Shows `depth=2 ... GTS Root R4` (TLS handshake success).

**Note**: `192.168.65.7` is Docker Desktop's host DNS resolver. Confirm it's correct for your setup:
```bash
openshell doctor exec -- cat /etc/resolv.conf | grep ExtServers
```

### 7. Verify Sandbox is Running Properly

```bash
nemoclaw cos-agent status
openshell sandbox list
```

Check that the OpenClaw gateway process is running inside the sandbox:
```bash
openshell doctor exec -- kubectl -n openshell exec cos-agent -- \
  bash -c "ls /proc/*/cmdline 2>/dev/null | while read f; do \
    echo -n \"\$(basename \$(dirname \$f)): \"; \
    cat \$f 2>/dev/null | tr '\0' ' '; echo; \
  done" | grep -E "openclaw|gateway|node"
```

**Expected**: Should show `openclaw gateway run` or `node` processes. If you only see `sleep infinity`, the sandbox was created wrong — see Troubleshooting.

### 8. Verify Inference Works

Test the inference routing from inside the sandbox:
```bash
openshell doctor exec -- kubectl -n openshell exec cos-agent -- \
  bash -c "export https_proxy=http://10.200.0.1:3128; \
  curl -k -s --max-time 30 -X POST https://inference.local/v1/messages \
  -H 'anthropic-version: 2023-06-01' \
  -H 'content-type: application/json' \
  -d '{\"model\":\"claude-sonnet-4-6\",\"max_tokens\":20,\"messages\":[{\"role\":\"user\",\"content\":\"Say ok\"}]}'"
```

**Expected**: JSON response with `"text":"Ok"` or similar. If you get `"inference service unavailable"`, the provider isn't attached — see Troubleshooting.

### 9. Verify Agent Responds

```bash
openshell doctor exec -- kubectl -n openshell exec cos-agent -- \
  bash -c "su - sandbox -c 'source ~/.bashrc 2>/dev/null; \
  export https_proxy=http://10.200.0.1:3128; \
  export http_proxy=http://10.200.0.1:3128; \
  export NODE_EXTRA_CA_CERTS=/etc/openshell-tls/ca-bundle.pem; \
  openclaw agent --agent main --local \
  -m \"Confirm operational in one sentence.\" \
  --session-id verify-install' 2>&1"
```

**Expected**: A one-sentence response from Claude. Retry transient 529 errors are normal.

### 10. Verify Dashboard (MANDATORY)

Set up port forwarding:
```bash
openshell forward start 18789 cos-agent --background
```

**You MUST verify the dashboard with Playwright** (never trust port-forward output alone):

```javascript
// Save as /tmp/verify-dashboard.js and run: node /tmp/verify-dashboard.js
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const TOKEN = '<paste-token-here>';
  await page.goto(`http://127.0.0.1:18789/#token=${TOKEN}`, { waitUntil: 'networkidle', timeout: 15000 });
  const title = await page.title();
  const health = await page.textContent('.health-indicator, [class*=health], [data-testid*=health]').catch(() => 'not found');
  await page.screenshot({ path: '/tmp/nemoclaw-dashboard-verified.png' });
  console.log(`Title: ${title}`);
  console.log(`Health: ${health}`);
  console.log(`Screenshot saved`);
  await browser.close();
})();
```

Get the auth token:
```bash
openshell doctor exec -- kubectl -n openshell exec cos-agent -- \
  bash -c "su - sandbox -c \"python3 -c \\\"import json; \
  print(json.load(open('/sandbox/.openclaw/openclaw.json')).get('gateway',{}).get('auth',{}).get('token',''))\\\"\" 2>/dev/null"
```

**Expected**: Screenshot shows "OpenClaw Control" dashboard with Health: OK and a chat input.

### 11. Create Telegram Bot

Create a bot via @BotFather on Telegram mobile:

1. Open Telegram → search **@BotFather** → tap **Start**
2. Send `/newbot`
3. Send a display name (e.g. `NemoClaw COS Agent`)
4. Send a username ending in `bot` (e.g. `nemoclaw_cos_bot`)
5. Copy the **token** BotFather returns (format: `123456789:ABCdef...`)
6. Open **@userinfobot** → tap Start → note your **Id** number (your chat ID)

**Why not automate this?** Telegram Web has a rendering bug in Playwright persistent contexts — BotFather chat content fails to load. Mobile is the reliable path (30 seconds).

### 12. Store Telegram Credentials

```bash
cat > ~/.credentials/telegram_bot.env << 'EOF'
TELEGRAM_BOT_TOKEN=<paste-token-here>
ALLOWED_CHAT_IDS=<your-chat-id>
EOF
chmod 600 ~/.credentials/telegram_bot.env
```

Verify the token:
```bash
curl -s "https://api.telegram.org/bot<TOKEN>/getMe" | head -c 200
```
**Expected**: `{"ok":true,"result":{"id":...,"is_bot":true,"username":"...Bot"}}`.

### 13. Configure Network Policy for Telegram

The sandbox policy must allow access to `api.telegram.org:443`. If using the custom policy from this guide, the `telegram` section is already included:

```yaml
telegram:
  name: telegram
  endpoints:
    - host: api.telegram.org
      port: 443
      protocol: rest
      enforcement: enforce
      tls: terminate
      rules:
        - allow: { method: GET, path: "/bot*/**" }
        - allow: { method: POST, path: "/bot*/**" }
  binaries:
    - { path: /usr/local/bin/node }
```

If not already in your policy, add it and re-apply:
```bash
openshell policy set cos-agent --policy ~/workspace/nemoclaw/cos-agent-policy.yaml
```

### 14. Start the Telegram Bridge

The bridge runs on the **host** (not inside the sandbox). It polls Telegram for messages, SSHes into the sandbox to run the OpenClaw agent, and sends responses back.

```bash
source ~/.zshrc; nvm use 22
source ~/.credentials/telegram_bot.env
source <env-file-with-anthropic-key>
export TELEGRAM_BOT_TOKEN ALLOWED_CHAT_IDS
export NVIDIA_API_KEY="$ANTHROPIC_API_KEY"
export SANDBOX_NAME="cos-agent"
node ~/.nemoclaw/source/scripts/telegram-bridge.js 2>&1
```

**Gotcha**: The bridge requires `NVIDIA_API_KEY` even for Anthropic setups — it passes it to the sandbox env via SSH. Since inference goes through the OpenShell proxy (which injects the real key server-side), set `NVIDIA_API_KEY` to your `ANTHROPIC_API_KEY`. Any non-empty value works; the proxy handles the actual authentication.

**Expected**: Banner shows `NemoClaw Telegram Bridge` with bot username and sandbox name, then begins polling.

To run in background with logging:
```bash
node ~/.nemoclaw/source/scripts/telegram-bridge.js > /tmp/telegram-bridge.log 2>&1 &
echo $! > /tmp/telegram-bridge.pid
```

### 15. Verify Telegram End-to-End (MANDATORY)

Send a test message to the bot on Telegram (e.g. "Hello, are you working?").

Check the bridge logs:
```bash
tail -20 /tmp/telegram-bridge.log
```

**Expected**: Logs show:
```
[<chat-id>] <name>: Hello, are you working?
[<chat-id>] agent: <response from Claude>...
```

Verify bot can send messages via API:
```bash
source ~/.credentials/telegram_bot.env
curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -H "Content-Type: application/json" \
  -d "{\"chat_id\": ${ALLOWED_CHAT_IDS}, \"text\": \"Bridge connectivity test.\"}"
```

**Expected**: You receive the test message on Telegram AND the agent response to your test message.

## Troubleshooting

### Sandbox shows only `sleep infinity` (no gateway running)

The sandbox MUST be created with the `nemoclaw-start` entrypoint. If onboarding created it correctly, this is handled. If recreating manually:

```bash
openshell sandbox delete cos-agent
openshell sandbox create --name cos-agent \
  --from openshell/sandbox-from:<BUILD_TAG> \
  --provider anthropic-prod \
  --policy ~/workspace/nemoclaw/cos-agent-policy.yaml \
  --no-tty \
  -- env CHAT_UI_URL=http://127.0.0.1:18789 nemoclaw-start
```

**The `-- env ... nemoclaw-start` part is critical.** Without it, the sandbox defaults to `sleep infinity` and nothing starts.

Find the build tag:
```bash
openshell doctor exec -- kubectl -n openshell get pods -o jsonpath='{.items[*].spec.containers[*].image}' | tr ' ' '\n' | grep sandbox-from
```

### `"inference service unavailable"` from inference.local

The provider isn't attached to the sandbox. Check:
```bash
openshell doctor exec -- kubectl -n openshell logs openshell-0 --tail=20 | grep ProviderEnvironment
```

If `provider_count=0`: the sandbox was created without `--provider anthropic-prod`. Recreate it with that flag.

### Policy stuck in "Pending"

Policies take 10-15 seconds to load. Check:
```bash
openshell policy get cos-agent
```

If still pending after 30s, try re-applying:
```bash
openshell policy set cos-agent --policy ~/workspace/nemoclaw/cos-agent-policy.yaml
```

### `"policy is managed globally"` error

A global policy blocks per-sandbox policy updates:
```bash
openshell policy delete --global --yes
```

### HTTP 403 from proxy — binary not allowed

The default NemoClaw policy only allows `/usr/local/bin/claude` to access `api.anthropic.com`. If the OpenClaw agent uses `node` or `openclaw` (which it does), inference calls get 403'd by the proxy.

**Fix**: Create a custom policy that adds the required binaries:

```yaml
# In the network_policies section for api.anthropic.com, add:
binaries:
  - /usr/local/bin/claude
  - /usr/local/bin/openclaw
  - /usr/local/bin/node
  - /usr/bin/curl
```

Apply it:
```bash
openshell policy set cos-agent --policy ~/workspace/nemoclaw/cos-agent-policy.yaml
```

### CoreDNS returns SERVFAIL

DNS inside k3s is broken. See Step 6 above to patch CoreDNS.

### Telegram bridge starts but bot doesn't respond

Check the bridge logs:
```bash
tail -30 /tmp/telegram-bridge.log
```

Common causes:
- **`NVIDIA_API_KEY required`**: Set `NVIDIA_API_KEY` to your `ANTHROPIC_API_KEY` (the bridge requires it non-empty, but the proxy handles actual auth)
- **`openshell not found`**: Ensure `openshell` is on PATH (`source ~/.zshrc; nvm use 22`)
- **SSH fails**: The sandbox must be in `Ready` phase (`openshell sandbox list`)
- **No response in logs**: The bridge consumed the update but the agent timed out (120s default). Check sandbox inference with Step 8.

### Telegram bridge stops when terminal closes

The bridge runs as a foreground Node.js process. For persistence, create a LaunchAgent:
```bash
cat > ~/Library/LaunchAgents/com.nemoclaw.telegram-bridge.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.nemoclaw.telegram-bridge</string>
  <key>ProgramArguments</key><array>
    <string>/Users/YOU/.nvm/versions/node/v22.22.2/bin/node</string>
    <string>/Users/YOU/.nemoclaw/source/scripts/telegram-bridge.js</string>
  </array>
  <key>EnvironmentVariables</key><dict>
    <key>TELEGRAM_BOT_TOKEN</key><string>YOUR_TOKEN</string>
    <key>ALLOWED_CHAT_IDS</key><string>YOUR_CHAT_ID</string>
    <key>NVIDIA_API_KEY</key><string>YOUR_ANTHROPIC_KEY</string>
    <key>SANDBOX_NAME</key><string>cos-agent</string>
    <key>PATH</key><string>/usr/local/bin:/usr/bin:/bin:/Users/YOU/.nvm/versions/node/v22.22.2/bin</string>
  </dict>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>/tmp/telegram-bridge.log</string>
  <key>StandardErrorPath</key><string>/tmp/telegram-bridge.log</string>
</dict></plist>
EOF
launchctl load ~/Library/LaunchAgents/com.nemoclaw.telegram-bridge.plist
```

### Telegram bot automation via Playwright fails

**Known issue**: Telegram Web (both A and K versions) has a rendering bug in Playwright persistent contexts — BotFather chat content fails to load (blank chat area, "Text not allowed"). Create bots via Telegram mobile app instead.

### Agent uses wrong model (claude-opus instead of claude-sonnet)

The OpenClaw agent's model is configured in `/sandbox/.openclaw/openclaw.json` inside the sandbox, not the gateway inference route. The NemoClaw Dockerfile patches this at build time. If the model is wrong, rebuild via `nemoclaw onboard`.

## Key Paths

| Path | Purpose |
|------|---------|
| `~/.nemoclaw/` | Config, credentials, source code |
| `~/.nemoclaw/source/` | NemoClaw CLI source (cloned from GitHub) |
| `~/.nemoclaw/onboard-session.json` | Onboarding state (resume from here) |
| `~/.nemoclaw/source/bin/lib/onboard.js` | Onboarding logic (patched for skipVerify) |
| `~/.nemoclaw/source/nemoclaw-blueprint/policies/` | Default + preset network policies |
| `~/workspace/nemoclaw/` | Workshop docs, custom policy, screenshots |
| `~/workspace/nemoclaw/cos-agent-policy.yaml` | Custom policy with expanded binary access |
| `~/.credentials/telegram_bot.env` | Telegram bot token + allowed chat IDs |
| `~/.nemoclaw/source/scripts/telegram-bridge.js` | Telegram ↔ sandbox bridge (runs on host) |
| `/tmp/telegram-bridge.log` | Bridge runtime logs |
| `/tmp/telegram-bridge.pid` | Bridge process ID |

## Architecture

```
Host (macOS)
├── NemoClaw CLI (nemoclaw v0.1.0, Node 22+)
├── Docker Desktop
│   └── k3s cluster (openshell-cluster-nemoclaw)
│       ├── CoreDNS (patched to forward → 192.168.65.7 + 8.8.8.8)
│       ├── openshell-0 (gateway server)
│       │   ├── gRPC API (sandbox management)
│       │   ├── HTTP proxy (10.200.0.1:3128, enforces network policies)
│       │   └── Inference router (inference.local → api.anthropic.com)
│       └── cos-agent (sandbox pod)
│           ├── nemoclaw-start (entrypoint, sets up proxy env vars)
│           ├── OpenClaw gateway (serves dashboard on port 18789)
│           ├── OpenClaw agent (claude-sonnet-4-6 via inference.local)
│           └── auto-pair watcher (approves dashboard device connections)
├── Telegram Bridge (telegram-bridge.js, runs on host)
│   ├── Polls api.telegram.org for messages (long-polling)
│   ├── SSHes into sandbox via openshell ssh-config
│   ├── Runs: openclaw agent --agent main --local -m <message>
│   └── Sends agent response back to Telegram
└── Port forwards
    ├── 8080 → OpenShell gateway (mTLS, managed by openshell CLI)
    └── 18789 → cos-agent dashboard (HTTP, user-facing)
```

## Network Flow for Inference

```
1. Agent calls https://inference.local/v1/messages
2. https_proxy (http://10.200.0.1:3128) intercepts
3. Proxy CONNECT tunnel → openshell-0 pod
4. OpenShell server checks policy (binary + endpoint rules)
5. OpenShell server injects stored ANTHROPIC_API_KEY
6. OpenShell server forwards to https://api.anthropic.com/v1/messages
7. Response flows back through tunnel to agent
```

The sandbox never sees the raw API key — it's injected server-side by the gateway.

## Network Flow for Telegram

```
1. User sends message to @Bot on Telegram
2. telegram-bridge.js polls api.telegram.org/getUpdates (from host)
3. Bridge checks ALLOWED_CHAT_IDS, rejects unauthorized chats
4. Bridge SSHes into sandbox via openshell ssh-config
5. Runs: openclaw agent --agent main --local -m <message>
6. Agent calls inference.local → proxy → api.anthropic.com (same as above)
7. Agent response captured via SSH stdout
8. Bridge sends response to api.telegram.org/sendMessage
9. User receives response on Telegram
```

The bridge never runs inside the sandbox — it runs on the host and uses SSH for isolation.
