"""Regression tests for route-level authorization.

Bug-bash: Verifies that all project-scoped agent endpoints include
the verify_project_access dependency to prevent authorization bypass.
"""

from src.api.agents import router as agents_router
from src.dependencies import verify_project_access


class TestAgentEndpointAuthorization:
    """All project-scoped agent routes must enforce verify_project_access."""

    def _get_route_deps(self, method: str, path: str):
        """Return the dependency list for a given route."""
        for route in agents_router.routes:
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
            # The dependency callable is the .dependency attribute of the Depends() object
            if hasattr(dep, "dependency") and dep.dependency is verify_project_access:
                return True
        return False

    def test_list_agents_has_project_access_check(self):
        assert self._has_verify_project_access("GET", "/{project_id}")

    def test_list_pending_agents_has_project_access_check(self):
        """Regression: GET /pending was missing verify_project_access."""
        assert self._has_verify_project_access("GET", "/{project_id}/pending")

    def test_purge_pending_agents_has_project_access_check(self):
        """Regression: DELETE /pending was missing verify_project_access."""
        assert self._has_verify_project_access("DELETE", "/{project_id}/pending")

    def test_bulk_update_models_has_project_access_check(self):
        assert self._has_verify_project_access("PATCH", "/{project_id}/bulk-model")
