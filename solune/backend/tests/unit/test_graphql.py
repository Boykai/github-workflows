"""Unit tests for GraphQL constants and query/mutation definitions."""

import pytest

from src.services.github_projects.graphql import (
    ADD_ISSUE_TO_PROJECT_MUTATION,
    ASSIGN_COPILOT_MUTATION,
    BOARD_GET_PROJECT_ITEMS_QUERY,
    BOARD_LIST_PROJECTS_QUERY,
    BOARD_RECONCILE_ITEMS_QUERY,
    CREATE_BRANCH_MUTATION,
    CREATE_COMMIT_ON_BRANCH_MUTATION,
    CREATE_DRAFT_ITEM_MUTATION,
    CREATE_PULL_REQUEST_MUTATION,
    DELETE_PROJECT_ITEM_MUTATION,
    GET_BRANCH_HEAD_QUERY,
    GET_ISSUE_LINKED_PRS_QUERY,
    GET_ISSUE_WITH_COMMENTS_QUERY,
    GET_PROJECT_FIELD_QUERY,
    GET_PROJECT_FIELDS_QUERY,
    GET_PROJECT_ITEMS_QUERY,
    GET_PROJECT_OWNER_INFO_QUERY,
    GET_PROJECT_REPOSITORY_QUERY,
    GET_PULL_REQUEST_QUERY,
    GET_REPOSITORY_INFO_QUERY,
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
    VERIFY_ITEM_ON_PROJECT_QUERY,
)

# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------


class TestConfigConstants:
    """Tests for module-level configuration constants."""

    def test_graphql_url(self):
        assert GITHUB_GRAPHQL_URL == "https://api.github.com/graphql"

    def test_max_retries(self):
        assert MAX_RETRIES == 3

    def test_initial_backoff_seconds(self):
        assert INITIAL_BACKOFF_SECONDS == 1

    def test_max_backoff_seconds(self):
        assert MAX_BACKOFF_SECONDS == 30

    def test_backoff_ordering(self):
        """Initial backoff should be less than max backoff."""
        assert INITIAL_BACKOFF_SECONDS < MAX_BACKOFF_SECONDS


# ---------------------------------------------------------------------------
# Fragment
# ---------------------------------------------------------------------------


class TestProjectFieldsFragment:
    """Tests for PROJECT_FIELDS_FRAGMENT."""

    def test_is_nonempty_string(self):
        assert isinstance(PROJECT_FIELDS_FRAGMENT, str)
        assert len(PROJECT_FIELDS_FRAGMENT.strip()) > 0

    def test_contains_fragment_keyword(self):
        assert "fragment ProjectFields on ProjectV2" in PROJECT_FIELDS_FRAGMENT

    def test_contains_expected_fields(self):
        assert "id" in PROJECT_FIELDS_FRAGMENT
        assert "title" in PROJECT_FIELDS_FRAGMENT
        assert "url" in PROJECT_FIELDS_FRAGMENT
        assert "shortDescription" in PROJECT_FIELDS_FRAGMENT


# ---------------------------------------------------------------------------
# Queries — all non-empty strings with correct keyword
# ---------------------------------------------------------------------------

ALL_QUERIES = [
    ("LIST_USER_PROJECTS_QUERY", LIST_USER_PROJECTS_QUERY),
    ("LIST_ORG_PROJECTS_QUERY", LIST_ORG_PROJECTS_QUERY),
    ("GET_PROJECT_ITEMS_QUERY", GET_PROJECT_ITEMS_QUERY),
    ("VERIFY_ITEM_ON_PROJECT_QUERY", VERIFY_ITEM_ON_PROJECT_QUERY),
    ("GET_PROJECT_OWNER_INFO_QUERY", GET_PROJECT_OWNER_INFO_QUERY),
    ("GET_PROJECT_FIELD_QUERY", GET_PROJECT_FIELD_QUERY),
    ("GET_PROJECT_REPOSITORY_QUERY", GET_PROJECT_REPOSITORY_QUERY),
    ("GET_ISSUE_WITH_COMMENTS_QUERY", GET_ISSUE_WITH_COMMENTS_QUERY),
    ("GET_SUGGESTED_ACTORS_QUERY", GET_SUGGESTED_ACTORS_QUERY),
    ("GET_ISSUE_LINKED_PRS_QUERY", GET_ISSUE_LINKED_PRS_QUERY),
    ("GET_PULL_REQUEST_QUERY", GET_PULL_REQUEST_QUERY),
    ("GET_PROJECT_FIELDS_QUERY", GET_PROJECT_FIELDS_QUERY),
    ("BOARD_RECONCILE_ITEMS_QUERY", BOARD_RECONCILE_ITEMS_QUERY),
    ("BOARD_LIST_PROJECTS_QUERY", BOARD_LIST_PROJECTS_QUERY),
    ("BOARD_GET_PROJECT_ITEMS_QUERY", BOARD_GET_PROJECT_ITEMS_QUERY),
    ("GET_REPOSITORY_INFO_QUERY", GET_REPOSITORY_INFO_QUERY),
    ("GET_BRANCH_HEAD_QUERY", GET_BRANCH_HEAD_QUERY),
]

ALL_MUTATIONS = [
    ("CREATE_DRAFT_ITEM_MUTATION", CREATE_DRAFT_ITEM_MUTATION),
    ("UPDATE_ITEM_STATUS_MUTATION", UPDATE_ITEM_STATUS_MUTATION),
    ("ADD_ISSUE_TO_PROJECT_MUTATION", ADD_ISSUE_TO_PROJECT_MUTATION),
    ("DELETE_PROJECT_ITEM_MUTATION", DELETE_PROJECT_ITEM_MUTATION),
    ("ASSIGN_COPILOT_MUTATION", ASSIGN_COPILOT_MUTATION),
    ("MARK_PR_READY_FOR_REVIEW_MUTATION", MARK_PR_READY_FOR_REVIEW_MUTATION),
    ("REQUEST_COPILOT_REVIEW_MUTATION", REQUEST_COPILOT_REVIEW_MUTATION),
    ("MERGE_PULL_REQUEST_MUTATION", MERGE_PULL_REQUEST_MUTATION),
    ("UPDATE_SINGLE_SELECT_FIELD_MUTATION", UPDATE_SINGLE_SELECT_FIELD_MUTATION),
    ("UPDATE_NUMBER_FIELD_MUTATION", UPDATE_NUMBER_FIELD_MUTATION),
    ("UPDATE_DATE_FIELD_MUTATION", UPDATE_DATE_FIELD_MUTATION),
    ("UPDATE_TEXT_FIELD_MUTATION", UPDATE_TEXT_FIELD_MUTATION),
    ("CREATE_BRANCH_MUTATION", CREATE_BRANCH_MUTATION),
    ("CREATE_COMMIT_ON_BRANCH_MUTATION", CREATE_COMMIT_ON_BRANCH_MUTATION),
    ("CREATE_PULL_REQUEST_MUTATION", CREATE_PULL_REQUEST_MUTATION),
]


class TestQueryConstants:
    """All query constants are non-empty strings containing 'query'."""

    @pytest.mark.parametrize("name,value", ALL_QUERIES, ids=[q[0] for q in ALL_QUERIES])
    def test_is_nonempty_string(self, name, value):
        assert isinstance(value, str), f"{name} should be a string"
        assert len(value.strip()) > 0, f"{name} should not be empty"

    @pytest.mark.parametrize("name,value", ALL_QUERIES, ids=[q[0] for q in ALL_QUERIES])
    def test_contains_query_keyword(self, name, value):
        assert "query" in value.lower(), f"{name} should contain the 'query' keyword"


class TestMutationConstants:
    """All mutation constants are non-empty strings containing 'mutation'."""

    @pytest.mark.parametrize("name,value", ALL_MUTATIONS, ids=[m[0] for m in ALL_MUTATIONS])
    def test_is_nonempty_string(self, name, value):
        assert isinstance(value, str), f"{name} should be a string"
        assert len(value.strip()) > 0, f"{name} should not be empty"

    @pytest.mark.parametrize("name,value", ALL_MUTATIONS, ids=[m[0] for m in ALL_MUTATIONS])
    def test_contains_mutation_keyword(self, name, value):
        assert "mutation" in value.lower(), f"{name} should contain the 'mutation' keyword"


# ---------------------------------------------------------------------------
# Fragment inclusion in queries that depend on it
# ---------------------------------------------------------------------------


class TestFragmentInclusion:
    """Queries that use ...ProjectFields must include the fragment."""

    def test_list_user_projects_includes_fragment(self):
        assert "...ProjectFields" in LIST_USER_PROJECTS_QUERY
        assert "fragment ProjectFields" in LIST_USER_PROJECTS_QUERY

    def test_list_org_projects_includes_fragment(self):
        assert "...ProjectFields" in LIST_ORG_PROJECTS_QUERY
        assert "fragment ProjectFields" in LIST_ORG_PROJECTS_QUERY

    def test_standalone_queries_do_not_include_fragment(self):
        """Queries that don't spread ...ProjectFields need not carry the fragment."""
        assert "...ProjectFields" not in GET_PROJECT_ITEMS_QUERY
        assert "...ProjectFields" not in GET_REPOSITORY_INFO_QUERY


# ---------------------------------------------------------------------------
# Specific query/mutation structure
# ---------------------------------------------------------------------------


class TestSpecificQueryStructure:
    """Spot-check important structural details in select queries."""

    def test_get_repository_info_requests_default_branch(self):
        assert "defaultBranchRef" in GET_REPOSITORY_INFO_QUERY
        assert "oid" in GET_REPOSITORY_INFO_QUERY

    def test_create_commit_mutation_uses_file_changes(self):
        assert "$fileChanges" in CREATE_COMMIT_ON_BRANCH_MUTATION
        assert "createCommitOnBranch" in CREATE_COMMIT_ON_BRANCH_MUTATION

    def test_create_branch_mutation_uses_create_ref(self):
        assert "createRef" in CREATE_BRANCH_MUTATION
        assert "$repositoryId" in CREATE_BRANCH_MUTATION

    def test_create_pull_request_mutation_fields(self):
        assert "createPullRequest" in CREATE_PULL_REQUEST_MUTATION
        assert "$headRefName" in CREATE_PULL_REQUEST_MUTATION
        assert "$baseRefName" in CREATE_PULL_REQUEST_MUTATION

    def test_get_branch_head_query_uses_qualified_name(self):
        assert "$qualifiedName" in GET_BRANCH_HEAD_QUERY

    def test_merge_pr_mutation_includes_merge_method(self):
        assert "$mergeMethod" in MERGE_PULL_REQUEST_MUTATION
        assert "mergePullRequest" in MERGE_PULL_REQUEST_MUTATION

    def test_assign_copilot_mutation_has_agent_assignment(self):
        assert "agentAssignment" in ASSIGN_COPILOT_MUTATION
        assert "$customAgent" in ASSIGN_COPILOT_MUTATION
