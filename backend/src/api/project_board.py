"""Project board API endpoints."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from src.api.auth import get_session_dep
from src.models.project_board import (
    BoardAssignee,
    BoardDataResponse,
    BoardIssueCard,
    BoardProject,
    BoardProjectListResponse,
    BoardStatusColumn,
    BoardStatusColumnSummary,
    LinkedPRsRequest,
    LinkedPRsResponse,
    LinkedPullRequest,
)
from src.models.user import UserSession
from src.services.cache import cache, get_user_projects_cache_key
from src.services.github_projects import github_projects_service

logger = logging.getLogger(__name__)
router = APIRouter()

# GraphQL query to fetch full board data with field values, assignees, and content
GET_BOARD_DATA_QUERY = """
query($projectId: ID!, $first: Int!, $after: String) {
  node(id: $projectId) {
    ... on ProjectV2 {
      title
      shortDescription
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
                field { ... on ProjectV2SingleSelectField { name } }
              }
              ... on ProjectV2ItemFieldNumberValue {
                number
                field { ... on ProjectV2Field { name } }
              }
              ... on ProjectV2ItemFieldTextValue {
                text
                field { ... on ProjectV2Field { name } }
              }
            }
          }
          content {
            ... on Issue {
              id
              number
              title
              body
              state
              url
              repository { name nameWithOwner }
              assignees(first: 10) {
                nodes { login avatarUrl }
              }
            }
            ... on DraftIssue {
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


def _build_linked_prs_query(content_ids: list[str]) -> tuple[str, dict]:
    """Build a batched GraphQL query for linked PRs using aliases."""
    if not content_ids:
        return "", {}

    fragments = []
    variables = {}
    var_declarations = []

    for i, cid in enumerate(content_ids):
        alias = f"issue{i}"
        var_name = f"issueId{i}"
        var_declarations.append(f"${var_name}: ID!")
        fragments.append(f"""
    {alias}: node(id: ${var_name}) {{
      ... on Issue {{
        id
        timelineItems(first: 10, itemTypes: [CROSS_REFERENCED_EVENT]) {{
          nodes {{
            ... on CrossReferencedEvent {{
              source {{
                ... on PullRequest {{
                  number
                  title
                  state
                  url
                }}
              }}
            }}
          }}
        }}
      }}
    }}""")
        variables[var_name] = cid

    newline = "\n"
    query = f"""query({', '.join(var_declarations)}) {{{newline.join(fragments)}
}}"""
    return query, variables


def _parse_board_items(items_data: list[dict]) -> list[BoardIssueCard]:
    """Parse GraphQL project items into BoardIssueCard models."""
    cards = []
    for item in items_data:
        if not item:
            continue

        content = item.get("content") or {}
        field_values = item.get("fieldValues", {}).get("nodes", [])

        # Parse field values
        status = None
        priority = None
        size = None
        estimate = None

        for fv in field_values:
            if not fv:
                continue
            field_info = fv.get("field", {})
            field_name = field_info.get("name", "") if field_info else ""

            if "name" in fv and field_name == "Status":
                status = fv["name"]
            elif "name" in fv and field_name == "Priority":
                priority = fv["name"]
            elif "name" in fv and field_name == "Size":
                size = fv["name"]
            elif "number" in fv and field_name == "Estimate":
                estimate = fv["number"]

        # Parse assignees
        assignees = []
        assignee_nodes = content.get("assignees", {}).get("nodes", [])
        for a in assignee_nodes:
            if a:
                assignees.append(BoardAssignee(
                    login=a.get("login", ""),
                    avatar_url=a.get("avatarUrl", ""),
                ))

        # Determine if it's a real issue or draft
        is_issue = "number" in content
        repo = content.get("repository", {})

        cards.append(BoardIssueCard(
            item_id=item["id"],
            content_id=content.get("id") if is_issue else None,
            issue_number=content.get("number") if is_issue else None,
            title=content.get("title", "Untitled"),
            body=content.get("body"),
            state=content.get("state") if is_issue else None,
            url=content.get("url") if is_issue else None,
            repo_name=repo.get("name") if repo else None,
            repo_full_name=repo.get("nameWithOwner") if repo else None,
            status=status,
            priority=priority,
            size=size,
            estimate=estimate,
            assignees=assignees,
            linked_prs=[],
        ))

    return cards


@router.get("/projects", response_model=BoardProjectListResponse)
async def list_board_projects(
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> BoardProjectListResponse:
    """List all available GitHub Projects for the authenticated user."""
    cache_key = get_user_projects_cache_key(session.github_user_id)

    # Check cache
    cached = cache.get(cache_key)
    if cached:
        projects = [
            BoardProject(
                project_id=p.project_id,
                title=p.name,
                description=p.description,
                url=p.url,
                item_count=p.item_count or 0,
                status_columns=[
                    BoardStatusColumnSummary(
                        name=sc.name,
                        color=sc.color or "GRAY",
                        option_id=sc.option_id,
                    )
                    for sc in p.status_columns
                ],
            )
            for p in cached
        ]
        return BoardProjectListResponse(projects=projects)

    # Fetch from GitHub
    user_projects = await github_projects_service.list_user_projects(
        session.access_token, session.github_username
    )
    cache.set(cache_key, user_projects)

    projects = [
        BoardProject(
            project_id=p.project_id,
            title=p.name,
            description=p.description,
            url=p.url,
            item_count=p.item_count or 0,
            status_columns=[
                BoardStatusColumnSummary(
                    name=sc.name,
                    color=sc.color or "GRAY",
                    option_id=sc.option_id,
                )
                for sc in p.status_columns
            ],
        )
        for p in user_projects
    ]
    return BoardProjectListResponse(projects=projects)


@router.get("/{project_id}/board", response_model=BoardDataResponse)
async def get_board_data(
    project_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> BoardDataResponse:
    """Fetch full board data for a specific project, grouped by status columns."""
    board_cache_key = f"board_data:{session.github_user_id}:{project_id}"

    # Check cache
    cached_board = cache.get(board_cache_key)
    if cached_board:
        return cached_board

    try:
        # Fetch all items with pagination
        all_items: list[dict] = []
        cursor = None
        page_size = 100

        while True:
            variables: dict = {
                "projectId": project_id,
                "first": page_size,
            }
            if cursor:
                variables["after"] = cursor

            data = await github_projects_service._graphql(
                session.access_token,
                GET_BOARD_DATA_QUERY,
                variables,
            )

            project_node = data.get("node", {})
            if not project_node:
                raise HTTPException(status_code=404, detail="Project not found")

            items_data = project_node.get("items", {})
            nodes = items_data.get("nodes", [])
            all_items.extend(nodes)

            page_info = items_data.get("pageInfo", {})
            if page_info.get("hasNextPage"):
                cursor = page_info.get("endCursor")
            else:
                break

        # Parse status columns from project
        title = project_node.get("title", "")
        status_field = project_node.get("field", {})
        status_options = status_field.get("options", []) if status_field else []

        # Parse all items
        cards = _parse_board_items(all_items)

        # Group cards by status
        column_map: dict[str, list[BoardIssueCard]] = {}
        for option in status_options:
            column_map[option["name"]] = []

        # Also add an "No Status" column for items without status
        no_status_cards: list[BoardIssueCard] = []

        for card in cards:
            if card.status and card.status in column_map:
                column_map[card.status].append(card)
            else:
                no_status_cards.append(card)

        # Build columns
        columns: list[BoardStatusColumn] = []
        for option in status_options:
            name = option["name"]
            items_in_col = column_map.get(name, [])
            estimates = [c.estimate for c in items_in_col if c.estimate is not None]
            columns.append(BoardStatusColumn(
                name=name,
                color=option.get("color", "GRAY"),
                option_id=option.get("id", ""),
                description=option.get("description"),
                item_count=len(items_in_col),
                total_estimate=sum(estimates) if estimates else None,
                items=items_in_col,
            ))

        # Add "No Status" column if there are items without status
        if no_status_cards:
            estimates = [c.estimate for c in no_status_cards if c.estimate is not None]
            columns.insert(0, BoardStatusColumn(
                name="No Status",
                color="GRAY",
                option_id="",
                description="Items without a status assigned",
                item_count=len(no_status_cards),
                total_estimate=sum(estimates) if estimates else None,
                items=no_status_cards,
            ))

        response = BoardDataResponse(
            project_id=project_id,
            title=title,
            columns=columns,
        )

        # Cache for 30 seconds (shorter than default to keep board fresh)
        cache.set(board_cache_key, response, ttl=30)

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to fetch board data: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch board data: {str(e)}")


@router.post("/linked-prs", response_model=LinkedPRsResponse)
async def get_linked_prs(
    request: LinkedPRsRequest,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> LinkedPRsResponse:
    """Fetch linked pull requests for a batch of issue content IDs."""
    if not request.content_ids:
        return LinkedPRsResponse(linked_prs={})

    try:
        query, variables = _build_linked_prs_query(request.content_ids)
        if not query:
            return LinkedPRsResponse(linked_prs={})

        data = await github_projects_service._graphql(
            session.access_token,
            query,
            variables,
        )

        # Parse results
        result: dict[str, list[LinkedPullRequest]] = {}
        for i, content_id in enumerate(request.content_ids):
            alias = f"issue{i}"
            issue_data = data.get(alias, {})
            timeline = issue_data.get("timelineItems", {}).get("nodes", [])

            prs: list[LinkedPullRequest] = []
            seen_pr_numbers: set[int] = set()
            for event in timeline:
                if not event:
                    continue
                source = event.get("source", {})
                if source and "number" in source:
                    pr_number = source["number"]
                    if pr_number not in seen_pr_numbers:
                        seen_pr_numbers.add(pr_number)
                        prs.append(LinkedPullRequest(
                            pr_number=pr_number,
                            title=source.get("title", ""),
                            state=source.get("state", "OPEN"),
                            url=source.get("url", ""),
                        ))

            result[content_id] = prs

        return LinkedPRsResponse(linked_prs=result)

    except Exception as e:
        logger.error("Failed to fetch linked PRs: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch linked PRs: {str(e)}")
