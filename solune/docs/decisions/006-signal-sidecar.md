# ADR-006: Signal messaging via `signal-cli-rest-api` sidecar

**Status**: Accepted
**Date**: 2025-Q1

## Context

The system needs to send and receive Signal messages to allow users to interact with the agent pipeline from their phones. Options for Signal integration:

- **Signal native SDK** — No official SDK exists; would require reverse-engineering the Signal protocol.
- **signal-cli (direct)** — Java CLI tool; embedding in a Python process is complex and requires a JVM.
- **`bbernhard/signal-cli-rest-api`** — Docker sidecar that wraps `signal-cli` with a REST + WebSocket API; widely used in the open-source community.

## Decision

Run `bbernhard/signal-cli-rest-api` as a Docker Compose sidecar service (`solune-signal-api`) accessible via HTTP at `signal-api:8080`. The backend communicates with the sidecar via:

- **HTTP** — Send messages, generate QR codes, manage account registration.
- **WebSocket** — Receive inbound messages in real time.

Phone numbers are Fernet-encrypted at rest; SHA-256 hashes are used for lookup to avoid exposing plaintext numbers.

## Consequences

- **+** No custom protocol implementation needed; the sidecar handles all Signal protocol complexity.
- **+** Isolation: the sidecar manages Signal state independently; it can be restarted without affecting the backend.
- **+** Health check in `docker-compose.yml` ensures the backend does not start polling before the sidecar is ready.
- **−** Adds a third container to the Docker Compose stack; users who don't need Signal still run the sidecar.
- **−** The sidecar requires a dedicated phone number and device registration; initial setup is manual.
- **−** The `signal-cli` project is not officially supported by Signal; future Signal protocol changes may break the sidecar.
