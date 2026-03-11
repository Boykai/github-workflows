from __future__ import annotations

from typing import TYPE_CHECKING

from src.logging_utils import get_logger

if TYPE_CHECKING:
    from src.services.github_projects import GitHubClientFactory

# Domain mixins — method implementations live in separate files
from src.services.github_projects.agents import AgentsMixin
from src.services.github_projects.base_client import GitHubBaseClient
from src.services.github_projects.board import BoardMixin
from src.services.github_projects.branches import BranchesMixin
from src.services.github_projects.copilot import CopilotMixin
from src.services.github_projects.identities import (
    is_copilot_author as _is_copilot_author,
)
from src.services.github_projects.identities import (
    is_copilot_reviewer_bot as _is_copilot_reviewer_bot,
)
from src.services.github_projects.identities import (
    is_copilot_swe_agent as _is_copilot_swe_agent,
)
from src.services.github_projects.issues import IssuesMixin
from src.services.github_projects.projects import ProjectsMixin
from src.services.github_projects.pull_requests import PullRequestsMixin
from src.services.github_projects.repository import RepositoryMixin

logger = get_logger(__name__)


class GitHubProjectsService(
    AgentsMixin,
    BoardMixin,
    BranchesMixin,
    CopilotMixin,
    IssuesMixin,
    ProjectsMixin,
    PullRequestsMixin,
    RepositoryMixin,
    GitHubBaseClient,
):
    """Service for interacting with GitHub Projects V2 API.

    Inherits shared HTTP infrastructure (REST, GraphQL, rate-limit tracking,
    request coalescing) from :class:`GitHubBaseClient` and domain-specific
    operations from the individual mixins.
    """

    def __init__(self, client_factory: GitHubClientFactory | None = None) -> None:
        super().__init__(client_factory)

    @staticmethod
    def is_copilot_author(login: str) -> bool:
        return _is_copilot_author(login)

    @staticmethod
    def is_copilot_swe_agent(login: str) -> bool:
        return _is_copilot_swe_agent(login)

    @staticmethod
    def is_copilot_reviewer_bot(login: str) -> bool:
        return _is_copilot_reviewer_bot(login)

    def get_last_rate_limit(self) -> dict[str, int] | None:
        """Return the most recent rate-limit info.

        Delegates to the :class:`RateLimitManager` extracted into
        ``rate_limit.py``.
        """
        return self._rate_limit.get()

    def clear_last_rate_limit(self) -> None:
        """Clear both the request-scoped and instance-level rate-limit caches.

        Called by the polling loop when stale rate-limit data is detected.
        """
        self._rate_limit.clear()


# TODO(018-codebase-audit-refactor): Module-level singleton should be removed
# in favor of exclusive app.state registration. Deferred because 17+ files
# import this directly in non-request contexts (background tasks, signal bridge,
# orchestrator) where Request.app.state is not available.
# Global service instance
github_projects_service = GitHubProjectsService()
