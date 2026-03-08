"""Regression tests for route-level authorization on pipeline endpoints.

Bug-bash: Verifies that all project-scoped pipeline endpoints include
the verify_project_access dependency to prevent authorization bypass.
"""

from src.api.pipelines import router as pipelines_router
from src.dependencies import verify_project_access


class TestPipelineEndpointAuthorization:
    """All project-scoped pipeline routes must enforce verify_project_access."""

    def _get_route_deps(self, method: str, path: str):
        """Return the dependency list for a given route."""
        for route in pipelines_router.routes:
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

    def test_list_pipelines_has_project_access_check(self):
        """Regression: GET /{project_id} was missing verify_project_access."""
        assert self._has_verify_project_access("GET", "/{project_id}")

    def test_seed_presets_has_project_access_check(self):
        """Regression: POST /{project_id}/seed-presets was missing verify_project_access."""
        assert self._has_verify_project_access("POST", "/{project_id}/seed-presets")

    def test_get_assignment_has_project_access_check(self):
        """Regression: GET /{project_id}/assignment was missing verify_project_access."""
        assert self._has_verify_project_access("GET", "/{project_id}/assignment")

    def test_set_assignment_has_project_access_check(self):
        """Regression: PUT /{project_id}/assignment was missing verify_project_access."""
        assert self._has_verify_project_access("PUT", "/{project_id}/assignment")

    def test_create_pipeline_has_project_access_check(self):
        """Regression: POST /{project_id} was missing verify_project_access."""
        assert self._has_verify_project_access("POST", "/{project_id}")

    def test_get_pipeline_has_project_access_check(self):
        """Regression: GET /{project_id}/{pipeline_id} was missing verify_project_access."""
        assert self._has_verify_project_access("GET", "/{project_id}/{pipeline_id}")

    def test_update_pipeline_has_project_access_check(self):
        """Regression: PUT /{project_id}/{pipeline_id} was missing verify_project_access."""
        assert self._has_verify_project_access("PUT", "/{project_id}/{pipeline_id}")

    def test_delete_pipeline_has_project_access_check(self):
        """Regression: DELETE /{project_id}/{pipeline_id} was missing verify_project_access."""
        assert self._has_verify_project_access("DELETE", "/{project_id}/{pipeline_id}")
