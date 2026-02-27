# Quickstart: Signal Messaging Integration

**Feature**: `011-signal-chat-integration`  
**Date**: 2026-02-27

## Prerequisites

- Docker and Docker Compose installed
- Existing backend and frontend running (see root `README.md`)
- A Signal account on a phone (for testing the QR code link)
- A phone number that can be registered with Signal (for the app's dedicated Signal number)

## 1. Add signal-cli-rest-api to Docker Compose

Add the Signal sidecar container to the existing `docker-compose.yml`:

```yaml
services:
  # ... existing backend and frontend services ...

  signal-api:
    image: bbernhard/signal-cli-rest-api:latest
    environment:
      - MODE=json-rpc
      - DEFAULT_SIGNAL_TEXT_MODE=styled
    volumes:
      - signal-cli-config:/home/.local/share/signal-cli
    ports:
      - "8080"  # Internal only — not exposed to host
    restart: unless-stopped

volumes:
  signal-cli-config:
```

## 2. Register the App's Signal Number

Before users can link, the app needs its own registered Signal number:

```bash
# Register (replace +1234567890 with your dedicated number)
curl -X POST "http://localhost:8080/v1/register/+1234567890"

# Complete verification with the SMS code received
curl -X POST "http://localhost:8080/v1/register/+1234567890/verify/123456"
```

## 3. Add Environment Variables

Add to the backend's `.env` file:

```env
# Signal integration
SIGNAL_API_URL=http://signal-api:8080
SIGNAL_PHONE_NUMBER=+1234567890
```

## 4. Run Database Migration

The migration `004_add_signal_tables.sql` runs automatically on backend startup. Tables created:
- `signal_connections` — user↔Signal link records
- `signal_messages` — delivery audit log
- `signal_conflict_banners` — conflict notification banners

## 5. Verify the Integration

1. Start all services: `docker compose up -d`
2. Open the app in your browser
3. Navigate to **Settings** → **Signal Connection** section
4. Click **Connect Signal** — a QR code appears
5. On your phone: **Signal → Settings → Linked Devices → "+" → Scan QR code**
6. The Settings view should update to show "Connected" status
7. Send a message in the app's chat — it should arrive on your Signal
8. Reply from Signal — the message should appear in the app's chat

## Key Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/v1/signal/connection` | Get connection status |
| `POST` | `/api/v1/signal/connection/link` | Generate QR code for linking |
| `GET` | `/api/v1/signal/connection/link/status` | Poll link completion status |
| `DELETE` | `/api/v1/signal/connection` | Disconnect Signal |
| `GET` | `/api/v1/signal/preferences` | Get notification preferences |
| `PUT` | `/api/v1/signal/preferences` | Update notification preferences |
| `GET` | `/api/v1/signal/banners` | Get active conflict banners |
| `POST` | `/api/v1/signal/banners/{id}/dismiss` | Dismiss a banner |

## Architecture Overview

```
┌─────────────┐    HTTP/WS     ┌──────────────────┐    Signal
│   Backend   │ ◄────────────► │ signal-cli-rest-  │ ◄──────► Signal servers
│  (FastAPI)  │                │ api (sidecar)     │
└──────┬──────┘                └──────────────────┘
       │
       │ REST API
       ▼
┌─────────────┐
│  Frontend   │
│  (React)    │
└─────────────┘
```

- **Backend** communicates with `signal-api` via HTTP (send messages, generate QR codes) and WebSocket (receive inbound messages).
- **Frontend** only talks to the Backend — never directly to the Signal sidecar.
- Phone numbers are Fernet-encrypted at rest in SQLite, with SHA-256 hashes for lookup.
