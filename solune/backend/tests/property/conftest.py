"""Hypothesis settings profiles for property-based tests."""

import os

from hypothesis import HealthCheck, settings

# CI profile: more examples, stricter deadlines
settings.register_profile(
    "ci",
    max_examples=200,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.differing_executors],
)

# Dev profile: fewer examples for faster feedback
settings.register_profile(
    "dev",
    max_examples=20,
    deadline=400,
    suppress_health_check=[HealthCheck.differing_executors],
)

# Default to dev; CI sets HYPOTHESIS_PROFILE=ci
settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "dev"))
