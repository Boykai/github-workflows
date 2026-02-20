"""GitHub Projects V2 GraphQL service (package facade).

This package splits the monolithic ``GitHubProjectsService`` into focused
mixin modules while preserving the original public API.  Importing from
``src.services.github_projects`` behaves identically to the old single-file
module.
"""

from ._base import _BaseServiceMixin
from ._copilot_ops import _CopilotOpsMixin
from ._issue_ops import _IssueOpsMixin
from ._pr_ops import _PrOpsMixin
from ._project_ops import _ProjectOpsMixin
from ._queries import (
    ADD_ISSUE_TO_PROJECT_MUTATION,
    ASSIGN_COPILOT_MUTATION,
    BOARD_GET_PROJECT_ITEMS_QUERY,
    BOARD_LIST_PROJECTS_QUERY,
    CREATE_DRAFT_ITEM_MUTATION,
    GET_ISSUE_LINKED_PRS_QUERY,
    GET_ISSUE_WITH_COMMENTS_QUERY,
    GET_PROJECT_FIELD_QUERY,
    GET_PROJECT_FIELDS_QUERY,
    GET_PROJECT_ITEMS_QUERY,
    GET_PROJECT_REPOSITORY_QUERY,
    GET_PULL_REQUEST_QUERY,
    GET_SUGGESTED_ACTORS_QUERY,
    GITHUB_GRAPHQL_URL,
    INITIAL_BACKOFF_SECONDS,
    LIST_ORG_PROJECTS_QUERY,
    LIST_USER_PROJECTS_QUERY,
    MARK_PR_READY_FOR_REVIEW_MUTATION,
    MAX_BACKOFF_SECONDS,
    MAX_RETRIES,
    MERGE_PULL_REQUEST_MUTATION,
    PROJECT_FIELDS_FRAGMENT,
    REQUEST_COPILOT_REVIEW_MUTATION,
    UPDATE_DATE_FIELD_MUTATION,
    UPDATE_ITEM_STATUS_MUTATION,
    UPDATE_NUMBER_FIELD_MUTATION,
    UPDATE_SINGLE_SELECT_FIELD_MUTATION,
    UPDATE_TEXT_FIELD_MUTATION,
)
from ._status_ops import _StatusOpsMixin


class GitHubProjectsService(
    _BaseServiceMixin,
    _ProjectOpsMixin,
    _IssueOpsMixin,
    _PrOpsMixin,
    _CopilotOpsMixin,
    _StatusOpsMixin,
):
    """Service for interacting with GitHub Projects V2 API."""


# Global service instance
github_projects_service = GitHubProjectsService()

__all__ = [
    # Service class and singleton
    "GitHubProjectsService",
    "github_projects_service",
    # Constants
    "GITHUB_GRAPHQL_URL",
    "MAX_RETRIES",
    "INITIAL_BACKOFF_SECONDS",
    "MAX_BACKOFF_SECONDS",
    # GraphQL fragments and queries
    "PROJECT_FIELDS_FRAGMENT",
    "LIST_USER_PROJECTS_QUERY",
    "LIST_ORG_PROJECTS_QUERY",
    "GET_PROJECT_ITEMS_QUERY",
    "CREATE_DRAFT_ITEM_MUTATION",
    "UPDATE_ITEM_STATUS_MUTATION",
    "ADD_ISSUE_TO_PROJECT_MUTATION",
    "GET_PROJECT_FIELD_QUERY",
    "GET_PROJECT_REPOSITORY_QUERY",
    "ASSIGN_COPILOT_MUTATION",
    "GET_ISSUE_WITH_COMMENTS_QUERY",
    "GET_SUGGESTED_ACTORS_QUERY",
    "GET_ISSUE_LINKED_PRS_QUERY",
    "MARK_PR_READY_FOR_REVIEW_MUTATION",
    "REQUEST_COPILOT_REVIEW_MUTATION",
    "MERGE_PULL_REQUEST_MUTATION",
    "GET_PULL_REQUEST_QUERY",
    "GET_PROJECT_FIELDS_QUERY",
    "UPDATE_SINGLE_SELECT_FIELD_MUTATION",
    "UPDATE_NUMBER_FIELD_MUTATION",
    "UPDATE_DATE_FIELD_MUTATION",
    "UPDATE_TEXT_FIELD_MUTATION",
    "BOARD_LIST_PROJECTS_QUERY",
    "BOARD_GET_PROJECT_ITEMS_QUERY",
]
