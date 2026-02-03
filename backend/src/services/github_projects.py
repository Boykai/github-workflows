"""GitHub Projects V2 GraphQL service."""

import asyncio
import logging
from datetime import datetime

import httpx

from src.models.project import GitHubProject, ProjectType, StatusColumn
from src.models.task import Task

logger = logging.getLogger(__name__)

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"

# T057: Rate limit configuration
MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 1
MAX_BACKOFF_SECONDS = 30


# GraphQL queries
LIST_USER_PROJECTS_QUERY = """
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
            }
          }
        }
        items(first: 1) {
          totalCount
        }
      }
    }
  }
}
"""

LIST_ORG_PROJECTS_QUERY = """
query($login: String!, $first: Int!) {
  organization(login: $login) {
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
            }
          }
        }
        items(first: 1) {
          totalCount
        }
      }
    }
  }
}
"""

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
              title
              body
            }
            ... on PullRequest {
              id
              title
              body
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
mutation($issueId: ID!, $assigneeIds: [ID!]!, $repoId: ID!, $baseRef: String!) {
  addAssigneesToAssignable(input: {
    assignableId: $issueId,
    assigneeIds: $assigneeIds,
    agentAssignment: {
      targetRepositoryId: $repoId,
      baseRef: $baseRef,
      customInstructions: "",
      customAgent: "",
      model: ""
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
            request=None,
            response=None,
        )

    async def _graphql(self, access_token: str, query: str, variables: dict, extra_headers: dict | None = None) -> dict:
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
                status_columns = [
                    StatusColumn(field_id="", name="Todo", option_id=""),
                    StatusColumn(field_id="", name="In Progress", option_id=""),
                    StatusColumn(field_id="", name="Done", option_id=""),
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

                all_tasks.append(
                    Task(
                        project_id=project_id,
                        github_item_id=item["id"],
                        github_content_id=content.get("id"),
                        title=content.get("title", "Untitled"),
                        description=content.get("body"),
                        status=status_value.get("name", "Todo") if status_value else "Todo",
                        status_option_id=status_value.get("optionId", "") if status_value else "",
                    )
                )

            has_next_page = page_info.get("hasNextPage", False)
            after = page_info.get("endCursor")

            # Safety check to prevent infinite loops
            if not after:
                break

        logger.info("Fetched %d total tasks from project %s", len(all_tasks), project_id)
        return all_tasks

    async def create_draft_item(
        self, access_token: str, project_id: str, title: str, description: str | None = None
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
                extra_headers={"GraphQL-Features": "issues_copilot_assignment_api_support,coding_agent_model_selection"},
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

            logger.warning("Copilot bot not available for %s/%s (actors: %s)", owner, repo, [a.get("login") for a in actors])
            return None, repo_id
        except Exception as e:
            logger.warning("Failed to get Copilot bot ID: %s", e)
            return None, None

    async def assign_copilot_to_issue(
        self,
        access_token: str,
        owner: str,
        repo: str,
        issue_node_id: str,
        base_ref: str = "main",
    ) -> bool:
        """
        Assign GitHub Copilot to an issue using GraphQL API with agent assignment.

        Requires the special header for Copilot assignment support.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            issue_node_id: Issue node ID (not issue number)
            base_ref: Branch to base the PR on (default: main)

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
                },
                extra_headers={"GraphQL-Features": "issues_copilot_assignment_api_support,coding_agent_model_selection"},
            )

            assignees = (
                data.get("addAssigneesToAssignable", {})
                .get("assignable", {})
                .get("assignees", {})
                .get("nodes", [])
            )
            assigned_logins = [a.get("login", "") for a in assignees]
            logger.info("Assigned Copilot to issue, current assignees: %s", assigned_logins)
            return True

        except Exception as e:
            logger.error("Failed to assign Copilot to issue: %s", e)
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
                old_status = change.get("old_status", "")
                new_status = change.get("new_status", "")

                # Detect Ready status (trigger In Progress + Copilot assignment)
                if new_status.lower() == ready_status.lower():
                    workflow_triggers.append({
                        "trigger": "ready_detected",
                        "task_id": change.get("task_id"),
                        "title": change.get("title"),
                    })

                # T046: Detect completion signals (In Progress → closed or labeled)
                # This is handled via labels/state, not status change
                # Status-based completion detection would be In Progress → Done
                # but spec says completion is via label or closed state

        return {
            "changes": changes,
            "current_tasks": current_tasks,
            "workflow_triggers": workflow_triggers,
        }

    def _detect_changes(
        self, old_tasks: list[Task], new_tasks: list[Task]
    ) -> list[dict]:
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
                changes.append({
                    "type": "task_created",
                    "task_id": item_id,
                    "title": task.title,
                    "status": task.status,
                })

        # Detect deleted tasks
        for item_id, task in old_map.items():
            if item_id not in new_map:
                changes.append({
                    "type": "task_deleted",
                    "task_id": item_id,
                    "title": task.title,
                })

        # Detect status changes
        for item_id in old_map.keys() & new_map.keys():
            old_task = old_map[item_id]
            new_task = new_map[item_id]

            if old_task.status != new_task.status:
                changes.append({
                    "type": "status_changed",
                    "task_id": item_id,
                    "title": new_task.title,
                    "old_status": old_task.status,
                    "new_status": new_task.status,
                })

            if old_task.title != new_task.title:
                changes.append({
                    "type": "title_changed",
                    "task_id": item_id,
                    "old_title": old_task.title,
                    "new_title": new_task.title,
                })

        return changes


# Global service instance
github_projects_service = GitHubProjectsService()
