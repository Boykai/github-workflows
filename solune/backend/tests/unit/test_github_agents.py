"""Unit tests for AgentsMixin (agents.py) in GitHubProjectsService."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from githubkit.exception import RequestFailed
from githubkit.response import Response as GitHubResponse

from src.models.agent import AgentSource, AvailableAgent
from src.services.github_projects import GitHubProjectsService
from src.services.github_projects.agents import AgentsMixin

TOKEN = "ghp_test_token"
OWNER = "octocat"
REPO = "my-repo"


def _make_request_failed(status_code: int) -> RequestFailed:
    """Build a RequestFailed exception with the given status code."""
    github_response = GitHubResponse(
        httpx.Response(
            status_code,
            request=httpx.Request("GET", "https://api.github.com/test"),
        ),
        data_model=object,
    )
    return RequestFailed(github_response)


# =====================================================================
# BUILTIN_AGENTS
# =====================================================================


class TestBuiltinAgents:
    """Tests for the BUILTIN_AGENTS class variable."""

    def test_builtin_agents_exists(self):
        """BUILTIN_AGENTS should be a non-empty list."""
        assert isinstance(AgentsMixin.BUILTIN_AGENTS, list)
        assert len(AgentsMixin.BUILTIN_AGENTS) > 0

    def test_builtin_agents_count(self):
        """Should have exactly 8 built-in agents."""
        assert len(AgentsMixin.BUILTIN_AGENTS) == 8

    def test_all_agents_are_available_agent_instances(self):
        """Each entry should be an AvailableAgent."""
        for agent in AgentsMixin.BUILTIN_AGENTS:
            assert isinstance(agent, AvailableAgent)

    def test_copilot_agent_present(self):
        """The 'copilot' agent should be in the built-in list."""
        slugs = [a.slug for a in AgentsMixin.BUILTIN_AGENTS]
        assert "copilot" in slugs

    def test_human_agent_present(self):
        """The 'human' agent should be in the built-in list."""
        slugs = [a.slug for a in AgentsMixin.BUILTIN_AGENTS]
        assert "human" in slugs

    def test_expected_slugs(self):
        """All expected built-in agent slugs should be present."""
        expected = {
            "copilot",
            "copilot-review",
            "speckit.specify",
            "speckit.plan",
            "speckit.tasks",
            "speckit.implement",
            "speckit.analyze",
            "human",
        }
        actual = {a.slug for a in AgentsMixin.BUILTIN_AGENTS}
        assert actual == expected

    def test_all_builtin_source(self):
        """All built-in agents should have source=BUILTIN."""
        for agent in AgentsMixin.BUILTIN_AGENTS:
            assert agent.source == AgentSource.BUILTIN


# =====================================================================
# format_issue_context_as_prompt
# =====================================================================


class TestFormatIssueContextAsPrompt:
    """Tests for AgentsMixin.format_issue_context_as_prompt."""

    @pytest.fixture
    def service(self):
        return GitHubProjectsService()

    def test_basic_issue_data(self, service):
        """Should format title and body into the prompt."""
        issue_data = {
            "title": "Add caching layer",
            "body": "We need Redis caching.",
        }
        result = service.format_issue_context_as_prompt(issue_data)

        assert "## Issue Title" in result
        assert "Add caching layer" in result
        assert "## Issue Description" in result
        assert "We need Redis caching." in result

    def test_with_comments(self, service):
        """Should include comments in the prompt."""
        issue_data = {
            "title": "Feature request",
            "body": "Please implement X",
            "comments": [
                {
                    "author": "alice",
                    "body": "I agree with this.",
                    "created_at": "2024-01-15T10:00:00Z",
                },
                {
                    "author": "bob",
                    "body": "+1",
                    "created_at": "2024-01-15T11:00:00Z",
                },
            ],
        }
        result = service.format_issue_context_as_prompt(issue_data)

        assert "## Comments and Discussion" in result
        assert "@alice" in result
        assert "I agree with this." in result
        assert "@bob" in result

    def test_empty_issue_data(self, service):
        """Should handle empty issue data gracefully."""
        result = service.format_issue_context_as_prompt({})
        assert isinstance(result, str)

    def test_with_agent_name_speckit_specify(self, service):
        """Should add output instructions for speckit.specify."""
        issue_data = {"title": "Test", "body": "Test body"}
        result = service.format_issue_context_as_prompt(issue_data, agent_name="speckit.specify")

        assert "## Output Instructions" in result
        assert "`spec.md`" in result

    def test_with_agent_name_speckit_implement(self, service):
        """speckit.implement has no .md output files; instructions should still appear."""
        issue_data = {"title": "Test", "body": "Test body"}
        result = service.format_issue_context_as_prompt(issue_data, agent_name="speckit.implement")

        assert "## Output Instructions" in result
        assert "commit all changes" in result

    def test_with_agent_name_speckit_analyze(self, service):
        """speckit.analyze should remain read-only and avoid commit instructions."""
        issue_data = {"title": "Test", "body": "Test body"}
        result = service.format_issue_context_as_prompt(issue_data, agent_name="speckit.analyze")

        assert "## Output Instructions" in result
        assert "read-only" in result
        assert "Do NOT commit files" in result
        assert "analysis report" in result
        assert "commit all changes" not in result

    def test_with_existing_pr(self, service):
        """Should include PR context when existing_pr is provided."""
        issue_data = {"title": "Test", "body": "Test body"}
        existing_pr = {
            "number": 42,
            "head_ref": "feature/caching",
            "url": "https://github.com/octocat/repo/pull/42",
            "is_draft": True,
        }
        result = service.format_issue_context_as_prompt(issue_data, existing_pr=existing_pr)

        assert "## Related Pull Request" in result
        assert "#42" in result
        assert "`feature/caching`" in result
        assert "Draft / Work In Progress" in result

    def test_analyze_with_existing_pr_remains_read_only(self, service):
        """Existing PR context should not turn speckit.analyze into a write agent."""
        issue_data = {"title": "Test", "body": "Test body"}
        existing_pr = {
            "number": 42,
            "head_ref": "feature/caching",
            "url": "https://github.com/octocat/repo/pull/42",
            "is_draft": True,
        }
        result = service.format_issue_context_as_prompt(
            issue_data, agent_name="speckit.analyze", existing_pr=existing_pr
        )

        assert "`feature/caching`" in result
        assert "read-only" in result
        assert "Do NOT commit files" in result
        assert "commit all changes" not in result

    def test_existing_pr_not_draft(self, service):
        """Non-draft PR should not show draft label."""
        issue_data = {"title": "Test", "body": "Body"}
        existing_pr = {
            "number": 10,
            "head_ref": "main-feature",
            "url": "https://github.com/org/repo/pull/10",
            "is_draft": False,
        }
        result = service.format_issue_context_as_prompt(issue_data, existing_pr=existing_pr)

        assert "Draft" not in result

    def test_no_title_or_body(self, service):
        """Should handle missing title and body gracefully."""
        issue_data = {"comments": [{"author": "u", "body": "Hello", "created_at": "now"}]}
        result = service.format_issue_context_as_prompt(issue_data)

        assert "## Issue Title" not in result
        assert "## Issue Description" not in result
        assert "Hello" in result

    def test_agent_with_existing_pr_branch_note(self, service):
        """Output instructions should reference the PR branch when available."""
        issue_data = {"title": "T", "body": "B"}
        existing_pr = {
            "number": 5,
            "head_ref": "fix/branch",
            "url": "url",
            "is_draft": False,
        }
        result = service.format_issue_context_as_prompt(
            issue_data, agent_name="speckit.plan", existing_pr=existing_pr
        )

        assert "`fix/branch`" in result
        assert "`plan.md`" in result


# =====================================================================
# tailor_body_for_agent
# =====================================================================


class TestTailorBodyForAgent:
    """Tests for AgentsMixin.tailor_body_for_agent."""

    @pytest.fixture
    def service(self):
        return GitHubProjectsService()

    def test_basic_tailoring(self, service):
        """Should produce a body referencing parent issue and agent task."""
        result = service.tailor_body_for_agent(
            parent_body="Implement the feature.",
            agent_name="speckit.specify",
            parent_issue_number=10,
            parent_title="Feature X",
        )

        assert "**Parent Issue:** #10" in result
        assert "Feature X" in result
        assert "## 🤖 Agent Task: `speckit.specify`" in result
        assert "Write a detailed specification" in result
        assert "Implement the feature." in result

    def test_copilot_agent(self, service):
        """Copilot agent should get 'Implement the requested changes' guidance."""
        result = service.tailor_body_for_agent(
            parent_body="Fix the bug.",
            agent_name="copilot",
            parent_issue_number=20,
            parent_title="Bug Fix",
        )

        assert "`copilot`" in result
        assert "Implement the requested changes" in result

    def test_speckit_analyze_agent(self, service):
        """speckit.analyze should describe read-only analysis work."""
        result = service.tailor_body_for_agent(
            parent_body="Review the generated artifacts.",
            agent_name="speckit.analyze",
            parent_issue_number=21,
            parent_title="Artifact Review",
        )

        assert "`speckit.analyze`" in result
        assert "strictly read-only" in result
        assert "analysis report" in result

    def test_unknown_agent_fallback(self, service):
        """Unknown agents should get a generic fallback description."""
        result = service.tailor_body_for_agent(
            parent_body="Do something.",
            agent_name="custom-agent",
            parent_issue_number=30,
            parent_title="Custom Task",
        )

        assert "`custom-agent`" in result
        assert "Complete the work assigned to the `custom-agent` agent" in result

    def test_strips_tracking_table(self, service):
        """Should strip the agent pipeline tracking table from the parent body."""
        parent_body = (
            "Feature description\n"
            "\n---\n\n"
            "## 🤖 Agent Pipeline\n"
            "| Agent | Status |\n"
            "| copilot | ✅ Done |"
        )
        result = service.tailor_body_for_agent(
            parent_body=parent_body,
            agent_name="speckit.tasks",
            parent_issue_number=40,
            parent_title="Pipeline Feature",
        )

        assert "Feature description" in result
        assert "Agent Pipeline" not in result

    def test_strips_generated_by_ai_footer(self, service):
        """Should strip the 'Generated by AI' footer from the parent body."""
        parent_body = "Feature content\n\n---\n*Generated by AI assistant*"
        result = service.tailor_body_for_agent(
            parent_body=parent_body,
            agent_name="copilot",
            parent_issue_number=50,
            parent_title="AI Feature",
        )

        assert "Feature content" in result
        assert "Generated by AI" not in result

    def test_human_agent_description(self, service):
        """Human agent should get a manual task description."""
        result = service.tailor_body_for_agent(
            parent_body="Manual work needed.",
            agent_name="human",
            parent_issue_number=60,
            parent_title="Manual Task",
        )

        assert "manual human task" in result

    def test_footer_references_parent(self, service):
        """Footer should reference the parent issue number."""
        result = service.tailor_body_for_agent(
            parent_body="Body text",
            agent_name="copilot",
            parent_issue_number=77,
            parent_title="Title",
        )

        assert "see parent issue #77" in result


# =====================================================================
# list_available_agents
# =====================================================================


class TestListAvailableAgents:
    """Tests for AgentsMixin.list_available_agents."""

    @pytest.fixture
    def service(self):
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_success_with_repo_agents(self, service):
        """Should return built-in + repository agents from .github/agents/."""
        # Mock REST: list directory
        dir_contents = [
            {
                "name": "reviewer.agent.md",
                "type": "file",
                "download_url": "https://raw.githubusercontent.com/octocat/my-repo/main/.github/agents/reviewer.agent.md",
            },
        ]
        # Mock REST response: raw file content with YAML frontmatter
        raw_content = (
            "---\nname: Code Reviewer\ndescription: Reviews PRs\nicon: review\n---\nReview all PRs."
        )
        mock_response = SimpleNamespace(text=raw_content)

        with (
            patch.object(service, "_rest", new_callable=AsyncMock, return_value=dir_contents),
            patch.object(
                service, "_rest_response", new_callable=AsyncMock, return_value=mock_response
            ),
        ):
            result = await service.list_available_agents(OWNER, REPO, TOKEN)

        # Should have all built-in agents + 1 repo agent
        assert len(result) == len(AgentsMixin.BUILTIN_AGENTS) + 1
        repo_agent = result[-1]
        assert repo_agent.slug == "reviewer"
        assert repo_agent.display_name == "Code Reviewer"
        assert repo_agent.description == "Reviews PRs"
        assert repo_agent.icon_name == "review"
        assert repo_agent.source == AgentSource.REPOSITORY

    @pytest.mark.asyncio
    async def test_404_no_agents_dir(self, service):
        """Should return only built-in agents when .github/agents/ doesn't exist."""
        exc = _make_request_failed(404)

        with patch.object(service, "_rest", new_callable=AsyncMock, side_effect=exc):
            result = await service.list_available_agents(OWNER, REPO, TOKEN)

        assert len(result) == len(AgentsMixin.BUILTIN_AGENTS)
        assert all(a.source == AgentSource.BUILTIN for a in result)

    @pytest.mark.asyncio
    async def test_non_404_error_returns_builtins(self, service):
        """Non-404 RequestFailed should still return built-in agents."""
        exc = _make_request_failed(500)

        with patch.object(service, "_rest", new_callable=AsyncMock, side_effect=exc):
            result = await service.list_available_agents(OWNER, REPO, TOKEN)

        assert len(result) == len(AgentsMixin.BUILTIN_AGENTS)

    @pytest.mark.asyncio
    async def test_empty_owner_or_repo(self, service):
        """Should return only built-in agents when owner/repo is empty."""
        result = await service.list_available_agents("", REPO, TOKEN)
        assert len(result) == len(AgentsMixin.BUILTIN_AGENTS)

        result = await service.list_available_agents(OWNER, "", TOKEN)
        assert len(result) == len(AgentsMixin.BUILTIN_AGENTS)

    @pytest.mark.asyncio
    async def test_non_list_contents_returns_builtins(self, service):
        """If the API returns a non-list (e.g. single file), should return builtins only."""
        with patch.object(service, "_rest", new_callable=AsyncMock, return_value={"type": "file"}):
            result = await service.list_available_agents(OWNER, REPO, TOKEN)

        assert len(result) == len(AgentsMixin.BUILTIN_AGENTS)

    @pytest.mark.asyncio
    async def test_filters_non_agent_files(self, service):
        """Should only process *.agent.md files."""
        dir_contents = [
            {
                "name": "reviewer.agent.md",
                "type": "file",
                "download_url": "https://raw.example.com/reviewer.agent.md",
            },
            {
                "name": "README.md",
                "type": "file",
                "download_url": "https://raw.example.com/README.md",
            },
            {"name": "sub-dir", "type": "dir"},
        ]
        raw_content = "---\nname: Reviewer\n---\nContent"
        mock_response = SimpleNamespace(text=raw_content)

        with (
            patch.object(service, "_rest", new_callable=AsyncMock, return_value=dir_contents),
            patch.object(
                service, "_rest_response", new_callable=AsyncMock, return_value=mock_response
            ),
        ):
            result = await service.list_available_agents(OWNER, REPO, TOKEN)

        repo_agents = [a for a in result if a.source == AgentSource.REPOSITORY]
        assert len(repo_agents) == 1
        assert repo_agents[0].slug == "reviewer"

    @pytest.mark.asyncio
    async def test_agent_without_frontmatter(self, service):
        """Agent files without YAML frontmatter should use slug-derived display name."""
        dir_contents = [
            {
                "name": "quality-assurance.agent.md",
                "type": "file",
                "download_url": "https://raw.example.com/qa.agent.md",
            },
        ]
        raw_content = "No frontmatter, just instructions."
        mock_response = SimpleNamespace(text=raw_content)

        with (
            patch.object(service, "_rest", new_callable=AsyncMock, return_value=dir_contents),
            patch.object(
                service, "_rest_response", new_callable=AsyncMock, return_value=mock_response
            ),
        ):
            result = await service.list_available_agents(OWNER, REPO, TOKEN)

        repo_agent = next(a for a in result if a.source == AgentSource.REPOSITORY)
        assert repo_agent.slug == "quality-assurance"
        assert repo_agent.display_name == "Quality Assurance"
        assert repo_agent.description is None

    @pytest.mark.asyncio
    async def test_agent_file_fetch_failure(self, service):
        """If fetching agent file content fails, agent should still be added with defaults."""
        dir_contents = [
            {
                "name": "broken.agent.md",
                "type": "file",
                "download_url": "https://raw.example.com/broken.agent.md",
            },
        ]

        with (
            patch.object(service, "_rest", new_callable=AsyncMock, return_value=dir_contents),
            patch.object(
                service,
                "_rest_response",
                new_callable=AsyncMock,
                side_effect=_make_request_failed(404),
            ),
        ):
            result = await service.list_available_agents(OWNER, REPO, TOKEN)

        repo_agent = next(a for a in result if a.source == AgentSource.REPOSITORY)
        assert repo_agent.slug == "broken"
        assert repo_agent.display_name == "Broken"
