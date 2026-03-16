"""Hypothesis settings profiles for property-based tests."""

from hypothesis import HealthCheck, settings

# CI profile: more examples, stricter deadlines
settings.register_profile(
    "ci",
    max_examples=200,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)

# Dev profile: fewer examples for faster feedback
settings.register_profile(
    "dev",
    max_examples=20,
    deadline=400,
)

# Default to dev; CI sets HYPOTHESIS_PROFILE=ci
settings.load_profile("dev")
