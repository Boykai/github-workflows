# Signal Messaging Integration

Bidirectional Signal messaging allows users to receive chat notifications on their phone and reply directly from Signal.

## How It Works

- **Backend** communicates with a `signal-cli-rest-api` sidecar via HTTP (send messages, generate QR codes) and WebSocket (receive inbound messages)
- **Frontend** talks only to the Backend — never directly to the Signal sidecar
- Phone numbers are **Fernet-encrypted at rest** in SQLite with **SHA-256 hashes** for lookup

## Setup

### 1. Environment Variables

The Signal sidecar is already configured in `docker-compose.yml`. Add your phone number to `.env`:

```env
SIGNAL_PHONE_NUMBER=+1234567890
```

### 2. Start Services

```bash
docker compose up -d
```

The `signal-api` container starts with a health check. The backend waits for it to become healthy.

### 3. Register the App's Signal Number

```bash
# Register the dedicated number
docker compose exec signal-api curl -s -X POST \
  "http://localhost:8080/v1/register/+1234567890"

# Verify with the SMS code you receive
docker compose exec signal-api curl -s -X POST \
  "http://localhost:8080/v1/register/+1234567890/verify/123456"
```

### 4. Link Your Signal Account

1. Open the app → **Settings** → **Signal Connection**
2. Click **Connect Signal** — a QR code appears
3. On your phone: **Signal → Settings → Linked Devices → "+" → Scan QR code**
4. Status updates to "Connected" with your masked phone number

### 5. Test

- **Outbound**: Send a message in app chat → receive on Signal within 30 seconds
- **Inbound**: Reply from Signal → message appears in app chat and AI responds
- **Project routing**: Prefix with `#project-name` to route to a specific project
- **Preferences**: Choose which messages to receive (All, Actions Only, Confirmations Only, None)
- **Disconnect**: Click Disconnect in Settings

## Features

- **Notification preferences**: All Messages, Action Proposals Only, System Confirmations Only, or None
- **Conflict detection**: If another account links the same phone number, the displaced user sees a dismissible banner
- **Retry with exponential backoff**: 4 attempts (30s → 8 min) for delivery failures
- **Styled formatting**: Emoji headers, deep links to issues/PRs
- **Media handling**: Unsupported media/attachment messages receive an auto-reply
- **Auto-routing**: Unlinked phone numbers receive an auto-reply directing them to the app

## Architecture

| Component | Role |
|-----------|------|
| `signal_bridge.py` | HTTP client to sidecar, DB helpers, WebSocket listener for inbound messages |
| `signal_delivery.py` | Outbound formatting, retry delivery with tenacity |
| `signal_chat.py` | Inbound message processing, routing to AI workflow |

The WebSocket listener starts at application boot and reconnects automatically.
