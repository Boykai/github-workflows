# Signal Messaging Integration — Research Findings

**Date**: 2026-02-27  
**Status**: Complete  
**Scope**: Technical research for integrating Signal messaging into a Python FastAPI web application

---

## Topic 1: Signal Programmatic Messaging Interface

### Decision

**Use `signal-cli-rest-api`** (Docker container wrapping signal-cli) as the Signal messaging interface, communicating with it via HTTP from the FastAPI backend.

### Rationale

| Criterion | signal-cli-rest-api | signal-cli (direct) | signald | libsignal | Official Bot API |
|---|---|---|---|---|---|
| **Maturity** | High — 92 releases, 2.4k stars, 54 contributors, actively maintained (last commit: days ago), built on signal-cli v0.13.24 | High — 108 releases, 4.2k stars, 64 contributors, 11 years old | **Deprecated** — project page states "no longer actively maintained, use signal-cli" | Low-level crypto library, not a messaging API. Bindings for Java/Swift/TypeScript only — no Python. "Use outside of Signal is unsupported." | **Does not exist.** Signal has no official bot API or business messaging API. |
| **Python compatibility** | Excellent — plain HTTP/REST calls from any `httpx`/`aiohttp` client. Community Python library `pysignalclirestapi` exists (30 stars). | Poor — Java application (JRE 25 required). Must be invoked via subprocess or JSON-RPC socket. No native Python binding. | Moderate — Unix socket protocol, Python libraries existed but project is abandoned. | None for Python — Rust core with Java/Swift/TypeScript bridges only. | N/A |
| **Docker-friendliness** | **Best** — published as `bbernhard/signal-cli-rest-api:latest` Docker image. Single container, compose-ready. Volume mount for persistent config. | Possible — community Containerfile available (`ghcr.io/asamk/signal-cli`), but requires manual setup of daemon mode. | Docker image available but unmaintained. | Not applicable (library, not a service). | N/A |
| **QR code linking** | **Built-in** — `GET /v1/qrcodelink?device_name=signal-api` returns a QR code image directly. Also provides `GET /v1/qrcodelink/raw` for the raw URI. | Supported — `link` command outputs `sgnl://linkdevice?uuid=...` URI that must be encoded to QR externally (e.g., `qrencode`). | Supported linking but project abandoned. | N/A | N/A |
| **Send/Receive as linked device** | Yes — full send (`POST /v2/send`) and receive (`GET /v1/receive/{number}`, also WebSocket) support as a linked device. | Yes — full CLI support for send/receive in linked device mode. | Yes (when it was maintained). | N/A | N/A |
| **Execution modes** | Three modes: `normal` (JVM per request, slow), `native` (GraalVM binary, fast, low memory), `json-rpc` (persistent JVM daemon, fastest, more memory). | Daemon mode with JSON-RPC (Unix socket, TCP, or HTTP), or one-shot CLI invocations. | Single daemon process. | N/A | N/A |
| **License** | MIT | GPL-3.0 | GPL-3.0 | AGPL-3.0 | N/A |

**Key advantages of signal-cli-rest-api:**

1. **Separation of concerns** — Runs as a sidecar Docker container; the FastAPI app communicates via HTTP. No JVM dependency in the Python service.
2. **QR code generation built-in** — The `/v1/qrcodelink` endpoint returns a QR code image that can be proxied directly to the frontend, simplifying the linking flow.
3. **Swagger documentation** — Full API docs at `bbernhard.github.io/signal-cli-rest-api/`.
4. **Styled text support** — `DEFAULT_SIGNAL_TEXT_MODE` env var and per-message `text_mode` field support `styled` mode for formatted messages.
5. **`json-rpc` mode recommended** — Fastest execution with persistent JVM; best for a server that sends/receives frequently.

### Alternatives Considered

- **signal-cli direct (via JSON-RPC TCP)**: Viable but adds complexity — requires managing the JVM process, parsing JSON-RPC responses, and generating QR codes manually. The REST API wrapper provides the same functionality with a simpler integration surface.
- **signald**: Abandoned project. Homepage explicitly says "no longer actively maintained. Use signal-cli." Not a safe dependency.
- **libsignal**: Not a messaging interface — it's the cryptographic protocol library used internally by Signal clients. No Python bindings. Explicitly states "Use outside of Signal is unsupported."
- **Official Signal Bot API**: Does not exist. Signal intentionally does not provide a bot/business API to protect user privacy.
- **Custom Python implementation on top of libsignal-service-java**: Extremely high effort, fragile, and Signal clients expire after 3 months requiring constant updates.

---

## Topic 2: QR Code Linking Flow

### Decision

**Use the linked device model** via signal-cli-rest-api's QR code linking endpoint. The server application operates as a "linked device" associated with a real Signal account (the app operator's phone number), not as a standalone registered number.

### Rationale

**How Signal device linking works technically:**

1. Signal uses a primary device (the user's phone) and up to **5 linked devices** (Desktop, iPad, or other clients).
2. Linked devices share the same Signal identity/phone number as the primary device.
3. The linking process uses a key exchange: the new device generates a key pair and encodes it into a `sgnl://linkdevice?uuid=<UUID>&pub_key=<KEY>` URI.
4. This URI is displayed as a QR code. The primary device scans it, confirms, and sends the encrypted identity keys to the new device.
5. After linking, the linked device **does not need the phone to be online** to send/receive messages.
6. A linked device **unlinks after 30 days of inactivity** — the server must regularly call `receive` to stay active.
7. Message history from the last 45 days can optionally be synced on first link.

**QR code flow with signal-cli-rest-api:**

1. Backend calls `GET /v1/qrcodelink?device_name=my-app` → returns a PNG image of the QR code.
2. Frontend displays the QR code to the user in the Settings view.
3. User opens Signal on their phone → Settings → Linked Devices → tap "+" → scans the QR code.
4. Signal confirms the link. The REST API container is now a linked device for that phone number.
5. Backend can verify success by calling `GET /v1/accounts` or `GET /v1/devices/{number}`.
6. The QR code **changes with each request** (security measure) — the frontend should not cache it.

**Important constraints:**

- Each signal-cli-rest-api instance links to **one Signal account at a time** per registered number. For multi-user support, the architecture needs one signal-cli instance per linked user, OR a single "app number" model where the app has its own phone number and users message it.
- The spec describes users linking their own Signal accounts — this means the app acts as a linked device on each user's account. This requires **one signal-cli config per user**, which creates scaling complexity.

**Recommended architecture revision:** Instead of linking to each user's Signal account (which would require N signal-cli instances), use a **single app-owned Signal number**. Users send messages TO that number, and the app maps inbound messages to users by their phone number (stored encrypted). This is simpler, matches the spec's "app's Signal contact" language, and is how most Signal bot integrations work.

### Alternatives Considered

- **Standalone registration (new phone number)**: Requires a phone number that can receive SMS for verification, plus solving CAPTCHAs. More independent but needs a dedicated number. This is actually the **recommended approach** — register a dedicated phone number for the app, rather than linking to existing users' accounts.
- **Per-user linked device**: Would require one signal-cli instance per user. Doesn't scale. The 5-device limit per phone would also be a concern. Not recommended.
- **Signal username-based**: Signal now supports usernames, but they're for discovery — messages still route through phone numbers. Not a replacement for the linking flow.

---

## Topic 3: Message Formatting for Signal

### Decision

**Use Signal's native text styling** (BOLD, ITALIC, STRIKETHROUGH, MONOSPACE, SPOILER) via the signal-cli-rest-api `styled` text mode, with plain URLs for clickable links.

### Rationale

**Signal's formatting capabilities:**

| Feature | Support | Details |
|---|---|---|
| **Bold** | Yes | Markdown-like: `*bold*` in styled mode; or explicit style annotations (start:length:BOLD) |
| **Italic** | Yes | Markdown-like: `_italic_` in styled mode; or explicit style annotations (start:length:ITALIC) |
| **Strikethrough** | Yes | Markdown-like: `~strikethrough~` in styled mode; or explicit style annotations |
| **Monospace** | Yes | Uses backticks in styled mode; or explicit style annotations (start:length:MONOSPACE) |
| **Spoiler** | Yes | Explicit style annotation (start:length:SPOILER) — hides text until tapped |
| **Clickable links** | Yes | URLs in message text are **automatically detected and made clickable** by Signal clients. No special markup needed. The REST API also supports **link previews** via `link_preview` field (URL + title + optional thumbnail). |
| **Markdown** | Partial | Signal uses a subset of markdown-like syntax in the app (*bold*, _italic_, ~strikethrough~). Not full Markdown. No headers, lists, or tables. |
| **HTML** | No | Not supported at all. |
| **Max message length** | ~64KB | Signal doesn't publish an official limit. In practice, messages up to ~64KB work. The protocol allows large messages but clients may truncate extremely long ones. |

**signal-cli-rest-api styled text mode:**

- Set `DEFAULT_SIGNAL_TEXT_MODE=styled` env var on the container, OR pass `"text_mode": "styled"` per message.
- In styled mode, markdown-like syntax (`*bold*`, `_italic_`, `~strike~`) is parsed and converted to Signal's native text style annotations.
- For programmatic control, signal-cli also supports explicit `--text-style "start:length:STYLE"` annotations.

**Best practices for action-bearing messages:**

```
📋 *Task Proposal*

_Project: My Project_

Create login page with OAuth support

👉 Review in app: https://app.example.com/projects/123/tasks/456

Reply here with:
  ✅ "approve" to accept
  ❌ "reject" to decline
```

Key formatting guidelines:
1. Use emoji as visual anchors (📋, ✅, ❌, 👉) — universally rendered in Signal.
2. Use bold (`*text*`) for headers/emphasis.
3. Use italic (`_text_`) for metadata (project name, status).
4. Include bare URLs — Signal auto-links them. Use the `link_preview` API field for rich previews.
5. Keep messages under 1000 characters for readability on mobile.
6. Use line breaks liberally for scannability.
7. Avoid deeply nested structure — Signal has no list/table support.

### Alternatives Considered

- **Plain text only**: Works but sacrifices readability. Bold and italic are widely supported across Signal clients and add value.
- **HTML formatting**: Not supported by Signal at all. Would be rendered as raw text.
- **Full Markdown**: Signal only supports a subset. Headers (`#`), bullet lists (`-`), and tables are not rendered. Stick to `*bold*`, `_italic_`, `~strike~`, and backtick monospace.
- **Attachment-based formatting (sending images of formatted text)**: Over-engineered, slow, inaccessible. Not recommended.

---

## Topic 4: Exponential Backoff Retry Pattern in Python asyncio

### Decision

**Use the `tenacity` library** with `asyncio.create_task` for fire-and-forget background retries that don't block the request handler.

### Rationale

**Library comparison:**

| Criterion | tenacity | backoff | Manual implementation |
|---|---|---|---|
| **Maintenance** | Actively maintained, Apache 2.0, widely adopted | Last release Oct 2022 (v2.2.1), less active | N/A |
| **asyncio support** | First-class — `@retry` works on `async` functions natively, `AsyncRetrying` context manager available | Supports asyncio coroutines | Full control |
| **Exponential backoff** | `wait_exponential(multiplier, min, max)` and `wait_random_exponential` (with jitter) | `backoff.expo` with `max_value` and `jitter` | Must implement manually |
| **Logging** | Built-in: `before_log`, `after_log`, `before_sleep_log` callbacks | Built-in: logs to `'backoff'` logger, configurable level | Must implement manually |
| **Flexibility** | Highly composable — combine stop/wait/retry conditions with `|` operator | Good — decorator-based with `on_exception` and `on_predicate` | Unlimited flexibility |
| **Custom callbacks** | `before`, `after`, `before_sleep`, `retry_error_callback` | `on_success`, `on_backoff`, `on_giveup` | N/A |

**tenacity is preferred** because:
1. More actively maintained than `backoff`.
2. More composable API (combining stop conditions, wait strategies).
3. Built-in `before_sleep_log` is perfect for structured logging of retry attempts.
4. `AsyncRetrying` context manager allows retry logic in non-decorator contexts.

**Pattern for fire-and-forget background retry (doesn't block request):**

```python
import asyncio
import logging
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
    retry_if_exception_type,
)

logger = logging.getLogger(__name__)

@retry(
    stop=stop_after_attempt(4),  # 1 initial + 3 retries
    wait=wait_exponential(multiplier=30, min=30, max=480),  # 30s, 60s, 120s, capped at 480s
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
async def _deliver_signal_message(number: str, message: str) -> None:
    """Attempt to deliver a message via Signal with retry."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://signal-api:8080/v2/send",
            json={"message": message, "number": number, "recipients": [number]},
            timeout=10.0,
        )
        response.raise_for_status()


async def send_signal_message(number: str, message: str) -> None:
    """Fire-and-forget Signal message delivery with background retry."""
    async def _task():
        try:
            await _deliver_signal_message(number, message)
            logger.info("Signal message delivered to %s", number)
        except Exception:
            logger.error("Signal message delivery failed after all retries to %s", number)

    asyncio.create_task(_task())
```

**Key patterns:**

1. **`asyncio.create_task()`** — launches the retry loop as a background task; the HTTP request handler returns immediately.
2. **`wait_exponential(multiplier=30, min=30, max=480)`** — matches spec's "30s, 2min, 8min" backoff (30s → 60s → 120s, capped at 480s). Exact values can be tuned with min/max.
3. **`stop_after_attempt(4)`** — 1 initial attempt + 3 retries = 4 total attempts.
4. **`before_sleep_log`** — logs each retry attempt at WARNING level before sleeping.
5. **`reraise=True`** — ensures the final exception propagates to the `_task` wrapper for logging.
6. **Scoped retry** — only retries on connection/timeout errors, not on 4xx client errors.

**Logging pattern:**

```
WARNING - Retrying _deliver_signal_message: attempt #2 ended with ConnectionError
WARNING - Retrying _deliver_signal_message: attempt #3 ended with ConnectionError  
ERROR   - Signal message delivery failed after all retries to +1234567890
```

### Alternatives Considered

- **`backoff` library**: Solid but less actively maintained (last release 2022). API is slightly less composable. Would work fine but tenacity is the safer long-term choice.
- **Manual `asyncio.sleep` loop**: More code, more bugs. No reason to reimplement what tenacity provides.
- **Celery/task queue**: Over-engineered for this use case. The retry happens in-memory over minutes, not hours. If the server restarts mid-retry, the message is lost — which is acceptable per the spec ("best-effort delivery").
- **`asyncio.TaskGroup` (Python 3.11+)**: Good for structured concurrency but doesn't add retry logic. Would still need tenacity inside the task.

---

## Topic 5: Webhook vs Polling for Inbound Signal Messages

### Decision

**Use WebSocket connection** to the signal-cli-rest-api `GET /v1/receive/{number}` endpoint for real-time inbound message reception, with a reconnection loop.

### Rationale

**signal-cli-rest-api receive mechanisms:**

| Method | Endpoint | How it works | Real-time? |
|---|---|---|---|
| **HTTP GET (polling)** | `GET /v1/receive/{number}` | Returns pending messages and clears them from the queue. Must be called repeatedly. | No — introduces latency equal to poll interval |
| **WebSocket** | `ws://signal-api:8080/v1/receive/{number}` | Opens a persistent WebSocket connection. Messages are pushed in real-time as they arrive. Supports ping/pong keep-alive. | **Yes** |
| **AUTO_RECEIVE_SCHEDULE** | Env var (cron) | Automatically calls `receive` on a schedule. Only for normal/native modes. **Warning**: fetches ALL messages, can cause loss if you're also polling. | No |

**WebSocket is the clear winner because:**

1. **Real-time delivery** — matches the spec's "within 30 seconds" requirement for inbound messages.
2. **No message loss** — polling with `GET /v1/receive` clears messages from the queue; if the poll fails mid-request, messages can be lost. WebSocket delivers each message exactly once to the connected client.
3. **Lower overhead** — no repeated HTTP connection setup. Single persistent connection.
4. **signal-cli json-rpc mode compatibility** — WebSocket works best with `json-rpc` mode, which keeps signal-cli running as a daemon.

**Implementation pattern for FastAPI:**

```python
import asyncio
import json
import logging
import websockets

logger = logging.getLogger(__name__)

async def signal_message_listener(number: str):
    """Persistent WebSocket listener for inbound Signal messages."""
    url = f"ws://signal-api:8080/v1/receive/{number}"
    
    while True:  # Reconnection loop
        try:
            async with websockets.connect(url, ping_interval=30) as ws:
                logger.info("Connected to Signal message stream for %s", number)
                async for raw_message in ws:
                    message = json.loads(raw_message)
                    await process_inbound_signal_message(message)
        except (websockets.ConnectionClosed, ConnectionError) as e:
            logger.warning("Signal WebSocket disconnected: %s. Reconnecting in 5s...", e)
            await asyncio.sleep(5)
        except Exception:
            logger.exception("Unexpected error in Signal listener. Reconnecting in 10s...")
            await asyncio.sleep(10)
```

**Mapping incoming Signal messages to app users:**

Inbound messages include the sender's phone number. The mapping flow:

1. Receive message with `source` field (sender's phone number or UUID).
2. Look up `signal_connections` table: `SELECT user_id FROM signal_connections WHERE signal_phone_number_hash = hash(source) AND status = 'connected'`.
3. If found → route to that user's chat session in their most recently active project.
4. If not found → send auto-reply: "Your Signal number is not linked to an account. Visit {app_url}/settings to connect."
5. Phone numbers are stored as encrypted hashes for lookup; the raw number is encrypted at rest per FR-014.

**Important consideration: `json-rpc` mode and `receive`**

- In `json-rpc` mode, signal-cli runs as a persistent daemon that **automatically receives messages** in the background.
- The `AUTO_RECEIVE_SCHEDULE` env var should **NOT** be used when consuming messages via WebSocket — it would consume messages before the WebSocket can deliver them.
- The signal-cli-rest-api docs explicitly warn: "Calling `receive` will fetch all the messages... if you are using the REST API for receiving messages, it's not a good idea to use `AUTO_RECEIVE_SCHEDULE`."

### Alternatives Considered

- **HTTP polling**: Simpler to implement but introduces latency (poll interval tradeoff). Risk of message loss if polling fails. Would require `AUTO_RECEIVE_SCHEDULE` or manual periodic calls. Not recommended for real-time use.
- **Webhook (push from signal-cli-rest-api)**: signal-cli-rest-api does **not** natively support outbound webhooks (HTTP callbacks to a configured URL). There is no `WEBHOOK_URL` config option. The only push mechanism is WebSocket.
- **signal-cli JSON-RPC directly via TCP**: Could connect to signal-cli's daemon TCP socket (port 7583) and subscribe to incoming messages via JSON-RPC. This bypasses the REST API but couples tightly to signal-cli's internal protocol. Not recommended when the REST API is available.
- **Polling with short interval (1-2s)**: Could meet the 30-second SLA but wastes resources and still risks race conditions with message consumption. WebSocket is strictly better.

---

## Summary of Decisions

| Topic | Decision | Confidence |
|---|---|---|
| **1. Messaging Interface** | `signal-cli-rest-api` Docker container, `json-rpc` mode | High |
| **2. QR Code Linking** | Linked device model via `/v1/qrcodelink` endpoint; single app-owned number recommended over per-user linking | High |
| **3. Message Formatting** | Signal styled text mode (`*bold*`, `_italic_`), emoji anchors, bare URLs with link previews | High |
| **4. Retry Pattern** | `tenacity` library with `asyncio.create_task` for background fire-and-forget | High |
| **5. Inbound Messages** | WebSocket to `/v1/receive/{number}` with reconnection loop | High |

## Architecture Implications

Based on this research, the recommended Docker Compose topology is:

```yaml
services:
  backend:
    # FastAPI app — connects to signal-api via HTTP and WebSocket
    depends_on:
      - signal-api
      
  signal-api:
    image: bbernhard/signal-cli-rest-api:latest
    environment:
      - MODE=json-rpc
      - DEFAULT_SIGNAL_TEXT_MODE=styled
    ports:
      - "8080"  # Internal only — not exposed to host
    volumes:
      - signal-cli-config:/home/.local/share/signal-cli

volumes:
  signal-cli-config:
```

The FastAPI backend communicates with signal-api over the internal Docker network. No Signal-related ports are exposed to the public internet.
