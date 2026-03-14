"""Reusable assertion helpers for backend tests.

Provides common assertion patterns to reduce boilerplate in API and
service tests.
"""

from typing import Any


def assert_api_success(response, *, status_code: int = 200) -> dict:
    """Assert that an API response indicates success and return JSON body.

    Args:
        response: httpx Response object.
        status_code: Expected HTTP status code (default 200).

    Returns:
        Parsed JSON response body.
    """
    assert response.status_code == status_code, (
        f"Expected {status_code}, got {response.status_code}: {response.text}"
    )
    return response.json()


def assert_api_error(
    response,
    *,
    status_code: int,
    error_substring: str | None = None,
) -> dict:
    """Assert that an API response indicates an error.

    Args:
        response: httpx Response object.
        status_code: Expected HTTP error status code.
        error_substring: Optional substring that must appear in the response body.

    Returns:
        Parsed JSON response body.
    """
    assert response.status_code == status_code, (
        f"Expected {status_code}, got {response.status_code}: {response.text}"
    )
    data = response.json()
    if error_substring:
        body_text = str(data).lower()
        assert error_substring.lower() in body_text, (
            f"Expected '{error_substring}' in response body, got: {data}"
        )
    return data


def assert_json_structure(data: dict, expected_keys: set[str]) -> None:
    """Assert that a JSON dict contains at least the specified keys.

    Args:
        data: Parsed JSON dictionary.
        expected_keys: Set of keys that must be present.
    """
    missing = expected_keys - set(data.keys())
    assert not missing, f"Missing keys in response: {missing}"


def assert_json_values(data: dict, expected: dict[str, Any]) -> None:
    """Assert that a JSON dict contains specified key-value pairs.

    Args:
        data: Parsed JSON dictionary.
        expected: Mapping of key → expected value.
    """
    for key, value in expected.items():
        assert key in data, f"Key '{key}' not found in response"
        assert data[key] == value, f"Key '{key}': expected {value!r}, got {data[key]!r}"
