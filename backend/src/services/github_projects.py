"""GitHub Projects V2 GraphQL service."""

import asyncio
import logging
import re
from datetime import datetime

import httpx
import yaml

from src.models.chat import AgentSource, AvailableAgent
from src.models.project import GitHubProject, ProjectType, StatusColumn
from src.models.task import Task

logger = logging.getLogger(__name__)

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"

# T057: Rate limit configuration
MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 1
MAX_BACKOFF_SECONDS = 30


# GraphQL fragments for reusable field selections
PROJECT_FIELDS_FRAGMENT = """
fragment ProjectFields on ProjectV2 {
  id
  title
  url
  shortDescription
  closed
  field(name: "Status") {
    ... on ProjectV2SingleSelectField {
      id
      options {
        id
        name
        color
      }
    }
  }
  items(first: 1) {
    totalCount
  }
}
"""

# GraphQL queries
LIST_USER_PROJECTS_QUERY = (
    PROJECT_FIELDS_FRAGMENT
    + """
query($login: String!, $first: Int!) {
  user(login: $login) {
    projectsV2(first: $first) {
      nodes {
        ...ProjectFields
      }
    }
  }
}
"""
)

LIST_ORG_PROJECTS_QUERY = (
    PROJECT_FIELDS_FRAGMENT
    + """
query($login: String!, $first: Int!) {
  organization(login: $login) {
    projectsV2(first: $first) {
      nodes {
        ...ProjectFields
      }
    }
  }
}
"""
)

GET_PROJECT_ITEMS_QUERY = """
query($projectId: ID!, $first: Int!, $after: String) {
  node(id: $projectId) {
    ... on ProjectV2 {
      items(first: $first, after: $after) {
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          id
          fieldValueByName(name: "Status") {
            ... on ProjectV2ItemFieldSingleSelectValue {
              name
              optionId
            }
          }
          content {
            ... on DraftIssue {
              title
              body
            }
            ... on Issue {
              id
              number
              title
              body
              repository {
                owner {
                  login
                }
                name
              }
            }
            ... on PullRequest {
              id
              number
              title
              body
              repository {
                owner {
                  login
                }
                name
              }
            }
          }
        }
      }
    }
  }
}
"""

CREATE_DRAFT_ITEM_MUTATION = """
mutation($projectId: ID!, $title: String!, $body: String) {
  addProjectV2DraftIssue(input: {projectId: $projectId, title: $title, body: $body}) {
    projectItem {
      id
    }
  }
}
"""

UPDATE_ITEM_STATUS_MUTATION = """
mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
  updateProjectV2ItemFieldValue(
    input: {
      projectId: $projectId
      itemId: $itemId
      fieldId: $fieldId
      value: { singleSelectOptionId: $optionId }
    }
  ) {
    projectV2Item {
      id
    }
  }
}
"""

# T019: GraphQL mutation to add existing issue to project
ADD_ISSUE_TO_PROJECT_MUTATION = """
mutation($projectId: ID!, $contentId: ID!) {
  addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
    item {
      id
    }
  }
}
"""

# Query to get project field info for status updates
GET_PROJECT_FIELD_QUERY = """
query($projectId: ID!) {
  node(id: $projectId) {
    ... on ProjectV2 {
      field(name: "Status") {
        ... on ProjectV2SingleSelectField {
          id
          options {
            id
            name
          }
        }
      }
    }
  }
}
"""

# Query to get repository info from project items (for issue creation target)
GET_PROJECT_REPOSITORY_QUERY = """
query($projectId: ID!) {
  node(id: $projectId) {
    ... on ProjectV2 {
      items(first: 10) {
        nodes {
          content {
            ... on Issue {
              repository {
                owner {
                  login
                }
                name
              }
            }
            ... on PullRequest {
              repository {
                owner {
                  login
                }
                name
              }
            }
          }
        }
      }
    }
  }
}
"""

# GraphQL mutation to assign Copilot to an issue with agent assignment config
# Requires headers: GraphQL-Features: issues_copilot_assignment_api_support,coding_agent_model_selection
ASSIGN_COPILOT_MUTATION = """
mutation($issueId: ID!, $assigneeIds: [ID!]!, $repoId: ID!, $baseRef: String!, $customInstructions: String!, $customAgent: String!) {
  addAssigneesToAssignable(input: {
    assignableId: $issueId,
    assigneeIds: $assigneeIds,
    agentAssignment: {
      targetRepositoryId: $repoId,
      baseRef: $baseRef,
      customInstructions: $customInstructions,
      customAgent: $customAgent,
      model: "claude-opus-4.6"
    }
  }) {
    assignable {
      ... on Issue {
        id
        assignees(first: 10) {
          nodes {
            login
          }
        }
      }
    }
  }
}
"""

# GraphQL query to get issue details including title, body, and comments
GET_ISSUE_WITH_COMMENTS_QUERY = """
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    issue(number: $number) {
      id
      title
      body
      comments(first: 100) {
        nodes {
          id
          author {
            login
          }
          body
          createdAt
        }
      }
    }
  }
}
"""

# GraphQL query to get suggested actors (including Copilot bot) for a repository
GET_SUGGESTED_ACTORS_QUERY = """
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    id
    suggestedActors(capabilities: [CAN_BE_ASSIGNED], first: 100) {
      nodes {
        login
        __typename
        ... on Bot {
          id
        }
        ... on User {
          id
        }
      }
    }
  }
}
"""

# GraphQL query to get linked pull requests for an issue
GET_ISSUE_LINKED_PRS_QUERY = """
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    issue(number: $number) {
      id
      title
      state
      timelineItems(itemTypes: [CONNECTED_EVENT, CROSS_REFERENCED_EVENT], first: 50) {
        nodes {
          ... on ConnectedEvent {
            subject {
              ... on PullRequest {
                id
                number
                title
                state
                isDraft
                url
                headRefName
                author {
                  login
                }
                createdAt
                updatedAt
              }
            }
          }
          ... on CrossReferencedEvent {
            source {
              ... on PullRequest {
                id
                number
                title
                state
                isDraft
                url
                headRefName
                author {
                  login
                }
                createdAt
                updatedAt
              }
            }
          }
        }
      }
    }
  }
}
"""

# GraphQL mutation to mark a draft PR as ready for review
MARK_PR_READY_FOR_REVIEW_MUTATION = """
mutation($pullRequestId: ID!) {
  markPullRequestReadyForReview(input: {pullRequestId: $pullRequestId}) {
    pullRequest {
      id
      number
      isDraft
      state
      url
    }
  }
}
"""

# GraphQL mutation to request Copilot code review on a PR
REQUEST_COPILOT_REVIEW_MUTATION = """
mutation($pullRequestId: ID!) {
  requestReviewsByLogin(input: {pullRequestId: $pullRequestId, botLogins: ["copilot"]}) {
    pullRequest {
      id
      number
      url
    }
  }
}
"""

# GraphQL mutation to merge a pull request into its base branch
# Used to merge child PR branches into the parent/main branch for an issue
MERGE_PULL_REQUEST_MUTATION = """
mutation($pullRequestId: ID!, $commitHeadline: String, $mergeMethod: PullRequestMergeMethod) {
  mergePullRequest(input: {
    pullRequestId: $pullRequestId,
    commitHeadline: $commitHeadline,
    mergeMethod: $mergeMethod
  }) {
    pullRequest {
      id
      number
      state
      merged
      mergedAt
      mergeCommit {
        oid
      }
      url
    }
  }
}
"""

# GraphQL query to get PR details by number (with commit status for completion detection)
GET_PULL_REQUEST_QUERY = """
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      id
      number
      title
      body
      state
      isDraft
      url
      headRefName
      baseRefName
      author {
        login
      }
      reviewRequests(first: 10) {
        nodes {
          requestedReviewer {
            ... on User {
              login
            }
          }
        }
      }
      reviews(first: 50) {
        nodes {
          author {
            login
          }
          state
          body
          createdAt
        }
      }
      commits(last: 1) {
        nodes {
          commit {
            oid
            committedDate
            statusCheckRollup {
              state
            }
          }
        }
      }
      createdAt
      updatedAt
    }
  }
}
"""

# Query to get all project fields (for setting metadata like Priority, Size, Estimate, dates)
GET_PROJECT_FIELDS_QUERY = """
query($projectId: ID!) {
  node(id: $projectId) {
    ... on ProjectV2 {
      fields(first: 50) {
        nodes {
          ... on ProjectV2Field {
            id
            name
            dataType
          }
          ... on ProjectV2SingleSelectField {
            id
            name
            dataType
            options {
              id
              name
            }
          }
          ... on ProjectV2IterationField {
            id
            name
            dataType
          }
        }
      }
    }
  }
}
"""

# Mutation to update a single select field value (Priority, Size, Status)
UPDATE_SINGLE_SELECT_FIELD_MUTATION = """
mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
  updateProjectV2ItemFieldValue(
    input: {
      projectId: $projectId
      itemId: $itemId
      fieldId: $fieldId
      value: { singleSelectOptionId: $optionId }
    }
  ) {
    projectV2Item {
      id
    }
  }
}
"""

# Mutation to update a number field value (Estimate)
UPDATE_NUMBER_FIELD_MUTATION = """
mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $number: Float!) {
  updateProjectV2ItemFieldValue(
    input: {
      projectId: $projectId
      itemId: $itemId
      fieldId: $fieldId
      value: { number: $number }
    }
  ) {
    projectV2Item {
      id
    }
  }
}
"""

# Mutation to update a date field value (Start date, Target date)
UPDATE_DATE_FIELD_MUTATION = """
mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $date: Date!) {
  updateProjectV2ItemFieldValue(
    input: {
      projectId: $projectId
      itemId: $itemId
      fieldId: $fieldId
      value: { date: $date }
    }
  ) {
    projectV2Item {
      id
    }
  }
}
"""

# Mutation to update a text field value
UPDATE_TEXT_FIELD_MUTATION = """
mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $text: String!) {
  updateProjectV2ItemFieldValue(
    input: {
      projectId: $projectId
      itemId: $itemId
      fieldId: $fieldId
      value: { text: $text }
    }
  ) {
    projectV2Item {
      id
    }
  }
}
"""


# ──────────────────────────────────────────────────────────────────
# Board feature: GraphQL queries for project board display
# ──────────────────────────────────────────────────────────────────

# Query to list projects with full status field options (colors, descriptions)
BOARD_LIST_PROJECTS_QUERY = """
query($login: String!, $first: Int!) {
  user(login: $login) {
    projectsV2(first: $first) {
      nodes {
        id
        title
        url
        shortDescription
        closed
        field(name: "Status") {
          ... on ProjectV2SingleSelectField {
            id
            options {
              id
              name
              color
              description
            }
          }
        }
      }
    }
  }
}
"""

# Query to get all project items with custom field values for board display
BOARD_GET_PROJECT_ITEMS_QUERY = """
query($projectId: ID!, $first: Int!, $after: String) {
  node(id: $projectId) {
    ... on ProjectV2 {
      title
      url
      shortDescription
      owner {
        ... on User { login }
        ... on Organization { login }
      }
      field(name: "Status") {
        ... on ProjectV2SingleSelectField {
          id
          options {
            id
            name
            color
            description
          }
        }
      }
      items(first: $first, after: $after) {
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          id
          fieldValues(first: 20) {
            nodes {
              ... on ProjectV2ItemFieldSingleSelectValue {
                name
                optionId
                field { ... on ProjectV2FieldCommon { name } }
                color
              }
              ... on ProjectV2ItemFieldNumberValue {
                number
                field { ... on ProjectV2FieldCommon { name } }
              }
            }
          }
          content {
            ... on DraftIssue {
              title
              body
            }
            ... on Issue {
              id
              number
              title
              body
              url
              assignees(first: 10) {
                nodes {
                  login
                  avatarUrl
                }
              }
              repository {
                owner { login }
                name
              }
              timelineItems(itemTypes: [CONNECTED_EVENT, CROSS_REFERENCED_EVENT], first: 50) {
                nodes {
                  ... on ConnectedEvent {
                    subject {
                      ... on PullRequest {
                        id
                        number
                        title
                        state
                        url
                      }
                    }
                  }
                  ... on CrossReferencedEvent {
                    source {
                      ... on PullRequest {
                        id
                        number
                        title
                        state
                        url
                      }
                    }
                  }
                }
              }
            }
            ... on PullRequest {
              id
              number
              title
              body
              url
              state
              assignees(first: 10) {
                nodes {
                  login
                  avatarUrl
                }
              }
              repository {
                owner { login }
                name
              }
            }
          }
        }
      }
    }
  }
}
"""


class GitHubProjectsService:
    """Service for interacting with GitHub Projects V2 API."""

    def __init__(self):
        self._client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()

    # ──────────────────────────────────────────────────────────────────
    # T057: Rate limit handling with exponential backoff
    # ──────────────────────────────────────────────────────────────────
    async def _request_with_retry(
        self,
        method: str,
        url: str,
        headers: dict,
        json: dict | None = None,
    ) -> httpx.Response:
        """
        Make HTTP request with exponential backoff on rate limits.

        Args:
            method: HTTP method (GET, POST, PATCH, etc.)
            url: Request URL
            headers: Request headers
            json: Optional JSON body

        Returns:
            Response object

        Raises:
            httpx.HTTPStatusError: If request fails after retries
        """
        backoff = INITIAL_BACKOFF_SECONDS

        for attempt in range(MAX_RETRIES + 1):
            try:
                if method.upper() == "GET":
                    response = await self._client.get(url, headers=headers)
                elif method.upper() == "POST":
                    response = await self._client.post(url, json=json, headers=headers)
                elif method.upper() == "PATCH":
                    response = await self._client.patch(url, json=json, headers=headers)
                else:
                    raise ValueError(f"Unsupported method: {method}")

                # Check for rate limit
                if response.status_code == 403:
                    remaining = response.headers.get("X-RateLimit-Remaining", "0")
                    if remaining == "0":
                        reset_time = int(response.headers.get("X-RateLimit-Reset", "0"))
                        wait_seconds = max(reset_time - int(datetime.utcnow().timestamp()), backoff)
                        wait_seconds = min(wait_seconds, MAX_BACKOFF_SECONDS)

                        logger.warning(
                            "Rate limited. Waiting %d seconds before retry %d/%d",
                            wait_seconds,
                            attempt + 1,
                            MAX_RETRIES,
                        )
                        await asyncio.sleep(wait_seconds)
                        backoff = min(backoff * 2, MAX_BACKOFF_SECONDS)
                        continue

                response.raise_for_status()
                return response

            except httpx.HTTPStatusError as e:
                if e.response.status_code in (429, 503) and attempt < MAX_RETRIES:
                    logger.warning(
                        "Request failed with %d. Retrying in %d seconds (%d/%d)",
                        e.response.status_code,
                        backoff,
                        attempt + 1,
                        MAX_RETRIES,
                    )
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, MAX_BACKOFF_SECONDS)
                else:
                    raise

        raise httpx.HTTPStatusError(
            "Max retries exceeded",
            request=httpx.Request("GET", ""),  # type: ignore[arg-type]
            response=httpx.Response(500),
        )

    async def _graphql(
        self,
        access_token: str,
        query: str,
        variables: dict,
        extra_headers: dict | None = None,
    ) -> dict:
        """
        Execute GraphQL query against GitHub API.

        Args:
            access_token: GitHub OAuth access token
            query: GraphQL query string
            variables: Query variables
            extra_headers: Optional extra headers (e.g., for Copilot assignment)

        Returns:
            GraphQL response data
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if extra_headers:
            headers.update(extra_headers)

        response = await self._client.post(
            GITHUB_GRAPHQL_URL,
            json={"query": query, "variables": variables},
            headers=headers,
        )
        response.raise_for_status()
        result = response.json()

        if "errors" in result:
            error_msg = "; ".join(e.get("message", str(e)) for e in result["errors"])
            raise ValueError(f"GraphQL error: {error_msg}")

        return result.get("data", {})

    async def list_user_projects(
        self, access_token: str, username: str, limit: int = 20
    ) -> list[GitHubProject]:
        """
        List projects owned by a user.

        Args:
            access_token: GitHub OAuth access token
            username: GitHub username
            limit: Maximum number of projects to return

        Returns:
            List of GitHubProject objects
        """
        data = await self._graphql(
            access_token,
            LIST_USER_PROJECTS_QUERY,
            {"login": username, "first": limit},
        )

        user_data = data.get("user")
        if not user_data:
            return []

        return self._parse_projects(
            user_data.get("projectsV2", {}).get("nodes", []),
            owner_login=username,
            project_type=ProjectType.USER,
        )

    async def list_org_projects(
        self, access_token: str, org: str, limit: int = 20
    ) -> list[GitHubProject]:
        """
        List projects owned by an organization.

        Args:
            access_token: GitHub OAuth access token
            org: Organization login name
            limit: Maximum number of projects to return

        Returns:
            List of GitHubProject objects
        """
        data = await self._graphql(
            access_token,
            LIST_ORG_PROJECTS_QUERY,
            {"login": org, "first": limit},
        )

        org_data = data.get("organization")
        if not org_data:
            return []

        return self._parse_projects(
            org_data.get("projectsV2", {}).get("nodes", []),
            owner_login=org,
            project_type=ProjectType.ORGANIZATION,
        )

    def _parse_projects(
        self, nodes: list[dict], owner_login: str, project_type: ProjectType
    ) -> list[GitHubProject]:
        """Parse GraphQL project nodes into GitHubProject models."""
        projects = []

        for node in nodes:
            if not node or node.get("closed"):
                continue

            # Parse status field
            status_columns = []
            status_field = node.get("field")
            if status_field:
                for option in status_field.get("options", []):
                    status_columns.append(
                        StatusColumn(
                            field_id=status_field["id"],
                            name=option["name"],
                            option_id=option["id"],
                            color=option.get("color"),
                        )
                    )

            # Default status columns if none found
            if not status_columns:
                from src.constants import DEFAULT_STATUS_COLUMNS

                status_columns = [
                    StatusColumn(field_id="", name=name, option_id="")
                    for name in DEFAULT_STATUS_COLUMNS
                ]

            projects.append(
                GitHubProject(
                    project_id=node["id"],
                    owner_id="",  # Not available in this query
                    owner_login=owner_login,
                    name=node["title"],
                    type=project_type,
                    url=node["url"],
                    description=node.get("shortDescription"),
                    status_columns=status_columns,
                    item_count=node.get("items", {}).get("totalCount"),
                    cached_at=datetime.utcnow(),
                )
            )

        return projects

    async def get_project_items(
        self, access_token: str, project_id: str, limit: int = 100
    ) -> list[Task]:
        """
        Get items (tasks) from a project with pagination support.

        Args:
            access_token: GitHub OAuth access token
            project_id: GitHub Project V2 node ID
            limit: Maximum number of items per page (default 100)

        Returns:
            List of Task objects
        """
        all_tasks = []
        has_next_page = True
        after = None

        while has_next_page:
            data = await self._graphql(
                access_token,
                GET_PROJECT_ITEMS_QUERY,
                {"projectId": project_id, "first": limit, "after": after},
            )

            node = data.get("node")
            if not node:
                break

            items_data = node.get("items", {})
            items = items_data.get("nodes", [])
            page_info = items_data.get("pageInfo", {})

            for item in items:
                if not item:
                    continue

                content = item.get("content", {})
                if not content:
                    continue

                status_value = item.get("fieldValueByName", {})

                # Extract repository info if available
                repo_info = content.get("repository", {})
                repo_owner = repo_info.get("owner", {}).get("login") if repo_info else None
                repo_name = repo_info.get("name") if repo_info else None

                all_tasks.append(
                    Task(
                        project_id=project_id,
                        github_item_id=item["id"],
                        github_content_id=content.get("id"),
                        github_issue_id=(content.get("id") if content.get("number") else None),
                        issue_number=content.get("number"),
                        repository_owner=repo_owner,
                        repository_name=repo_name,
                        title=content.get("title", "Untitled"),
                        description=content.get("body"),
                        status=(status_value.get("name", "Todo") if status_value else "Todo"),
                        status_option_id=(status_value.get("optionId", "") if status_value else ""),
                    )
                )

            has_next_page = page_info.get("hasNextPage", False)
            after = page_info.get("endCursor")

            # Safety check to prevent infinite loops
            if not after:
                break

        logger.info("Fetched %d total tasks from project %s", len(all_tasks), project_id)
        return all_tasks

    # ──────────────────────────────────────────────────────────────────
    # Board feature methods
    # ──────────────────────────────────────────────────────────────────

    async def list_board_projects(self, access_token: str, username: str, limit: int = 20) -> list:
        """
        List projects with full status field configuration for board display.

        Args:
            access_token: GitHub OAuth access token
            username: GitHub username
            limit: Maximum number of projects

        Returns:
            List of BoardProject objects with status field options
        """
        from src.models.board import BoardProject, StatusField, StatusOption

        data = await self._graphql(
            access_token,
            BOARD_LIST_PROJECTS_QUERY,
            {"login": username, "first": limit},
        )

        user_data = data.get("user")
        if not user_data:
            return []

        projects = []
        for node in user_data.get("projectsV2", {}).get("nodes", []):
            if not node or node.get("closed"):
                continue

            status_field_data = node.get("field")
            if not status_field_data:
                continue  # Skip projects without a Status field

            options = []
            for opt in status_field_data.get("options", []):
                options.append(
                    StatusOption(
                        option_id=opt["id"],
                        name=opt["name"],
                        color=opt.get("color", "GRAY"),
                        description=opt.get("description"),
                    )
                )

            projects.append(
                BoardProject(
                    project_id=node["id"],
                    name=node["title"],
                    description=node.get("shortDescription"),
                    url=node["url"],
                    owner_login=username,
                    status_field=StatusField(
                        field_id=status_field_data["id"],
                        options=options,
                    ),
                )
            )

        return projects

    async def get_board_data(self, access_token: str, project_id: str, limit: int = 100):
        """
        Get full board data for a project: items with custom fields and linked PRs.

        Args:
            access_token: GitHub OAuth access token
            project_id: GitHub Project V2 node ID
            limit: Maximum items per page

        Returns:
            BoardDataResponse with project metadata and columns
        """
        from src.models.board import (
            Assignee,
            BoardColumn,
            BoardDataResponse,
            BoardItem,
            BoardProject,
            ContentType,
            CustomFieldValue,
            LinkedPR,
            PRState,
            Repository,
            StatusColor,
            StatusField,
            StatusOption,
            SubIssue,
        )

        all_items: list[BoardItem] = []
        has_next_page = True
        after = None
        project_meta = None

        while has_next_page:
            data = await self._graphql(
                access_token,
                BOARD_GET_PROJECT_ITEMS_QUERY,
                {"projectId": project_id, "first": limit, "after": after},
            )

            node = data.get("node")
            if not node:
                break

            # Parse project metadata on first page
            if project_meta is None:
                status_field_data = node.get("field")
                if not status_field_data:
                    raise ValueError(f"Project {project_id} has no Status field")

                status_options = [
                    StatusOption(
                        option_id=opt["id"],
                        name=opt["name"],
                        color=opt.get("color", "GRAY"),
                        description=opt.get("description"),
                    )
                    for opt in status_field_data.get("options", [])
                ]

                owner_data = node.get("owner", {})
                owner_login = owner_data.get("login", "")

                project_meta = BoardProject(
                    project_id=project_id,
                    name=node.get("title", ""),
                    description=node.get("shortDescription"),
                    url=node.get("url", ""),
                    owner_login=owner_login,
                    status_field=StatusField(
                        field_id=status_field_data["id"],
                        options=status_options,
                    ),
                )

            items_data = node.get("items", {})
            page_info = items_data.get("pageInfo", {})

            for item in items_data.get("nodes", []):
                if not item:
                    continue

                content = item.get("content", {})
                if not content:
                    continue

                # Parse field values (Status, Priority, Size, Estimate)
                field_values = item.get("fieldValues", {}).get("nodes", [])
                status_name = ""
                status_option_id = ""
                priority_val = None
                size_val = None
                estimate_val = None

                for fv in field_values:
                    if not fv:
                        continue
                    field_info = fv.get("field", {})
                    field_name = field_info.get("name", "")

                    if field_name == "Status":
                        status_name = fv.get("name", "")
                        status_option_id = fv.get("optionId", "")
                    elif field_name == "Priority":
                        priority_val = CustomFieldValue(
                            name=fv.get("name", ""),
                            color=fv.get("color"),
                        )
                    elif field_name == "Size":
                        size_val = CustomFieldValue(
                            name=fv.get("name", ""),
                            color=fv.get("color"),
                        )
                    elif field_name == "Estimate":
                        num = fv.get("number")
                        if num is not None:
                            estimate_val = float(num)

                # Determine content type
                if content.get("number") is not None and "state" in content:
                    content_type = ContentType.PULL_REQUEST
                elif content.get("number") is not None:
                    content_type = ContentType.ISSUE
                else:
                    content_type = ContentType.DRAFT_ISSUE

                # Parse assignees
                assignees = []
                for assignee_node in content.get("assignees", {}).get("nodes", []):
                    if assignee_node:
                        assignees.append(
                            Assignee(
                                login=assignee_node["login"],
                                avatar_url=assignee_node.get("avatarUrl", ""),
                            )
                        )

                # Parse repository
                repo_data = content.get("repository")
                repository = None
                if repo_data:
                    repository = Repository(
                        owner=repo_data.get("owner", {}).get("login", ""),
                        name=repo_data.get("name", ""),
                    )

                # Parse linked PRs from timeline events
                linked_prs: list[LinkedPR] = []
                seen_pr_ids: set[str] = set()
                timeline = content.get("timelineItems", {}).get("nodes", [])
                for event in timeline:
                    if not event:
                        continue
                    pr_data = event.get("subject") or event.get("source")
                    if pr_data and pr_data.get("id"):
                        pr_id = pr_data["id"]
                        if pr_id not in seen_pr_ids:
                            seen_pr_ids.add(pr_id)
                            pr_state_raw = pr_data.get("state", "OPEN").upper()
                            if pr_state_raw == "MERGED":
                                pr_state = PRState.MERGED
                            elif pr_state_raw == "CLOSED":
                                pr_state = PRState.CLOSED
                            else:
                                pr_state = PRState.OPEN

                            linked_prs.append(
                                LinkedPR(
                                    pr_id=pr_id,
                                    number=pr_data.get("number", 0),
                                    title=pr_data.get("title", ""),
                                    state=pr_state,
                                    url=pr_data.get("url", ""),
                                )
                            )

                all_items.append(
                    BoardItem(
                        item_id=item["id"],
                        content_id=content.get("id"),
                        content_type=content_type,
                        title=content.get("title", "Untitled"),
                        number=content.get("number"),
                        repository=repository,
                        url=content.get("url"),
                        body=content.get("body"),
                        status=status_name or "No Status",
                        status_option_id=status_option_id,
                        assignees=assignees,
                        priority=priority_val,
                        size=size_val,
                        estimate=estimate_val,
                        linked_prs=linked_prs,
                    )
                )

            has_next_page = page_info.get("hasNextPage", False)
            after = page_info.get("endCursor")
            if not after:
                break

        if project_meta is None:
            raise ValueError(f"Project not found: {project_id}")

        # Fetch sub-issues for each issue item
        for board_item in all_items:
            if (
                board_item.content_type == ContentType.ISSUE
                and board_item.number is not None
                and board_item.repository
            ):
                try:
                    raw_sub_issues = await self.get_sub_issues(
                        access_token=access_token,
                        owner=board_item.repository.owner,
                        repo=board_item.repository.name,
                        issue_number=board_item.number,
                    )
                    for si in raw_sub_issues:
                        si_assignees = [
                            Assignee(
                                login=a.get("login", ""),
                                avatar_url=a.get("avatar_url", ""),
                            )
                            for a in si.get("assignees", [])
                            if isinstance(a, dict)
                        ]
                        # Detect agent from title: "[speckit.implement] Feature title"
                        si_title = si.get("title", "")
                        si_agent = None
                        if si_title.startswith("[") and "]" in si_title:
                            si_agent = si_title[1 : si_title.index("]")]
                        board_item.sub_issues.append(
                            SubIssue(
                                id=si.get("node_id", ""),
                                number=si.get("number", 0),
                                title=si_title,
                                url=si.get("html_url", ""),
                                state=si.get("state", "open"),
                                assigned_agent=si_agent,
                                assignees=si_assignees,
                            )
                        )
                except Exception as e:
                    logger.debug(
                        "Failed to fetch sub-issues for item #%s: %s",
                        board_item.number,
                        e,
                    )

        # Group items into columns by status
        status_options = project_meta.status_field.options

        # Also create a "No Status" column for items without a status
        columns_map: dict[str, list[BoardItem]] = {opt.option_id: [] for opt in status_options}
        no_status_items: list[BoardItem] = []

        for board_item in all_items:
            if board_item.status_option_id in columns_map:
                columns_map[board_item.status_option_id].append(board_item)
            else:
                no_status_items.append(board_item)

        columns: list[BoardColumn] = []
        for opt in status_options:
            col_items = columns_map[opt.option_id]
            estimate_total = sum(it.estimate or 0.0 for it in col_items)
            columns.append(
                BoardColumn(
                    status=opt,
                    items=col_items,
                    item_count=len(col_items),
                    estimate_total=estimate_total,
                )
            )

        # Append no-status column if there are unclassified items
        if no_status_items:
            no_status_option = StatusOption(
                option_id="__no_status__",
                name="No Status",
                color=StatusColor.GRAY,
            )
            estimate_total = sum(it.estimate or 0.0 for it in no_status_items)
            columns.append(
                BoardColumn(
                    status=no_status_option,
                    items=no_status_items,
                    item_count=len(no_status_items),
                    estimate_total=estimate_total,
                )
            )

        logger.info(
            "Board data for project %s: %d items across %d columns",
            project_id,
            len(all_items),
            len(columns),
        )

        return BoardDataResponse(project=project_meta, columns=columns)

    async def create_draft_item(
        self,
        access_token: str,
        project_id: str,
        title: str,
        description: str | None = None,
    ) -> str:
        """
        Create a draft issue item in a project.

        Args:
            access_token: GitHub OAuth access token
            project_id: GitHub Project V2 node ID
            title: Task title
            description: Task description/body

        Returns:
            Created item ID
        """
        data = await self._graphql(
            access_token,
            CREATE_DRAFT_ITEM_MUTATION,
            {"projectId": project_id, "title": title, "body": description},
        )

        item_data = data.get("addProjectV2DraftIssue", {}).get("projectItem", {})
        return item_data.get("id", "")

    async def update_item_status(
        self,
        access_token: str,
        project_id: str,
        item_id: str,
        field_id: str,
        option_id: str,
    ) -> bool:
        """
        Update an item's status field.

        Args:
            access_token: GitHub OAuth access token
            project_id: GitHub Project V2 node ID
            item_id: Project item node ID
            field_id: Status field node ID
            option_id: Status option ID

        Returns:
            True if update succeeded
        """
        # Add 2 second delay before status update (rate limiting / UX improvement)
        await asyncio.sleep(2)

        data = await self._graphql(
            access_token,
            UPDATE_ITEM_STATUS_MUTATION,
            {
                "projectId": project_id,
                "itemId": item_id,
                "fieldId": field_id,
                "optionId": option_id,
            },
        )

        return bool(data.get("updateProjectV2ItemFieldValue", {}).get("projectV2Item"))

    # ──────────────────────────────────────────────────────────────────
    # Issue Creation and Project Attachment (T018-T020, T036-T037, T043)
    # ──────────────────────────────────────────────────────────────────

    async def create_issue(
        self,
        access_token: str,
        owner: str,
        repo: str,
        title: str,
        body: str,
        labels: list[str] | None = None,
    ) -> dict:
        """
        Create a GitHub Issue using REST API (T018).

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            title: Issue title
            body: Issue body (markdown)
            labels: Optional list of label names

        Returns:
            Dict with issue details: id, node_id, number, html_url
        """
        response = await self._client.post(
            f"https://api.github.com/repos/{owner}/{repo}/issues",
            json={
                "title": title,
                "body": body,
                "labels": labels or [],
            },
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        response.raise_for_status()
        issue = response.json()

        logger.info("Created issue #%d in %s/%s", issue["number"], owner, repo)
        return issue

    async def update_issue_body(
        self,
        access_token: str,
        owner: str,
        repo: str,
        issue_number: int,
        body: str,
    ) -> bool:
        """
        Update a GitHub Issue's body text using REST API.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            body: New issue body (markdown)

        Returns:
            True if update succeeded
        """
        try:
            response = await self._client.patch(
                f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}",
                json={"body": body},
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )
            response.raise_for_status()
            logger.info("Updated body of issue #%d in %s/%s", issue_number, owner, repo)
            return True
        except Exception as e:
            logger.error("Failed to update issue #%d body: %s", issue_number, e)
            return False

    async def update_issue_state(
        self,
        access_token: str,
        owner: str,
        repo: str,
        issue_number: int,
        state: str,
        state_reason: str | None = None,
        labels_add: list[str] | None = None,
        labels_remove: list[str] | None = None,
    ) -> bool:
        """
        Update a GitHub Issue's state (open/closed) and optionally manage labels.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            state: "open" or "closed"
            state_reason: Optional reason ("completed", "not_planned", "reopened")
            labels_add: Labels to add
            labels_remove: Labels to remove

        Returns:
            True if update succeeded
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        try:
            # Update state
            payload: dict = {"state": state}
            if state_reason:
                payload["state_reason"] = state_reason

            response = await self._client.patch(
                f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()

            # Add labels
            if labels_add:
                await self._client.post(
                    f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/labels",
                    json={"labels": labels_add},
                    headers=headers,
                )

            # Remove labels
            if labels_remove:
                for label in labels_remove:
                    await self._client.delete(
                        f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/labels/{label}",
                        headers=headers,
                    )

            logger.info(
                "Updated issue #%d state to '%s' in %s/%s",
                issue_number, state, owner, repo,
            )
            return True
        except Exception as e:
            logger.warning("Failed to update issue #%d state: %s", issue_number, e)
            return False

    async def add_issue_to_project(
        self,
        access_token: str,
        project_id: str,
        issue_node_id: str,
    ) -> str:
        """
        Add an existing issue to a GitHub Project (T020).

        Args:
            access_token: GitHub OAuth access token
            project_id: GitHub Project V2 node ID
            issue_node_id: GitHub Issue node ID

        Returns:
            Project item ID
        """
        data = await self._graphql(
            access_token,
            ADD_ISSUE_TO_PROJECT_MUTATION,
            {"projectId": project_id, "contentId": issue_node_id},
        )

        item_id = data.get("addProjectV2ItemById", {}).get("item", {}).get("id", "")
        logger.info("Added issue %s to project, item_id: %s", issue_node_id, item_id)
        return item_id

    async def assign_issue(
        self,
        access_token: str,
        owner: str,
        repo: str,
        issue_number: int,
        assignees: list[str],
    ) -> bool:
        """
        Assign users to a GitHub Issue (T036).

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            assignees: List of usernames to assign

        Returns:
            True if assignment succeeded
        """
        response = await self._client.patch(
            f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}",
            json={"assignees": assignees},
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )

        success = response.status_code == 200
        if success:
            logger.info("Assigned %s to issue #%d", assignees, issue_number)
        else:
            logger.warning(
                "Failed to assign %s to issue #%d: %s",
                assignees,
                issue_number,
                response.text,
            )

        return success

    async def get_copilot_bot_id(
        self,
        access_token: str,
        owner: str,
        repo: str,
    ) -> tuple[str | None, str | None]:
        """
        Get the Copilot bot actor ID for a repository using suggestedActors API.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name

        Returns:
            Tuple of (Copilot bot node ID, repository node ID) or (None, None) if not available
        """
        try:
            data = await self._graphql(
                access_token,
                GET_SUGGESTED_ACTORS_QUERY,
                {"owner": owner, "name": repo},
                extra_headers={
                    "GraphQL-Features": "issues_copilot_assignment_api_support,coding_agent_model_selection"
                },
            )

            repository = data.get("repository", {})
            repo_id = repository.get("id")
            actors = repository.get("suggestedActors", {}).get("nodes", [])

            # Look for the Copilot SWE agent bot
            for actor in actors:
                login = actor.get("login", "")
                typename = actor.get("__typename", "")
                if login == "copilot-swe-agent" and typename == "Bot":
                    bot_id = actor.get("id")
                    logger.info("Found Copilot bot: %s (ID: %s)", login, bot_id)
                    return bot_id, repo_id

            logger.warning(
                "Copilot bot not available for %s/%s (actors: %s)",
                owner,
                repo,
                [a.get("login") for a in actors],
            )
            return None, repo_id
        except Exception as e:
            logger.warning("Failed to get Copilot bot ID: %s", e)
            return None, None

    async def get_issue_with_comments(
        self,
        access_token: str,
        owner: str,
        repo: str,
        issue_number: int,
    ) -> dict:
        """
        Fetch issue details including title, body, and all comments.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number

        Returns:
            Dict with issue title, body, and comments list
        """
        try:
            data = await self._graphql(
                access_token,
                GET_ISSUE_WITH_COMMENTS_QUERY,
                {"owner": owner, "name": repo, "number": issue_number},
            )

            issue = data.get("repository", {}).get("issue", {})
            comments = issue.get("comments", {}).get("nodes", [])

            return {
                "title": issue.get("title", ""),
                "body": issue.get("body", ""),
                "comments": [
                    {
                        "author": c.get("author", {}).get("login", "unknown"),
                        "body": c.get("body", ""),
                        "created_at": c.get("createdAt", ""),
                    }
                    for c in comments
                ],
            }
        except Exception as e:
            logger.error("Failed to fetch issue #%d with comments: %s", issue_number, e)
            return {"title": "", "body": "", "comments": []}

    def format_issue_context_as_prompt(
        self,
        issue_data: dict,
        agent_name: str = "",
        existing_pr: dict | None = None,
    ) -> str:
        """
        Format issue details (title, body, comments) as a prompt for the custom agent.

        When ``existing_pr`` is provided, instructions tell the agent to push
        commits to the existing PR branch instead of creating a new PR.
        The existing PR instructions are placed FIRST so the agent prioritises
        branch reuse over creating a new pull request.

        Args:
            issue_data: Dict with title, body, and comments from get_issue_with_comments
            agent_name: Name of the custom agent (e.g., 'speckit.specify')
            existing_pr: Optional dict with ``number``, ``head_ref``, ``url``
                         of an existing PR to reuse

        Returns:
            Formatted string suitable as custom instructions for the agent
        """
        parts = []

        # ── Existing PR context (for agents working on an existing branch) ───
        if existing_pr:
            branch = existing_pr.get("head_ref", "")
            pr_num = existing_pr.get("number", "")
            pr_url = existing_pr.get("url", "")
            is_draft = existing_pr.get("is_draft", True)
            draft_label = " (Draft / Work In Progress)" if is_draft else ""
            parts.append(
                "## Related Pull Request\n\n"
                f"A pull request{draft_label} already exists for this issue.\n"
                f"- **PR:** #{pr_num} — {pr_url}\n"
                f"- **Branch:** `{branch}`\n\n"
                "Previous agent work exists on this branch. Your work will be "
                "created as a child branch and automatically merged back.\n\n"
                "---"
            )

        # ── Issue context ────────────────────────────────────────────────
        # Add title
        title = issue_data.get("title", "")
        if title:
            parts.append(f"## Issue Title\n{title}")

        # Add description/body
        body = issue_data.get("body", "")
        if body:
            parts.append(f"## Issue Description\n{body}")

        # Add comments/discussions
        comments = issue_data.get("comments", [])
        if comments:
            parts.append("## Comments and Discussion")
            for idx, comment in enumerate(comments, 1):
                author = comment.get("author", "unknown")
                comment_body = comment.get("body", "")
                created_at = comment.get("created_at", "")
                parts.append(f"### Comment {idx} by @{author} ({created_at})\n{comment_body}")

        # ── Output instructions ──────────────────────────────────────────
        if agent_name:
            # Map each agent to the specific .md file(s) it produces.
            # All agents are listed; implement has no .md outputs.
            agent_files = {
                "speckit.specify": ["spec.md"],
                "speckit.plan": ["plan.md"],
                "speckit.tasks": ["tasks.md"],
                "speckit.implement": [],
            }
            files = agent_files.get(agent_name, [])

            if files:
                file_list = ", ".join(f"`{f}`" for f in files)
                branch_note = f" on branch `{existing_pr['head_ref']}`" if existing_pr else ""
                parts.append(
                    "## Output Instructions\n"
                    "IMPORTANT: When you are done generating your output, ensure the following "
                    f"file(s) are committed to the PR branch{branch_note}: {file_list}.\n\n"
                    "The system will automatically detect your PR completion, extract the "
                    "markdown file content, and post it as an issue comment. You do NOT need to "
                    "post comments yourself — just commit the files and complete your PR work."
                )
            else:
                branch_note = f" (`{existing_pr['head_ref']}`)" if existing_pr else ""
                parts.append(
                    "## Output Instructions\n"
                    f"IMPORTANT: Complete your work and commit all changes to the PR branch{branch_note}.\n\n"
                    "The system will automatically detect your PR completion and advance "
                    "the workflow. You do NOT need to post any completion comments."
                )

        return "\n\n".join(parts)

    async def check_agent_completion_comment(
        self,
        access_token: str,
        owner: str,
        repo: str,
        issue_number: int,
        agent_name: str,
    ) -> bool:
        """
        Check if an agent has posted a completion comment on the issue.

        Scans issue comments for a comment body containing the pattern:
        ``<agent_name>: Done!``

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            issue_number: GitHub issue number
            agent_name: Agent name to look for (e.g., 'speckit.specify')

        Returns:
            True if a completion comment from the agent was found
        """
        try:
            issue_data = await self.get_issue_with_comments(
                access_token=access_token,
                owner=owner,
                repo=repo,
                issue_number=issue_number,
            )

            if not issue_data:
                logger.warning("Could not fetch issue #%d for agent completion check", issue_number)
                return False

            comments = issue_data.get("comments", [])
            marker = f"{agent_name}: Done!"

            # Scan comments in reverse chronological order for the most recent marker
            for comment in reversed(comments):
                body = comment.get("body", "")
                if marker in body:
                    logger.info(
                        "Found completion marker for agent '%s' on issue #%d",
                        agent_name,
                        issue_number,
                    )
                    return True

            return False

        except Exception as e:
            logger.error(
                "Error checking agent completion comment for issue #%d: %s",
                issue_number,
                e,
            )
            return False

    async def unassign_copilot_from_issue(
        self,
        access_token: str,
        owner: str,
        repo: str,
        issue_number: int,
    ) -> bool:
        """
        Unassign GitHub Copilot from an issue.

        This is needed before re-assigning Copilot with a different custom agent,
        as the API may fail if Copilot is already assigned.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number

        Returns:
            True if unassignment succeeded or Copilot was not assigned
        """
        try:
            import asyncio
            import json as json_mod

            url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/assignees"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
                "Content-Type": "application/json",
                "X-GitHub-Api-Version": "2022-11-28",
            }

            # Use REST API to remove Copilot assignee
            # The assignee login for Copilot is "copilot-swe-agent[bot]"
            # httpx's delete() doesn't support json= param, so use request()
            response = await self._client.request(
                "DELETE",
                url,
                content=json_mod.dumps({"assignees": ["copilot-swe-agent[bot]"]}),
                headers=headers,
            )

            if response.status_code == 200:
                # Verify Copilot was actually removed from assignees
                result = response.json()
                remaining = [a.get("login", "") for a in result.get("assignees", [])]
                copilot_gone = not any("copilot" in a.lower() for a in remaining)
                logger.info(
                    "Unassigned Copilot from issue #%d (remaining assignees: %s, copilot_removed: %s)",
                    issue_number,
                    remaining,
                    copilot_gone,
                )
                # Give GitHub a moment to propagate the unassignment
                await asyncio.sleep(2)
                return copilot_gone
            elif response.status_code == 404:
                # Copilot was not assigned
                logger.debug(
                    "Copilot was not assigned to issue #%d, nothing to unassign",
                    issue_number,
                )
                return True
            else:
                logger.warning(
                    "Failed to unassign Copilot from issue #%d - Status: %s, Response: %s",
                    issue_number,
                    response.status_code,
                    response.text[:500] if response.text else "empty",
                )
                # Don't fail - we'll try to assign anyway
                return True

        except Exception as e:
            logger.error("Error unassigning Copilot from issue #%d: %s", issue_number, e)
            # Don't fail - we'll try to assign anyway
            return True

    async def is_copilot_assigned_to_issue(
        self,
        access_token: str,
        owner: str,
        repo: str,
        issue_number: int,
    ) -> bool:
        """
        Check if GitHub Copilot is currently assigned to an issue.

        When Copilot finishes its work, it unassigns itself from the issue.
        This can be used as a completion signal for agents working on existing branches.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number

        Returns:
            True if Copilot is currently assigned
        """
        try:
            url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
            response = await self._client.get(url, headers=headers)
            if response.status_code != 200:
                logger.warning(
                    "Failed to check assignees for issue #%d: status %d",
                    issue_number,
                    response.status_code,
                )
                return True  # Assume still assigned on error (conservative)

            issue_data = response.json()
            assignees = issue_data.get("assignees", [])
            for assignee in assignees:
                login = (assignee.get("login") or "").lower()
                if "copilot" in login:
                    return True

            return False

        except Exception as e:
            logger.warning("Error checking Copilot assignment for issue #%d: %s", issue_number, e)
            return True  # Assume still assigned on error (conservative)

    async def assign_copilot_to_issue(
        self,
        access_token: str,
        owner: str,
        repo: str,
        issue_node_id: str,
        issue_number: int | None = None,
        base_ref: str = "main",
        custom_agent: str = "",
        custom_instructions: str = "",
    ) -> bool:
        """
        Assign GitHub Copilot to an issue using GraphQL API with agent assignment.

        Uses the GraphQL ``addAssigneesToAssignable`` mutation with the
        ``agentAssignment`` input which explicitly supports ``customAgent``.
        Falls back to the REST API if GraphQL fails.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            issue_node_id: Issue node ID (for GraphQL approach)
            issue_number: Issue number (used for REST fallback and logging)
            base_ref: Branch to base the PR on (default: main)
            custom_agent: Custom agent name (e.g., 'speckit.specify')
            custom_instructions: Custom instructions/prompt for the agent

        Returns:
            True if assignment succeeded
        """
        logger.info(
            "Assigning Copilot to issue #%s (node=%s) with custom_agent='%s'",
            issue_number,
            issue_node_id,
            custom_agent,
        )

        # If this is a custom agent assignment, unassign Copilot first — but
        # ONLY if Copilot is currently assigned. Skipping this for new issues
        # avoids a race condition where the recovery loop sees "Copilot NOT
        # assigned" between the unassign and re-assign steps.
        if custom_agent and issue_number:
            is_assigned = await self.is_copilot_assigned_to_issue(
                access_token=access_token,
                owner=owner,
                repo=repo,
                issue_number=issue_number,
            )
            if is_assigned:
                await self.unassign_copilot_from_issue(
                    access_token=access_token,
                    owner=owner,
                    repo=repo,
                    issue_number=issue_number,
                )

        # Prefer GraphQL — it explicitly supports customAgent in the schema
        graphql_success = await self._assign_copilot_graphql(
            access_token,
            owner,
            repo,
            issue_node_id,
            base_ref,
            custom_agent,
            custom_instructions,
        )

        if graphql_success:
            return True

        # Fall back to REST API if GraphQL failed
        if not issue_number:
            logger.warning("GraphQL assignment failed and no issue_number for REST fallback")
            return False

        return await self._assign_copilot_rest(
            access_token,
            owner,
            repo,
            issue_number,
            base_ref,
            custom_agent,
            custom_instructions,
        )

    async def _assign_copilot_rest(
        self,
        access_token: str,
        owner: str,
        repo: str,
        issue_number: int,
        base_ref: str = "main",
        custom_agent: str = "",
        custom_instructions: str = "",
    ) -> bool:
        """
        Fallback: Assign GitHub Copilot using REST API.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            base_ref: Branch to base the PR on
            custom_agent: Custom agent name
            custom_instructions: Custom instructions for the agent

        Returns:
            True if assignment succeeded
        """
        try:
            payload = {
                "assignees": ["copilot-swe-agent[bot]"],
                "agent_assignment": {
                    "target_repo": f"{owner}/{repo}",
                    "base_branch": base_ref,
                    "custom_instructions": custom_instructions,
                    "custom_agent": custom_agent,
                    "model": "claude-opus-4.6",
                },
            }

            logger.info(
                "REST fallback: Assigning Copilot to issue #%d with custom_agent='%s'",
                issue_number,
                custom_agent,
            )

            response = await self._client.post(
                f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/assignees",
                json=payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )

            if response.status_code in (200, 201):
                result = response.json()
                assignees = [a.get("login", "") for a in result.get("assignees", [])]
                logger.info(
                    "REST: Assigned Copilot to issue #%d with custom agent '%s', assignees: %s",
                    issue_number,
                    custom_agent,
                    assignees,
                )
                return True
            else:
                logger.error(
                    "REST API failed to assign Copilot to issue #%d - Status: %s, Response: %s",
                    issue_number,
                    response.status_code,
                    response.text[:500] if response.text else "empty",
                )
                return False

        except Exception as e:
            logger.error("REST fallback failed for issue #%d: %s", issue_number, e)
            return False

    async def _assign_copilot_graphql(
        self,
        access_token: str,
        owner: str,
        repo: str,
        issue_node_id: str,
        base_ref: str = "main",
        custom_agent: str = "",
        custom_instructions: str = "",
    ) -> bool:
        """
        Primary: Assign GitHub Copilot using GraphQL API.

        Uses the ``addAssigneesToAssignable`` mutation with ``agentAssignment``
        input which explicitly supports the ``customAgent`` field in the schema.
        This is preferred over the REST API to ensure custom agent routing.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            issue_node_id: Issue node ID
            base_ref: Branch to base the PR on
            custom_agent: Custom agent name
            custom_instructions: Custom instructions for the agent

        Returns:
            True if assignment succeeded
        """
        # Get Copilot bot ID and repo ID
        copilot_id, repo_id = await self.get_copilot_bot_id(access_token, owner, repo)
        if not copilot_id:
            logger.warning("Cannot assign Copilot - bot not available for %s/%s", owner, repo)
            return False
        if not repo_id:
            logger.warning("Cannot assign Copilot - repository ID not found for %s/%s", owner, repo)
            return False

        try:
            # Use GraphQL mutation with special headers for Copilot assignment
            data = await self._graphql(
                access_token,
                ASSIGN_COPILOT_MUTATION,
                {
                    "issueId": issue_node_id,
                    "assigneeIds": [copilot_id],
                    "repoId": repo_id,
                    "baseRef": base_ref,
                    "customInstructions": custom_instructions,
                    "customAgent": custom_agent,
                },
                extra_headers={
                    "GraphQL-Features": "issues_copilot_assignment_api_support,coding_agent_model_selection"
                },
            )

            assignees = (
                data.get("addAssigneesToAssignable", {})
                .get("assignable", {})
                .get("assignees", {})
                .get("nodes", [])
            )
            assigned_logins = [a.get("login", "") for a in assignees]

            if custom_agent:
                logger.info(
                    "GraphQL: Assigned Copilot with custom agent '%s', assignees: %s",
                    custom_agent,
                    assigned_logins,
                )
            else:
                logger.info("GraphQL: Assigned Copilot to issue, assignees: %s", assigned_logins)

            return True

        except Exception as e:
            logger.error("GraphQL failed to assign Copilot to issue: %s", e)
            return False

    async def validate_assignee(
        self,
        access_token: str,
        owner: str,
        repo: str,
        username: str,
    ) -> bool:
        """
        Check if a user can be assigned to issues in a repository (T037).

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            username: Username to validate

        Returns:
            True if user can be assigned
        """
        response = await self._client.get(
            f"https://api.github.com/repos/{owner}/{repo}/assignees/{username}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )

        # 204 means user can be assigned
        return response.status_code == 204

    async def get_repository_owner(
        self,
        access_token: str,
        owner: str,
        repo: str,
    ) -> str:
        """
        Get the repository owner username (T043).

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner (may be org)
            repo: Repository name

        Returns:
            Owner username
        """
        response = await self._client.get(
            f"https://api.github.com/repos/{owner}/{repo}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        response.raise_for_status()
        repo_data = response.json()

        # Return the owner login
        return repo_data.get("owner", {}).get("login", owner)

    async def get_project_repository(
        self,
        access_token: str,
        project_id: str,
    ) -> tuple[str, str] | None:
        """
        Get the repository associated with a project by examining project items.

        Args:
            access_token: GitHub OAuth access token
            project_id: GitHub Project V2 node ID

        Returns:
            Tuple of (owner, repo_name) or None if no repository found
        """
        data = await self._graphql(
            access_token,
            GET_PROJECT_REPOSITORY_QUERY,
            {"projectId": project_id},
        )

        items = data.get("node", {}).get("items", {}).get("nodes", [])

        for item in items:
            content = item.get("content")
            if content and "repository" in content:
                repo_info = content["repository"]
                owner = repo_info.get("owner", {}).get("login", "")
                name = repo_info.get("name", "")
                if owner and name:
                    logger.info("Found repository %s/%s from project items", owner, name)
                    return owner, name

        logger.warning("No repository found in project %s items", project_id)
        return None

    async def update_item_status_by_name(
        self,
        access_token: str,
        project_id: str,
        item_id: str,
        status_name: str,
    ) -> bool:
        """
        Update an item's status by status name (helper method).

        Args:
            access_token: GitHub OAuth access token
            project_id: GitHub Project V2 node ID
            item_id: Project item node ID
            status_name: Status name (e.g., "Ready", "In Progress")

        Returns:
            True if update succeeded
        """
        # Get project field info
        data = await self._graphql(
            access_token,
            GET_PROJECT_FIELD_QUERY,
            {"projectId": project_id},
        )

        field_data = data.get("node", {}).get("field", {})
        field_id = field_data.get("id")
        options = field_data.get("options", [])

        if not field_id:
            logger.error("Could not find Status field in project %s", project_id)
            return False

        # Find matching option
        option_id = None
        for opt in options:
            if opt.get("name", "").lower() == status_name.lower():
                option_id = opt.get("id")
                break

        if not option_id:
            logger.error(
                "Could not find status option '%s' in project %s",
                status_name,
                project_id,
            )
            return False

        # Update status
        return await self.update_item_status(
            access_token=access_token,
            project_id=project_id,
            item_id=item_id,
            field_id=field_id,
            option_id=option_id,
        )

    async def update_sub_issue_project_status(
        self,
        access_token: str,
        project_id: str,
        sub_issue_node_id: str,
        status_name: str,
    ) -> bool:
        """
        Update a sub-issue's Status field on the project board.

        Sub-issues automatically inherit the parent issue's project, so they
        already have a project item.  This method queries the sub-issue's
        ``projectItems`` connection to find its project-item ID, then delegates
        to ``update_item_status_by_name`` to set the Status column.

        Returns ``True`` on success, ``False`` otherwise.
        """
        query = """
        query($issueId: ID!) {
            node(id: $issueId) {
                ... on Issue {
                    projectItems(first: 10) {
                        nodes {
                            id
                            project { id }
                        }
                    }
                }
            }
        }
        """
        try:
            data = await self._graphql(
                access_token, query, {"issueId": sub_issue_node_id}
            )
        except Exception as exc:
            logger.warning(
                "GraphQL projectItems query failed for sub-issue %s: %s",
                sub_issue_node_id,
                exc,
            )
            return False

        nodes = (
            data.get("node", {})
            .get("projectItems", {})
            .get("nodes", [])
        )

        # Find the project item that belongs to *our* project
        item_id: str | None = None
        for node in nodes:
            if node.get("project", {}).get("id") == project_id:
                item_id = node["id"]
                break

        if not item_id and nodes:
            # Fallback: use the first project item if project_id didn't match
            item_id = nodes[0]["id"]

        if not item_id:
            # Sub-issue is not on the project yet — add it and retry
            logger.info(
                "Sub-issue %s has no project items — adding to project %s first",
                sub_issue_node_id,
                project_id,
            )
            try:
                new_item_id = await self.add_issue_to_project(
                    access_token=access_token,
                    project_id=project_id,
                    issue_node_id=sub_issue_node_id,
                )
                if new_item_id:
                    item_id = new_item_id
                    logger.info(
                        "Added sub-issue %s to project, item_id: %s",
                        sub_issue_node_id,
                        item_id,
                    )
            except Exception as add_err:
                logger.warning(
                    "Failed to add sub-issue %s to project %s: %s",
                    sub_issue_node_id,
                    project_id,
                    add_err,
                )

        if not item_id:
            logger.warning(
                "Sub-issue %s could not be added to project — cannot set status to '%s'",
                sub_issue_node_id,
                status_name,
            )
            return False

        logger.info(
            "Updating sub-issue project board status to '%s' (item %s)",
            status_name,
            item_id,
        )
        return await self.update_item_status_by_name(
            access_token=access_token,
            project_id=project_id,
            item_id=item_id,
            status_name=status_name,
        )

    # ──────────────────────────────────────────────────────────────────
    # Project Field Management (Priority, Size, Estimate, Dates)
    # ──────────────────────────────────────────────────────────────────

    async def get_project_fields(
        self,
        access_token: str,
        project_id: str,
    ) -> dict[str, dict]:
        """
        Get all fields from a project.

        Args:
            access_token: GitHub OAuth access token
            project_id: GitHub Project V2 node ID

        Returns:
            Dict mapping field names to field info (id, dataType, options if applicable)
        """
        try:
            data = await self._graphql(
                access_token,
                GET_PROJECT_FIELDS_QUERY,
                {"projectId": project_id},
            )

            fields = {}
            field_nodes = data.get("node", {}).get("fields", {}).get("nodes", [])

            for field in field_nodes:
                if not field:
                    continue
                name = field.get("name")
                if name:
                    fields[name] = {
                        "id": field.get("id"),
                        "dataType": field.get("dataType"),
                        "options": field.get("options", []),
                    }

            logger.debug("Found %d project fields: %s", len(fields), list(fields.keys()))
            return fields

        except Exception as e:
            logger.error("Failed to get project fields: %s", e)
            return {}

    async def update_project_item_field(
        self,
        access_token: str,
        project_id: str,
        item_id: str,
        field_name: str,
        value: str | float,
        field_type: str = "auto",
    ) -> bool:
        """
        Update a project item's field value.

        Args:
            access_token: GitHub OAuth access token
            project_id: GitHub Project V2 node ID
            item_id: Project item node ID
            field_name: Name of the field to update
            value: Value to set (string for select/text, float for number, date string for date)
            field_type: Type hint: "select", "number", "date", "text", or "auto" to detect

        Returns:
            True if update succeeded
        """
        try:
            # Get project fields
            fields = await self.get_project_fields(access_token, project_id)
            field_info = fields.get(field_name)

            if not field_info:
                logger.warning("Field '%s' not found in project %s", field_name, project_id)
                return False

            field_id = field_info["id"]
            data_type = field_info.get("dataType", "")

            # Determine mutation based on data type
            if data_type == "SINGLE_SELECT" or field_type == "select":
                # Find option ID for the value
                options = field_info.get("options", [])
                option_id = None
                for opt in options:
                    if opt.get("name", "").upper() == str(value).upper():
                        option_id = opt.get("id")
                        break

                if not option_id:
                    logger.warning("Option '%s' not found for field '%s'", value, field_name)
                    return False

                await self._graphql(
                    access_token,
                    UPDATE_SINGLE_SELECT_FIELD_MUTATION,
                    {
                        "projectId": project_id,
                        "itemId": item_id,
                        "fieldId": field_id,
                        "optionId": option_id,
                    },
                )

            elif data_type == "NUMBER" or field_type == "number":
                await self._graphql(
                    access_token,
                    UPDATE_NUMBER_FIELD_MUTATION,
                    {
                        "projectId": project_id,
                        "itemId": item_id,
                        "fieldId": field_id,
                        "number": float(value),
                    },
                )

            elif data_type == "DATE" or field_type == "date":
                await self._graphql(
                    access_token,
                    UPDATE_DATE_FIELD_MUTATION,
                    {
                        "projectId": project_id,
                        "itemId": item_id,
                        "fieldId": field_id,
                        "date": str(value),
                    },
                )

            elif data_type == "TEXT" or field_type == "text":
                await self._graphql(
                    access_token,
                    UPDATE_TEXT_FIELD_MUTATION,
                    {
                        "projectId": project_id,
                        "itemId": item_id,
                        "fieldId": field_id,
                        "text": str(value),
                    },
                )

            else:
                logger.warning("Unsupported field type '%s' for field '%s'", data_type, field_name)
                return False

            logger.info("Updated field '%s' to '%s' for item %s", field_name, value, item_id)
            return True

        except Exception as e:
            logger.error("Failed to update field '%s': %s", field_name, e)
            return False

    async def set_issue_metadata(
        self,
        access_token: str,
        project_id: str,
        item_id: str,
        metadata: dict,
    ) -> dict[str, bool]:
        """
        Set multiple metadata fields on a project item.

        Args:
            access_token: GitHub OAuth access token
            project_id: GitHub Project V2 node ID
            item_id: Project item node ID
            metadata: Dict with keys like priority, size, estimate_hours, start_date, target_date

        Returns:
            Dict mapping field names to success status
        """
        results = {}

        # Standard field mappings (project field name -> metadata key)
        field_mappings = {
            "Priority": ("priority", "select"),
            "Size": ("size", "select"),
            "Estimate": ("estimate_hours", "number"),
            "Start date": ("start_date", "date"),
            "Target date": ("target_date", "date"),
        }

        for field_name, (meta_key, field_type) in field_mappings.items():
            value = metadata.get(meta_key)
            if value:
                success = await self.update_project_item_field(
                    access_token=access_token,
                    project_id=project_id,
                    item_id=item_id,
                    field_name=field_name,
                    value=value,
                    field_type=field_type,
                )
                results[field_name] = success

        logger.info("Set metadata fields: %s", results)
        return results

    # ──────────────────────────────────────────────────────────────────
    # Pull Request Detection and Management
    # ──────────────────────────────────────────────────────────────────

    async def _search_open_prs_for_issue_rest(
        self,
        access_token: str,
        owner: str,
        repo: str,
        issue_number: int,
    ) -> list[dict]:
        """
        Search for open PRs related to an issue using the REST API.

        This is a fallback when GraphQL timeline events don't capture the
        PR link. Searches for open PRs whose title or body references the
        issue number (e.g., "Fixes #42", "Closes #42", "#42").

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number to search for

        Returns:
            List of PR dicts with number, state, is_draft, url, author, title
        """
        try:
            response = await self._client.get(
                f"https://api.github.com/repos/{owner}/{repo}/pulls",
                params={
                    "state": "open",
                    "per_page": 30,
                    "sort": "created",
                    "direction": "desc",
                },
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )

            if response.status_code != 200:
                logger.warning(
                    "REST PR search failed with status %d for issue #%d",
                    response.status_code,
                    issue_number,
                )
                return []

            all_prs = response.json()
            issue_ref = f"#{issue_number}"
            matched_prs = []

            for pr in all_prs:
                title = pr.get("title", "")
                body = pr.get("body", "") or ""
                head_branch = pr.get("head", {}).get("ref", "")

                # Match if issue number appears in title, body, or branch name
                # Branch patterns: copilot/fix-42, copilot/issue-42-desc, feature/42-fix
                branch_match = (
                    f"-{issue_number}" in head_branch
                    or f"/{issue_number}-" in head_branch
                    or f"/{issue_number}" == head_branch[-len(f"/{issue_number}") :]
                    or head_branch.endswith(f"-{issue_number}")
                )
                if issue_ref in title or issue_ref in body or branch_match:
                    matched_prs.append(
                        {
                            "id": pr.get("node_id"),
                            "number": pr.get("number"),
                            "title": title,
                            "state": "OPEN",
                            "is_draft": pr.get("draft", False),
                            "url": pr.get("html_url", ""),
                            "author": pr.get("user", {}).get("login", ""),
                            "head_ref": pr.get("head", {}).get("ref", ""),
                        }
                    )

            logger.info(
                "REST fallback found %d open PRs referencing issue #%d",
                len(matched_prs),
                issue_number,
            )
            return matched_prs

        except Exception as e:
            logger.error("REST PR search error for issue #%d: %s", issue_number, e)
            return []

    async def find_existing_pr_for_issue(
        self,
        access_token: str,
        owner: str,
        repo: str,
        issue_number: int,
    ) -> dict | None:
        """
        Find an existing open PR linked to an issue (created by Copilot).

        Used to ensure only one PR per issue. When a subsequent agent is
        assigned, we reuse the existing PR's branch as the ``baseRef``
        so the new agent pushes commits to the same branch and PR.

        Searches first via GraphQL timeline events, then falls back to
        the REST API to catch PRs not captured by timeline events.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number

        Returns:
            Dict with ``number``, ``head_ref``, ``url`` of the existing PR,
            or None if no existing PR is found.
        """
        try:
            # Strategy 1: GraphQL timeline events (CONNECTED_EVENT / CROSS_REFERENCED_EVENT)
            linked_prs = await self.get_linked_pull_requests(
                access_token=access_token,
                owner=owner,
                repo=repo,
                issue_number=issue_number,
            )

            # Strategy 2: REST API fallback — search open PRs referencing the issue
            if not linked_prs:
                logger.info(
                    "No linked PRs found via timeline for issue #%d, trying REST fallback",
                    issue_number,
                )
                rest_prs = await self._search_open_prs_for_issue_rest(
                    access_token=access_token,
                    owner=owner,
                    repo=repo,
                    issue_number=issue_number,
                )
                if rest_prs:
                    # REST results already have head_ref, pick the best one
                    copilot_prs = [
                        pr for pr in rest_prs if "copilot" in (pr.get("author", "") or "").lower()
                    ]
                    target_pr = (copilot_prs or rest_prs)[0]
                    result = {
                        "number": target_pr["number"],
                        "head_ref": target_pr["head_ref"],
                        "url": target_pr.get("url", ""),
                        "is_draft": target_pr.get("is_draft", False),
                    }
                    logger.info(
                        "REST fallback found existing PR #%d (branch: %s, draft: %s) for issue #%d",
                        result["number"],
                        result["head_ref"],
                        result["is_draft"],
                        issue_number,
                    )
                    return result
                return None

            # Find the first OPEN PR (preferring Copilot-authored ones)
            copilot_prs = [
                pr
                for pr in linked_prs
                if pr.get("state") == "OPEN" and "copilot" in (pr.get("author", "") or "").lower()
            ]

            open_prs = [pr for pr in linked_prs if pr.get("state") == "OPEN"]

            target_pr = (copilot_prs or open_prs or [None])[0]
            if not target_pr:
                # All linked PRs are closed/merged — try REST fallback for open PRs
                rest_prs = await self._search_open_prs_for_issue_rest(
                    access_token=access_token,
                    owner=owner,
                    repo=repo,
                    issue_number=issue_number,
                )
                if rest_prs:
                    copilot_rest = [
                        pr for pr in rest_prs if "copilot" in (pr.get("author", "") or "").lower()
                    ]
                    target_rest = (copilot_rest or rest_prs)[0]
                    result = {
                        "number": target_rest["number"],
                        "head_ref": target_rest["head_ref"],
                        "url": target_rest.get("url", ""),
                        "is_draft": target_rest.get("is_draft", False),
                    }
                    logger.info(
                        "REST fallback found existing PR #%d (branch: %s, draft: %s) for issue #%d",
                        result["number"],
                        result["head_ref"],
                        result["is_draft"],
                        issue_number,
                    )
                    return result
                return None

            # Use head_ref directly from timeline if available (avoids extra API call)
            if target_pr.get("head_ref"):
                result = {
                    "number": target_pr["number"],
                    "head_ref": target_pr["head_ref"],
                    "url": target_pr.get("url", ""),
                    "is_draft": target_pr.get("is_draft", False),
                }
                logger.info(
                    "Found existing PR #%d (branch: %s, draft: %s) for issue #%d",
                    result["number"],
                    result["head_ref"],
                    result["is_draft"],
                    issue_number,
                )
                return result

            # Fallback: fetch full PR details to get head_ref
            pr_details = await self.get_pull_request(
                access_token=access_token,
                owner=owner,
                repo=repo,
                pr_number=target_pr["number"],
            )

            if not pr_details or not pr_details.get("head_ref"):
                return None

            result = {
                "number": pr_details["number"],
                "head_ref": pr_details["head_ref"],
                "url": pr_details.get("url", ""),
                "is_draft": pr_details.get("is_draft", False),
            }

            logger.info(
                "Found existing PR #%d (branch: %s, draft: %s) for issue #%d",
                result["number"],
                result["head_ref"],
                result["is_draft"],
                issue_number,
            )
            return result

        except Exception as e:
            logger.error("Error finding existing PR for issue #%d: %s", issue_number, e)
            return None

    async def get_linked_pull_requests(
        self,
        access_token: str,
        owner: str,
        repo: str,
        issue_number: int,
    ) -> list[dict]:
        """
        Get all pull requests linked to an issue.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number

        Returns:
            List of PR details with id, number, title, state, isDraft, url, author
        """
        try:
            data = await self._graphql(
                access_token,
                GET_ISSUE_LINKED_PRS_QUERY,
                {"owner": owner, "name": repo, "number": issue_number},
            )

            prs = []
            timeline_items = (
                data.get("repository", {})
                .get("issue", {})
                .get("timelineItems", {})
                .get("nodes", [])
            )

            for item in timeline_items:
                # Check ConnectedEvent
                pr = item.get("subject") if "subject" in item else item.get("source")
                if pr and pr.get("__typename") == "PullRequest" or (pr and "number" in pr):
                    prs.append(
                        {
                            "id": pr.get("id"),
                            "number": pr.get("number"),
                            "title": pr.get("title"),
                            "state": pr.get("state"),
                            "is_draft": pr.get("isDraft", False),
                            "url": pr.get("url"),
                            "head_ref": pr.get("headRefName", ""),
                            "author": pr.get("author", {}).get("login", ""),
                            "created_at": pr.get("createdAt"),
                            "updated_at": pr.get("updatedAt"),
                        }
                    )

            # Remove duplicates by PR number
            seen = set()
            unique_prs = []
            for pr in prs:
                if pr["number"] and pr["number"] not in seen:
                    seen.add(pr["number"])
                    unique_prs.append(pr)

            logger.info(
                "Found %d linked PRs for issue #%d: %s",
                len(unique_prs),
                issue_number,
                [pr["number"] for pr in unique_prs],
            )
            return unique_prs

        except Exception as e:
            logger.error("Failed to get linked PRs for issue #%d: %s", issue_number, e)
            return []

    async def get_pull_request(
        self,
        access_token: str,
        owner: str,
        repo: str,
        pr_number: int,
    ) -> dict | None:
        """
        Get pull request details.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number

        Returns:
            PR details dict or None if not found
        """
        try:
            data = await self._graphql(
                access_token,
                GET_PULL_REQUEST_QUERY,
                {"owner": owner, "name": repo, "number": pr_number},
            )

            pr = data.get("repository", {}).get("pullRequest")
            if not pr:
                return None

            # Extract last commit info for completion detection
            last_commit = None
            check_status = None
            commits_data = pr.get("commits", {}).get("nodes", [])
            if commits_data and len(commits_data) > 0:
                commit_node = commits_data[0].get("commit", {})
                last_commit = {
                    "sha": commit_node.get("oid"),
                    "committed_date": commit_node.get("committedDate"),
                }
                status_rollup = commit_node.get("statusCheckRollup")
                if status_rollup:
                    check_status = status_rollup.get("state")

            return {
                "id": pr.get("id"),
                "number": pr.get("number"),
                "title": pr.get("title"),
                "body": pr.get("body"),
                "state": pr.get("state"),
                "is_draft": pr.get("isDraft", False),
                "url": pr.get("url"),
                "head_ref": pr.get("headRefName", ""),
                "base_ref": pr.get("baseRefName", ""),
                "author": pr.get("author", {}).get("login", ""),
                "created_at": pr.get("createdAt"),
                "updated_at": pr.get("updatedAt"),
                "last_commit": last_commit,
                "check_status": check_status,  # SUCCESS, FAILURE, PENDING, etc.
            }

        except Exception as e:
            logger.error("Failed to get PR #%d: %s", pr_number, e)
            return None

    async def mark_pr_ready_for_review(
        self,
        access_token: str,
        pr_node_id: str,
    ) -> bool:
        """
        Convert a draft PR to ready for review.

        Args:
            access_token: GitHub OAuth access token
            pr_node_id: Pull request node ID (GraphQL ID)

        Returns:
            True if successfully marked ready
        """
        try:
            data = await self._graphql(
                access_token,
                MARK_PR_READY_FOR_REVIEW_MUTATION,
                {"pullRequestId": pr_node_id},
            )

            pr = data.get("markPullRequestReadyForReview", {}).get("pullRequest", {})
            if pr and not pr.get("isDraft"):
                logger.info(
                    "Successfully marked PR #%d as ready for review: %s",
                    pr.get("number"),
                    pr.get("url"),
                )
                return True
            else:
                logger.warning("PR may not have been marked ready: %s", pr)
                return False

        except Exception as e:
            logger.error("Failed to mark PR ready for review: %s", e)
            return False

    async def request_copilot_review(
        self,
        access_token: str,
        pr_node_id: str,
        pr_number: int | None = None,
    ) -> bool:
        """
        Request a code review from GitHub Copilot on a pull request.

        Args:
            access_token: GitHub OAuth access token
            pr_node_id: Pull request node ID (GraphQL ID)
            pr_number: Optional PR number for logging

        Returns:
            True if review was successfully requested
        """
        try:
            data = await self._graphql(
                access_token,
                REQUEST_COPILOT_REVIEW_MUTATION,
                {"pullRequestId": pr_node_id},
                # Include Copilot code review feature flag
                extra_headers={"GraphQL-Features": "copilot_code_review"},
            )

            pr = data.get("requestReviewsByLogin", {}).get("pullRequest", {})
            if pr:
                logger.info(
                    "Successfully requested Copilot review for PR #%d: %s",
                    pr.get("number") or pr_number,
                    pr.get("url", ""),
                )
                return True
            else:
                logger.warning("Copilot review request may have failed: %s", data)
                return False

        except Exception as e:
            logger.error("Failed to request Copilot review for PR #%d: %s", pr_number or 0, e)
            return False

    async def merge_pull_request(
        self,
        access_token: str,
        pr_node_id: str,
        pr_number: int | None = None,
        commit_headline: str | None = None,
        merge_method: str = "SQUASH",
    ) -> dict | None:
        """
        Merge a pull request into its base branch.

        Used to merge child PR branches into the parent/main branch for an issue
        when an agent completes work.

        Args:
            access_token: GitHub OAuth access token
            pr_node_id: Pull request node ID (GraphQL ID)
            pr_number: Optional PR number for logging
            commit_headline: Optional custom commit message headline
            merge_method: Merge method - MERGE, SQUASH, or REBASE (default: SQUASH)

        Returns:
            Dict with merge details if successful, None otherwise
        """
        try:
            variables = {
                "pullRequestId": pr_node_id,
                "mergeMethod": merge_method,
            }
            if commit_headline:
                variables["commitHeadline"] = commit_headline

            data = await self._graphql(
                access_token,
                MERGE_PULL_REQUEST_MUTATION,
                variables,
            )

            result = data.get("mergePullRequest", {}).get("pullRequest", {})
            if result and result.get("merged"):
                logger.info(
                    "Successfully merged PR #%d (state=%s, merged_at=%s, commit=%s)",
                    result.get("number") or pr_number,
                    result.get("state"),
                    result.get("mergedAt"),
                    result.get("mergeCommit", {}).get("oid", "")[:8],
                )
                return {
                    "number": result.get("number"),
                    "state": result.get("state"),
                    "merged": result.get("merged"),
                    "merged_at": result.get("mergedAt"),
                    "merge_commit": result.get("mergeCommit", {}).get("oid"),
                    "url": result.get("url"),
                }
            else:
                logger.warning(
                    "PR #%d may not have been merged: %s",
                    pr_number or 0,
                    result,
                )
                return None

        except Exception as e:
            logger.error("Failed to merge PR #%d: %s", pr_number or 0, e)
            return None

    async def delete_branch(
        self,
        access_token: str,
        owner: str,
        repo: str,
        branch_name: str,
    ) -> bool:
        """
        Delete a branch from a repository.

        Used to clean up child PR branches after they are merged into the
        parent/main branch for an issue.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            branch_name: Name of the branch to delete (without refs/heads/ prefix)

        Returns:
            True if branch was deleted successfully
        """
        try:
            # Use REST API to delete the branch reference
            response = await self._client.delete(
                f"https://api.github.com/repos/{owner}/{repo}/git/refs/heads/{branch_name}",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )

            if response.status_code == 204:
                logger.info(
                    "Successfully deleted branch '%s' from %s/%s",
                    branch_name,
                    owner,
                    repo,
                )
                return True
            elif response.status_code == 422:
                # Branch doesn't exist or already deleted
                logger.debug(
                    "Branch '%s' does not exist or was already deleted",
                    branch_name,
                )
                return True
            else:
                logger.warning(
                    "Failed to delete branch '%s': %d %s",
                    branch_name,
                    response.status_code,
                    response.text,
                )
                return False

        except Exception as e:
            logger.error("Failed to delete branch '%s': %s", branch_name, e)
            return False

    async def update_pr_base(
        self,
        access_token: str,
        owner: str,
        repo: str,
        pr_number: int,
        base: str,
    ) -> bool:
        """
        Update the base branch of a pull request.

        Used to re-target child PRs that were created targeting 'main' (when
        Copilot branches from a commit SHA) so they target the issue's main
        branch instead. This ensures the child PR merges into the correct branch.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number
            base: New base branch name

        Returns:
            True if the base branch was updated successfully
        """
        try:
            response = await self._client.patch(
                f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}",
                json={"base": base},
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )

            if response.status_code == 200:
                logger.info(
                    "Updated PR #%d base branch to '%s' in %s/%s",
                    pr_number,
                    base,
                    owner,
                    repo,
                )
                return True
            else:
                logger.warning(
                    "Failed to update PR #%d base branch to '%s': %d %s",
                    pr_number,
                    base,
                    response.status_code,
                    response.text[:300] if response.text else "empty",
                )
                return False

        except Exception as e:
            logger.error(
                "Failed to update PR #%d base branch to '%s': %s",
                pr_number,
                base,
                e,
            )
            return False

    async def link_pull_request_to_issue(
        self,
        access_token: str,
        owner: str,
        repo: str,
        pr_number: int,
        issue_number: int,
    ) -> bool:
        """
        Link a pull request to a GitHub issue by adding a closing reference.

        Prepends ``Closes #<issue_number>`` to the PR body so that GitHub
        displays the PR in the issue's Development sidebar and automatically
        closes the issue when the PR is merged.

        This is called once for the *first* PR created for an issue — the
        "main" branch that all subsequent agent child PRs merge into.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number
            issue_number: Issue number to link

        Returns:
            True if the PR body was updated successfully
        """
        try:
            # Fetch the current PR body first
            pr_details = await self.get_pull_request(
                access_token=access_token,
                owner=owner,
                repo=repo,
                pr_number=pr_number,
            )
            current_body = (pr_details or {}).get("body", "") or ""

            closing_ref = f"Closes #{issue_number}"

            # Don't duplicate if the reference already exists
            if closing_ref in current_body:
                logger.debug(
                    "PR #%d already references issue #%d — skipping link",
                    pr_number,
                    issue_number,
                )
                return True

            updated_body = f"{closing_ref}\n\n{current_body}" if current_body else closing_ref

            response = await self._client.patch(
                f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}",
                json={"body": updated_body},
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )

            if response.status_code == 200:
                logger.info(
                    "Linked PR #%d to issue #%d ('%s') in %s/%s",
                    pr_number,
                    issue_number,
                    closing_ref,
                    owner,
                    repo,
                )
                return True
            else:
                logger.warning(
                    "Failed to link PR #%d to issue #%d: %d %s",
                    pr_number,
                    issue_number,
                    response.status_code,
                    response.text[:300] if response.text else "empty",
                )
                return False

        except Exception as e:
            logger.error(
                "Failed to link PR #%d to issue #%d: %s",
                pr_number,
                issue_number,
                e,
            )
            return False

    async def has_copilot_reviewed_pr(
        self,
        access_token: str,
        owner: str,
        repo: str,
        pr_number: int,
    ) -> bool:
        """
        Check if GitHub Copilot has already reviewed a pull request.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number

        Returns:
            True if Copilot has submitted a review
        """
        try:
            data = await self._graphql(
                access_token,
                GET_PULL_REQUEST_QUERY,
                {"owner": owner, "name": repo, "number": pr_number},
            )

            pr = data.get("repository", {}).get("pullRequest", {})
            if not pr:
                return False

            reviews = pr.get("reviews", {}).get("nodes", [])

            # Check if any review was submitted by copilot
            for review in reviews:
                author = review.get("author", {})
                if author and author.get("login", "").lower() == "copilot":
                    logger.info(
                        "Found existing Copilot review on PR #%d (state: %s)",
                        pr_number,
                        review.get("state"),
                    )
                    return True

            return False

        except Exception as e:
            logger.error("Failed to check Copilot review status for PR #%d: %s", pr_number, e)
            return False

    async def get_pr_timeline_events(
        self,
        access_token: str,
        owner: str,
        repo: str,
        issue_number: int,
    ) -> list[dict]:
        """
        Get timeline events for a PR/issue using the GitHub REST API.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            issue_number: Issue/PR number

        Returns:
            List of timeline events
        """
        url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/timeline"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(
                "Failed to get timeline events for issue #%d: %s",
                issue_number,
                e,
            )
            return []

    def _check_copilot_finished_events(self, events: list[dict]) -> bool:
        """
        Check if Copilot has finished work based on timeline events.

        Copilot is considered finished when one of these events exists:
        - 'copilot_work_finished' event
        - 'review_requested' event where review_requester is Copilot

        Args:
            events: List of timeline events

        Returns:
            True if Copilot has finished work
        """
        for event in events:
            event_type = event.get("event", "")

            # Check for copilot_work_finished event
            if event_type == "copilot_work_finished":
                logger.info("Found 'copilot_work_finished' timeline event")
                return True

            # Check for review_requested event from Copilot
            if event_type == "review_requested":
                review_requester = event.get("review_requester", {})
                requester_login = review_requester.get("login", "").lower()
                if requester_login == "copilot":
                    logger.info(
                        "Found 'review_requested' event from Copilot for reviewer: %s",
                        event.get("requested_reviewer", {}).get("login"),
                    )
                    return True

        return False

    async def check_copilot_pr_completion(
        self,
        access_token: str,
        owner: str,
        repo: str,
        issue_number: int,
        pipeline_started_at: "datetime | None" = None,
    ) -> dict | None:
        """
        Check if GitHub Copilot has finished work on a PR for an issue.

        Copilot completion is detected when:
        - A linked PR exists created by copilot-swe-agent[bot]
        - The PR state is OPEN (not CLOSED or MERGED)
        - The PR timeline has one of these events:
          - 'copilot_work_finished' event
          - 'review_requested' event where review_requester is Copilot

        When ``pipeline_started_at`` is provided, timeline events that
        occurred before this timestamp are ignored. This prevents stale
        events from earlier agents (e.g., speckit.specify) from being
        misattributed to the current agent (e.g., speckit.implement).

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            pipeline_started_at: If provided, only consider timeline events
                after this time (filters stale events from earlier agents).

        Returns:
            Dict with PR details if Copilot has finished work, None otherwise
        """
        try:
            linked_prs = await self.get_linked_pull_requests(
                access_token, owner, repo, issue_number
            )

            for pr in linked_prs:
                author = pr.get("author", "").lower()
                state = pr.get("state", "")
                is_draft = pr.get("is_draft", True)
                raw_pr_number = pr.get("number")
                if raw_pr_number is None:
                    continue
                pr_number = int(raw_pr_number)

                # Check if this is a Copilot-created PR
                if "copilot" in author or author == "copilot-swe-agent[bot]":
                    logger.info(
                        "Found Copilot PR #%d for issue #%d: state=%s, is_draft=%s",
                        pr_number,
                        issue_number,
                        state,
                        is_draft,
                    )

                    # PR must be OPEN to be processable
                    if state != "OPEN":
                        logger.info(
                            "Copilot PR #%d is not open (state=%s), skipping",
                            pr_number,
                            state,
                        )
                        continue

                    # Get PR details for node ID
                    pr_details = await self.get_pull_request(access_token, owner, repo, pr_number)

                    if not pr_details:
                        logger.warning(
                            "Could not get details for PR #%d",
                            pr_number,
                        )
                        continue

                    # If PR is already not a draft, it's ready (maybe manually marked)
                    if not is_draft:
                        logger.info(
                            "Copilot PR #%d is already ready for review",
                            pr_number,
                        )
                        return {
                            **pr,
                            "id": pr_details.get("id"),
                            "copilot_finished": True,
                        }

                    # PR is still draft - check timeline events for Copilot finish signal
                    timeline_events = await self.get_pr_timeline_events(
                        access_token, owner, repo, pr_number
                    )

                    # If a pipeline start time was provided, filter out stale
                    # events from earlier agents.  This prevents e.g. a
                    # review_requested event from speckit.specify being
                    # mistaken for speckit.implement completing.
                    if pipeline_started_at is not None:
                        fresh_events = []
                        for ev in timeline_events:
                            created_at_str = ev.get("created_at", "")
                            if not created_at_str:
                                fresh_events.append(ev)
                                continue
                            try:
                                from datetime import datetime as _dt

                                event_time = _dt.fromisoformat(
                                    created_at_str.replace("Z", "+00:00")
                                )
                                cutoff = (
                                    pipeline_started_at.replace(tzinfo=event_time.tzinfo)
                                    if pipeline_started_at.tzinfo is None
                                    else pipeline_started_at
                                )
                                if event_time > cutoff:
                                    fresh_events.append(ev)
                            except (ValueError, TypeError):
                                fresh_events.append(ev)
                        logger.debug(
                            "Filtered timeline events for PR #%d: %d/%d after pipeline start %s",
                            pr_number,
                            len(fresh_events),
                            len(timeline_events),
                            pipeline_started_at.isoformat(),
                        )
                        timeline_events = fresh_events

                    copilot_finished = self._check_copilot_finished_events(timeline_events)

                    if copilot_finished:
                        logger.info(
                            "Copilot PR #%d has finished work (timeline events indicate completion)",
                            pr_number,
                        )
                        return {
                            **pr,
                            "id": pr_details.get("id"),
                            "last_commit": pr_details.get("last_commit"),
                            "copilot_finished": True,
                        }

                    # No finish events yet - Copilot is still working
                    logger.info(
                        "Copilot PR #%d has no finish events yet, still in progress",
                        pr_number,
                    )

            return None

        except Exception as e:
            logger.error(
                "Failed to check Copilot PR completion for issue #%d: %s",
                issue_number,
                e,
            )
            return None

    # ──────────────────────────────────────────────────────────────────
    # Polling and Change Detection (T041, T046)
    # ──────────────────────────────────────────────────────────────────

    async def poll_project_changes(
        self,
        access_token: str,
        project_id: str,
        cached_tasks: list[Task],
        ready_status: str = "Ready",
        in_progress_status: str = "In Progress",
    ) -> dict:
        """
        Poll for changes in a project by comparing with cached state.

        Args:
            access_token: GitHub OAuth access token
            project_id: GitHub Project V2 node ID
            cached_tasks: Previously cached task list
            ready_status: Name of the Ready status column
            in_progress_status: Name of the In Progress status column

        Returns:
            Dict with:
            - 'changes': list of detected changes
            - 'current_tasks': updated task list
            - 'workflow_triggers': tasks that need workflow processing
        """
        current_tasks = await self.get_project_items(access_token, project_id)
        changes = self._detect_changes(cached_tasks, current_tasks)

        # T041: Detect tasks that need workflow processing
        workflow_triggers = []

        for change in changes:
            if change.get("type") == "status_changed":
                new_status = change.get("new_status", "")

                # Detect Ready status (trigger In Progress + Copilot assignment)
                if new_status.lower() == ready_status.lower():
                    workflow_triggers.append(
                        {
                            "trigger": "ready_detected",
                            "task_id": change.get("task_id"),
                            "title": change.get("title"),
                        }
                    )

                # T046: Detect completion signals (In Progress → closed or labeled)
                # This is handled via labels/state, not status change
                # Status-based completion detection would be In Progress → Done
                # but spec says completion is via label or closed state

        # Also check for tasks currently in "In Progress" that might have completed PRs
        for task in current_tasks:
            if task.status and task.status.lower() == in_progress_status.lower():
                workflow_triggers.append(
                    {
                        "trigger": "in_progress_check",
                        "task_id": task.github_item_id,
                        "title": task.title,
                        "issue_id": task.github_issue_id,
                    }
                )

        return {
            "changes": changes,
            "current_tasks": current_tasks,
            "workflow_triggers": workflow_triggers,
        }

    # ──────────────────────────────────────────────────────────────────
    # Sub-Issues
    # ──────────────────────────────────────────────────────────────────

    async def create_sub_issue(
        self,
        access_token: str,
        owner: str,
        repo: str,
        parent_issue_number: int,
        title: str,
        body: str,
        labels: list[str] | None = None,
    ) -> dict:
        """
        Create a GitHub sub-issue attached to a parent issue.

        Uses the GitHub Sub-Issues API to create a new issue and link it
        as a child of the parent issue.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            parent_issue_number: Parent issue number to attach to
            title: Sub-issue title
            body: Sub-issue body (markdown)
            labels: Optional list of label names

        Returns:
            Dict with sub-issue details: id, node_id, number, html_url
        """
        # Step 1: Create the issue
        sub_issue = await self.create_issue(
            access_token=access_token,
            owner=owner,
            repo=repo,
            title=title,
            body=body,
            labels=labels,
        )

        sub_issue_number = sub_issue["number"]

        # Step 2: Attach as sub-issue using the Sub-Issues API
        try:
            response = await self._client.post(
                f"https://api.github.com/repos/{owner}/{repo}/issues/{parent_issue_number}/sub_issues",
                json={"sub_issue_id": sub_issue["id"]},
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )

            if response.status_code in (200, 201):
                logger.info(
                    "Attached sub-issue #%d to parent issue #%d",
                    sub_issue_number,
                    parent_issue_number,
                )
            else:
                logger.warning(
                    "Failed to attach sub-issue #%d to parent #%d: %d %s",
                    sub_issue_number,
                    parent_issue_number,
                    response.status_code,
                    response.text[:300] if response.text else "",
                )
        except Exception as e:
            logger.warning(
                "Failed to attach sub-issue #%d to parent #%d: %s",
                sub_issue_number,
                parent_issue_number,
                e,
            )

        return sub_issue

    async def get_sub_issues(
        self,
        access_token: str,
        owner: str,
        repo: str,
        issue_number: int,
    ) -> list[dict]:
        """
        Get sub-issues for a parent issue using the GitHub Sub-Issues API.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            issue_number: Parent issue number

        Returns:
            List of sub-issue dicts with id, node_id, number, title, state, html_url, assignees, etc.
        """
        try:
            response = await self._client.get(
                f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/sub_issues",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                params={"per_page": 50},
            )

            if response.status_code == 200:
                sub_issues = response.json()
                logger.info(
                    "Found %d sub-issues for issue #%d",
                    len(sub_issues),
                    issue_number,
                )
                return sub_issues
            else:
                logger.debug(
                    "No sub-issues for issue #%d: %d",
                    issue_number,
                    response.status_code,
                )
                return []

        except Exception as e:
            logger.debug("Failed to get sub-issues for issue #%d: %s", issue_number, e)
            return []

    def tailor_body_for_agent(
        self,
        parent_body: str,
        agent_name: str,
        parent_issue_number: int,
        parent_title: str,
    ) -> str:
        """
        Tailor a parent issue's body for a specific agent sub-issue.

        Creates a focused body that references the parent issue and includes
        agent-specific guidance.

        Args:
            parent_body: The parent issue's body text
            agent_name: The agent slug (e.g., "speckit.specify")
            parent_issue_number: Parent issue number for cross-referencing
            parent_title: Parent issue title

        Returns:
            Tailored markdown body for the sub-issue
        """
        # Map agent slugs to human-readable task descriptions
        agent_descriptions = {
            "speckit.specify": "Write a detailed specification for this feature. Analyze requirements, define acceptance criteria, and document the technical approach.",
            "speckit.plan": "Create a detailed implementation plan. Break down the specification into actionable steps, identify dependencies, and define the order of execution.",
            "speckit.tasks": "Generate granular implementation tasks from the plan. Each task should be a well-defined unit of work with clear inputs, outputs, and acceptance criteria.",
            "speckit.implement": "Implement the feature based on the specification, plan, and tasks. Write production-quality code with tests.",
            "copilot": "Implement the requested changes. Write production-quality code with tests.",
        }

        agent_desc = agent_descriptions.get(
            agent_name,
            f"Complete the work assigned to the `{agent_name}` agent.",
        )

        # Strip the tracking table from the parent body (it belongs to the parent)
        import re
        clean_body = re.sub(
            r"\n---\s*\n\s*##\s*🤖\s*Agent Pipeline.*",
            "",
            parent_body,
            flags=re.DOTALL,
        ).rstrip()

        # Also strip the "Generated by AI" footer
        clean_body = re.sub(
            r"\n---\s*\n\*Generated by AI.*?\*\s*$",
            "",
            clean_body,
            flags=re.DOTALL,
        ).rstrip()

        body = f"""> **Parent Issue:** #{parent_issue_number} — {parent_title}

## 🤖 Agent Task: `{agent_name}`

{agent_desc}

---

## Parent Issue Context

{clean_body}

---
*Sub-issue created for agent `{agent_name}` — see parent issue #{parent_issue_number} for full context*
"""
        return body

    # ──────────────────────────────────────────────────────────────────
    # Issue Comments and PR File Content
    # ──────────────────────────────────────────────────────────────────

    async def create_issue_comment(
        self,
        access_token: str,
        owner: str,
        repo: str,
        issue_number: int,
        body: str,
    ) -> dict | None:
        """
        Create a comment on a GitHub Issue.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            body: Comment body (markdown)

        Returns:
            Dict with comment details if successful, None otherwise
        """
        try:
            response = await self._client.post(
                f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments",
                json={"body": body},
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )

            if response.status_code in (200, 201):
                result = response.json()
                logger.info(
                    "Created comment on issue #%d (id=%s)",
                    issue_number,
                    result.get("id"),
                )
                return result
            else:
                logger.error(
                    "Failed to create comment on issue #%d: %s %s",
                    issue_number,
                    response.status_code,
                    response.text[:300] if response.text else "",
                )
                return None

        except Exception as e:
            logger.error("Error creating comment on issue #%d: %s", issue_number, e)
            return None

    async def get_pr_changed_files(
        self,
        access_token: str,
        owner: str,
        repo: str,
        pr_number: int,
    ) -> list[dict]:
        """
        Get the list of files changed in a pull request.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number

        Returns:
            List of dicts with filename, status, additions, deletions, etc.
        """
        try:
            response = await self._client.get(
                f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                params={"per_page": 100},
            )

            if response.status_code == 200:
                files = response.json()
                logger.info(
                    "PR #%d has %d changed files",
                    pr_number,
                    len(files),
                )
                return files
            else:
                logger.error(
                    "Failed to get files for PR #%d: %s",
                    pr_number,
                    response.status_code,
                )
                return []

        except Exception as e:
            logger.error("Error getting PR #%d files: %s", pr_number, e)
            return []

    async def get_file_content_from_ref(
        self,
        access_token: str,
        owner: str,
        repo: str,
        path: str,
        ref: str,
    ) -> str | None:
        """
        Get the content of a file from a specific branch/ref.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            path: File path within the repository
            ref: Git ref (branch name, commit SHA, etc.)

        Returns:
            File content as a string, or None if not found
        """
        try:
            response = await self._client.get(
                f"https://api.github.com/repos/{owner}/{repo}/contents/{path}",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github.raw+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                params={"ref": ref},
            )

            if response.status_code == 200:
                return response.text
            else:
                logger.warning(
                    "Failed to get file %s@%s: %s",
                    path,
                    ref,
                    response.status_code,
                )
                return None

        except Exception as e:
            logger.error("Error getting file %s@%s: %s", path, ref, e)
            return None

    def _detect_changes(self, old_tasks: list[Task], new_tasks: list[Task]) -> list[dict]:
        """
        Compare two task lists and detect changes.

        Args:
            old_tasks: Previous task list
            new_tasks: Current task list

        Returns:
            List of change records
        """
        changes = []

        # Create lookup maps
        old_map = {t.github_item_id: t for t in old_tasks}
        new_map = {t.github_item_id: t for t in new_tasks}

        # Detect new tasks
        for item_id, task in new_map.items():
            if item_id not in old_map:
                changes.append(
                    {
                        "type": "task_created",
                        "task_id": item_id,
                        "title": task.title,
                        "status": task.status,
                    }
                )

        # Detect deleted tasks
        for item_id, task in old_map.items():
            if item_id not in new_map:
                changes.append(
                    {
                        "type": "task_deleted",
                        "task_id": item_id,
                        "title": task.title,
                    }
                )

        # Detect status changes
        for item_id in old_map.keys() & new_map.keys():
            old_task = old_map[item_id]
            new_task = new_map[item_id]

            if old_task.status != new_task.status:
                changes.append(
                    {
                        "type": "status_changed",
                        "task_id": item_id,
                        "title": new_task.title,
                        "old_status": old_task.status,
                        "new_status": new_task.status,
                    }
                )

            if old_task.title != new_task.title:
                changes.append(
                    {
                        "type": "title_changed",
                        "task_id": item_id,
                        "old_title": old_task.title,
                        "new_title": new_task.title,
                    }
                )

        return changes

    # ──────────────────────────────────────────────────────────────────
    # Agent Discovery (004-agent-workflow-config-ui, T016)
    # ──────────────────────────────────────────────────────────────────

    # Built-in agents that are always available
    BUILTIN_AGENTS: list[AvailableAgent] = [
        AvailableAgent(
            slug="copilot",
            display_name="GitHub Copilot",
            description="Default GitHub Copilot coding agent",
            avatar_url=None,
            source=AgentSource.BUILTIN,
        ),
        AvailableAgent(
            slug="copilot-review",
            display_name="Copilot Review",
            description="GitHub Copilot code review agent",
            avatar_url=None,
            source=AgentSource.BUILTIN,
        ),
        AvailableAgent(
            slug="speckit.specify",
            display_name="Spec Kit - Specify",
            description="Generates a detailed specification from a GitHub issue",
            avatar_url=None,
            source=AgentSource.BUILTIN,
        ),
        AvailableAgent(
            slug="speckit.plan",
            display_name="Spec Kit - Plan",
            description="Creates an implementation plan from a specification",
            avatar_url=None,
            source=AgentSource.BUILTIN,
        ),
        AvailableAgent(
            slug="speckit.tasks",
            display_name="Spec Kit - Tasks",
            description="Breaks an implementation plan into granular tasks",
            avatar_url=None,
            source=AgentSource.BUILTIN,
        ),
        AvailableAgent(
            slug="speckit.implement",
            display_name="Spec Kit - Implement",
            description="Implements code changes based on the task list",
            avatar_url=None,
            source=AgentSource.BUILTIN,
        ),
    ]

    _FRONTMATTER_RE = re.compile(r"^---\s*\r?\n(.*?)\r?\n---", re.DOTALL)

    async def list_available_agents(
        self,
        owner: str,
        repo: str,
        access_token: str,
    ) -> list[AvailableAgent]:
        """
        Discover agents available for assignment.

        Combines hardcoded built-in agents with custom agents found in
        the repository's `.github/agents/*.agent.md` files.

        Args:
            owner: Repository owner.
            repo: Repository name.
            access_token: GitHub OAuth access token.

        Returns:
            Combined list of built-in + repository agents.
        """
        agents: list[AvailableAgent] = list(self.BUILTIN_AGENTS)

        if not owner or not repo:
            return agents

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        # List .github/agents/ directory via Contents API
        try:
            response = await self._request_with_retry(
                "GET",
                f"https://api.github.com/repos/{owner}/{repo}/contents/.github/agents",
                headers=headers,
            )
            contents = response.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                logger.debug("No .github/agents/ directory in %s/%s", owner, repo)
                return agents
            logger.warning(
                "Failed to list .github/agents/ in %s/%s: %s",
                owner,
                repo,
                exc,
            )
            return agents

        if not isinstance(contents, list):
            return agents

        # Filter for *.agent.md files
        agent_files = [
            f
            for f in contents
            if isinstance(f, dict)
            and f.get("name", "").endswith(".agent.md")
            and f.get("type") == "file"
        ]

        for file_info in agent_files:
            slug = file_info["name"].removesuffix(".agent.md")
            download_url = file_info.get("download_url")
            display_name = slug
            description: str | None = None

            # Fetch raw content and parse YAML frontmatter
            if download_url:
                try:
                    raw_resp = await self._request_with_retry("GET", download_url, headers=headers)
                    raw_content = raw_resp.text
                    fm_match = self._FRONTMATTER_RE.match(raw_content)
                    if fm_match:
                        try:
                            fm = yaml.safe_load(fm_match.group(1))
                            if isinstance(fm, dict):
                                display_name = fm.get("name", slug)
                                description = fm.get("description")
                        except yaml.YAMLError:
                            logger.debug("Invalid YAML frontmatter in %s", file_info["name"])
                except httpx.HTTPStatusError:
                    logger.debug("Could not fetch content for %s", file_info["name"])

            agents.append(
                AvailableAgent(
                    slug=slug,
                    display_name=display_name,
                    description=description,
                    avatar_url=None,
                    source=AgentSource.REPOSITORY,
                )
            )

        return agents


# Global service instance
github_projects_service = GitHubProjectsService()
