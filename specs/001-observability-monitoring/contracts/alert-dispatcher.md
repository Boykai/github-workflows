# Contract: Alert Dispatcher Interface

**Module**: `solune/backend/src/services/alert_dispatcher.py`
**Feature**: 001-observability-monitoring
**Requirements**: FR-006, FR-007, FR-008, FR-009, FR-010, FR-011

## Purpose

Pluggable alert dispatcher for SLA-breach notifications. Supports log-only mode (default) and optional webhook delivery. Enforces per-type cooldown to prevent alert fatigue.

## Interface

```python
class AlertDispatcher:
    """Pluggable alert dispatcher with cooldown enforcement."""

    def __init__(
        self,
        webhook_url: str = "",
        cooldown_minutes: int = 15,
    ) -> None:
        """
        Initialize the alert dispatcher.

        Args:
            webhook_url: URL for webhook delivery. Empty string = log-only mode.
            cooldown_minutes: Minimum minutes between alerts of the same type.
        """

    async def dispatch_alert(
        self,
        alert_type: str,
        summary: str,
        details: dict[str, Any],
    ) -> None:
        """
        Dispatch an alert if cooldown has expired for this alert type.

        Args:
            alert_type: Category identifier (e.g., "pipeline_stall", "rate_limit_critical")
            summary: Human-readable one-line description
            details: Structured payload with alert-specific information

        Behavior:
            1. Check cooldown: If an alert of the same type was dispatched
               less than cooldown_minutes ago, suppress (no-op with debug log).
            2. Log the alert as a structured WARNING message.
            3. If webhook_url is configured, POST the payload to the URL.
            4. Update the cooldown timestamp for this alert type.
        """
```

## Alert Types

### `pipeline_stall`

**Trigger**: `recovery.py` detects a pipeline stall exceeding `pipeline_stall_alert_minutes` threshold.

**Details Payload**:
```json
{
  "issue_number": 42,
  "stall_duration_minutes": 35,
  "threshold_minutes": 30,
  "pipeline_state": "active"
}
```

### `rate_limit_critical`

**Trigger**: `polling_loop.py` detects GitHub API remaining quota below `rate_limit_critical_threshold`.

**Details Payload**:
```json
{
  "remaining": 15,
  "limit": 5000,
  "threshold": 20,
  "reset_at": 1742655600
}
```

## Webhook Payload Format

When `alert_webhook_url` is configured, the following JSON payload is POSTed:

```json
{
  "alert_type": "pipeline_stall",
  "summary": "Pipeline stall detected: issue #42 stalled for 35 minutes (threshold: 30)",
  "details": { "...alert-type-specific..." },
  "fired_at": "2026-03-22T14:00:00Z",
  "service": "solune-backend"
}
```

**Headers**:
- `Content-Type: application/json`

**Timeout**: 5 seconds

**Error Handling**: On webhook delivery failure, the alert is still logged locally. The failure is logged as a warning. No retries are attempted.

## Cooldown Behavior

- Default cooldown: 15 minutes (configurable via `alert_cooldown_minutes`)
- Cooldown is per alert type — different alert types have independent cooldowns
- Boundary is inclusive: alert fires at exactly `cooldown_minutes` after last dispatch
- Cooldown state is in-memory — resets on application restart
- Suppressed alerts are logged at DEBUG level for auditability

## Integration Points

### recovery.py

```python
# After detecting a stall exceeding threshold:
await alert_dispatcher.dispatch_alert(
    alert_type="pipeline_stall",
    summary=f"Pipeline stall detected: issue #{issue_number} stalled for {stall_minutes} minutes",
    details={
        "issue_number": issue_number,
        "stall_duration_minutes": stall_minutes,
        "threshold_minutes": settings.pipeline_stall_alert_minutes,
        "pipeline_state": current_state,
    },
)
```

### polling_loop.py

```python
# After rate-limit check detects critical level:
rate_info = github_projects_service.get_last_rate_limit()
if rate_info and rate_info["remaining"] < settings.rate_limit_critical_threshold:
    await alert_dispatcher.dispatch_alert(
        alert_type="rate_limit_critical",
        summary=f"GitHub API rate limit critical: {rate_info['remaining']} remaining (threshold: {settings.rate_limit_critical_threshold})",
        details={
            "remaining": rate_info["remaining"],
            "limit": rate_info["limit"],
            "threshold": settings.rate_limit_critical_threshold,
            "reset_at": rate_info["reset_at"],
        },
    )
```

## Configuration

| Setting | Default | Environment Variable | Description |
|---------|---------|---------------------|-------------|
| `alert_webhook_url` | `""` | `ALERT_WEBHOOK_URL` | Webhook URL (empty = log-only) |
| `alert_cooldown_minutes` | `15` | `ALERT_COOLDOWN_MINUTES` | Cooldown between same-type alerts |
| `pipeline_stall_alert_minutes` | `30` | `PIPELINE_STALL_ALERT_MINUTES` | Stall age threshold for alert |
| `agent_timeout_alert_minutes` | `15` | `AGENT_TIMEOUT_ALERT_MINUTES` | Agent timeout threshold for alert |
| `rate_limit_critical_threshold` | `20` | `RATE_LIMIT_CRITICAL_THRESHOLD` | API remaining count threshold |
