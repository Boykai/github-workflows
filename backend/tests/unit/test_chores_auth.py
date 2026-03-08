"""Regression tests for route-level authorization on chores endpoints.

Bug-bash: Verifies that all project-scoped chores endpoints include
the verify_project_access dependency to prevent authorization bypass.
"""

from src.api.chores import router as chores_router
from src.dependencies import verify_project_access


class TestChoresEndpointAuthorization:
    """All project-scoped chores routes must enforce verify_project_access."""

    def _get_route_deps(self, method: str, path: str):
        """Return the dependency list for a given route."""
        for route in chores_router.routes:
            route_path = getattr(route, "path", "")
            route_methods = {m.upper() for m in getattr(route, "methods", set())}
            if route_path == path and method.upper() in route_methods:
                return getattr(route, "dependencies", [])
        return None

    def _has_verify_project_access(self, method: str, path: str) -> bool:
        deps = self._get_route_deps(method, path)
        if deps is None:
            return False
        for dep in deps:
            if hasattr(dep, "dependency") and dep.dependency is verify_project_access:
                return True
        return False

    def test_list_templates_has_project_access_check(self):
        """Regression: GET /{project_id}/templates was missing verify_project_access."""
        assert self._has_verify_project_access("GET", "/{project_id}/templates")

    def test_list_chores_has_project_access_check(self):
        """Regression: GET /{project_id} was missing verify_project_access."""
        assert self._has_verify_project_access("GET", "/{project_id}")

    def test_create_chore_has_project_access_check(self):
        """Regression: POST /{project_id} was missing verify_project_access."""
        assert self._has_verify_project_access("POST", "/{project_id}")

    def test_update_chore_has_project_access_check(self):
        """Regression: PATCH /{project_id}/{chore_id} was missing verify_project_access."""
        assert self._has_verify_project_access("PATCH", "/{project_id}/{chore_id}")

    def test_delete_chore_has_project_access_check(self):
        """Regression: DELETE /{project_id}/{chore_id} was missing verify_project_access."""
        assert self._has_verify_project_access("DELETE", "/{project_id}/{chore_id}")

    def test_trigger_chore_has_project_access_check(self):
        """Regression: POST /{project_id}/{chore_id}/trigger was missing verify_project_access."""
        assert self._has_verify_project_access("POST", "/{project_id}/{chore_id}/trigger")

    def test_chore_chat_has_project_access_check(self):
        """Regression: POST /{project_id}/chat was missing verify_project_access."""
        assert self._has_verify_project_access("POST", "/{project_id}/chat")

    def test_inline_update_has_project_access_check(self):
        """Regression: PUT /{project_id}/{chore_id}/inline-update was missing verify_project_access."""
        assert self._has_verify_project_access("PUT", "/{project_id}/{chore_id}/inline-update")

    def test_create_with_merge_has_project_access_check(self):
        """Regression: POST /{project_id}/create-with-merge was missing verify_project_access."""
        assert self._has_verify_project_access("POST", "/{project_id}/create-with-merge")
