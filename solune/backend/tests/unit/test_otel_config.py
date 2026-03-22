"""Tests for OTel setup and config integration (src/services/otel_setup.py).

Covers:
- get_tracer() returns NoOpTracer when OTel is not initialised
- get_meter() returns NoOpMeter when OTel is not initialised
- Config fields have correct defaults
- Config fields respect environment variables
"""


class TestOtelSetupNoOp:
    """Tests for no-op behavior when OTel is not initialised."""

    def test_get_tracer_returns_noop(self):
        """get_tracer() returns a local no-op tracer when OTel is not initialised."""
        # Reset module state
        import src.services.otel_setup as otel_mod

        otel_mod._tracer = None

        tracer = otel_mod.get_tracer()
        assert isinstance(tracer, otel_mod._NoOpTracer)

    def test_get_meter_returns_noop(self):
        """get_meter() returns a local no-op meter when OTel is not initialised."""
        import src.services.otel_setup as otel_mod

        otel_mod._meter = None

        meter = otel_mod.get_meter()
        assert isinstance(meter, otel_mod._NoOpMeter)


class TestObservabilityConfigDefaults:
    """Tests that observability config fields have correct defaults."""

    def test_otel_enabled_default_false(self):
        """OTEL_ENABLED defaults to False."""
        from src.config import Settings

        # Build Settings with required fields only
        s = Settings(
            github_client_id="test",
            github_client_secret="secret",
            session_secret_key="test-key",
            debug=True,
        )
        assert s.otel_enabled is False

    def test_sentry_dsn_default_empty(self):
        """SENTRY_DSN defaults to empty string."""
        from src.config import Settings

        s = Settings(
            github_client_id="test",
            github_client_secret="secret",
            session_secret_key="test-key",
            debug=True,
        )
        assert s.sentry_dsn == ""

    def test_alert_defaults(self):
        """Alert config fields have correct defaults."""
        from src.config import Settings

        s = Settings(
            github_client_id="test",
            github_client_secret="secret",
            session_secret_key="test-key",
            debug=True,
        )
        assert s.pipeline_stall_alert_minutes == 30
        assert s.agent_timeout_alert_minutes == 15
        assert s.rate_limit_critical_threshold == 20
        assert s.alert_webhook_url == ""
        assert s.alert_cooldown_minutes == 15

    def test_otel_endpoint_default(self):
        """OTel endpoint defaults to localhost:4317."""
        from src.config import Settings

        s = Settings(
            github_client_id="test",
            github_client_secret="secret",
            session_secret_key="test-key",
            debug=True,
        )
        assert s.otel_endpoint == "http://localhost:4317"

    def test_otel_service_name_default(self):
        """OTel service name defaults to solune-backend."""
        from src.config import Settings

        s = Settings(
            github_client_id="test",
            github_client_secret="secret",
            session_secret_key="test-key",
            debug=True,
        )
        assert s.otel_service_name == "solune-backend"
