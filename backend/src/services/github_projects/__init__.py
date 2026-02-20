"""GitHub Projects V2 service - composed from focused sub-modules."""

from .client import GitHubClientMixin
from .copilot_ops import CopilotOpsMixin
from .fields import FieldsMixin
from .issues import IssuesMixin
from .projects import ProjectsMixin
from .pull_requests import PullRequestsMixin


class GitHubProjectsService(
    GitHubClientMixin,
    ProjectsMixin,
    IssuesMixin,
    PullRequestsMixin,
    CopilotOpsMixin,
    FieldsMixin,
):
    """Service for interacting with GitHub Projects V2 API."""

    def __init__(self):
        super().__init__()


# Global service instance
github_projects_service = GitHubProjectsService()
