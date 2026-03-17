"""Tests for webhook Pydantic models (src/api/webhook_models.py).

Covers:
- PullRequestEvent: valid data, extra fields ignored, default values
- IssuesEvent: valid data, optional fields
- PingEvent: defaults
- PullRequestData: default flags and nested defaults
- RepositoryData: nested OwnerData
"""

from src.api.webhook_models import (
    BranchRef,
    IssuesEvent,
    OwnerData,
    PingEvent,
    PullRequestData,
    PullRequestEvent,
    RepositoryData,
    UserData,
)

# ── PullRequestEvent ──────────────────────────────────────────────────────


class TestPullRequestEvent:
    """Tests for PullRequestEvent model."""

    def test_valid_pull_request_event(self):
        """Constructs successfully with valid data."""
        data = {
            "action": "opened",
            "pull_request": {
                "number": 42,
                "user": {"login": "octocat"},
            },
            "repository": {
                "name": "my-repo",
                "owner": {"login": "octocat"},
            },
        }
        event = PullRequestEvent(**data)
        assert event.action == "opened"
        assert event.pull_request.number == 42
        assert event.repository.name == "my-repo"

    def test_extra_fields_ignored(self):
        """Extra fields are silently ignored per ConfigDict(extra='ignore')."""
        data = {
            "action": "closed",
            "pull_request": {
                "number": 1,
                "user": {"login": "bot"},
                "unknown_field": True,
            },
            "repository": {
                "name": "r",
                "owner": {"login": "o"},
                "extra_repo_field": 42,
            },
            "sender": {"login": "someone"},
        }
        event = PullRequestEvent(**data)
        assert event.action == "closed"
        assert not hasattr(event, "sender")

    def test_default_values_on_pull_request_data(self):
        """PullRequestData defaults: draft=False, merged=False, head=BranchRef()."""
        data = {
            "action": "opened",
            "pull_request": {
                "number": 5,
                "user": {"login": "dev"},
            },
            "repository": {
                "name": "repo",
                "owner": {"login": "org"},
            },
        }
        event = PullRequestEvent(**data)
        assert event.pull_request.draft is False
        assert event.pull_request.merged is False
        assert event.pull_request.head.ref == ""
        assert event.pull_request.body is None


# ── IssuesEvent ───────────────────────────────────────────────────────────


class TestIssuesEvent:
    """Tests for IssuesEvent model."""

    def test_valid_issues_event(self):
        """Constructs successfully with valid issue data."""
        data = {
            "action": "opened",
            "issue": {
                "number": 10,
                "title": "Bug report",
                "body": "Something is broken",
                "user": {"login": "reporter"},
            },
            "repository": {
                "name": "my-repo",
                "owner": {"login": "org"},
            },
        }
        event = IssuesEvent(**data)
        assert event.action == "opened"
        assert event.issue.number == 10
        assert event.issue.title == "Bug report"

    def test_optional_fields_default_to_none(self):
        """title, body, and user are optional and default to None."""
        data = {
            "action": "closed",
            "issue": {"number": 99},
            "repository": {
                "name": "r",
                "owner": {"login": "o"},
            },
        }
        event = IssuesEvent(**data)
        assert event.issue.title is None
        assert event.issue.body is None
        assert event.issue.user is None

    def test_issue_with_user(self):
        """Issue with explicit user parses correctly."""
        data = {
            "action": "edited",
            "issue": {
                "number": 7,
                "user": {"login": "alice"},
            },
            "repository": {
                "name": "repo",
                "owner": {"login": "org"},
            },
        }
        event = IssuesEvent(**data)
        assert event.issue.user.login == "alice"


# ── PingEvent ─────────────────────────────────────────────────────────────


class TestPingEvent:
    """Tests for PingEvent model."""

    def test_ping_defaults(self):
        """Default zen is empty string, hook_id is None."""
        event = PingEvent()
        assert event.zen == ""
        assert event.hook_id is None

    def test_ping_with_values(self):
        """Ping with explicit values."""
        event = PingEvent(zen="Keep it simple", hook_id=123456)
        assert event.zen == "Keep it simple"
        assert event.hook_id == 123456


# ── PullRequestData ───────────────────────────────────────────────────────


class TestPullRequestData:
    """Tests for PullRequestData model in isolation."""

    def test_defaults(self):
        """draft=False, merged=False, default head BranchRef."""
        pr = PullRequestData(number=1, user=UserData(login="dev"))
        assert pr.draft is False
        assert pr.merged is False
        assert isinstance(pr.head, BranchRef)
        assert pr.head.ref == ""

    def test_with_head_branch(self):
        """Head branch ref is preserved."""
        pr = PullRequestData(
            number=2,
            user=UserData(login="dev"),
            head=BranchRef(ref="feature/x"),
        )
        assert pr.head.ref == "feature/x"


# ── RepositoryData ────────────────────────────────────────────────────────


class TestRepositoryData:
    """Tests for RepositoryData model."""

    def test_nested_owner(self):
        """RepositoryData correctly parses nested OwnerData."""
        repo = RepositoryData(name="my-repo", owner=OwnerData(login="org"))
        assert repo.name == "my-repo"
        assert repo.owner.login == "org"

    def test_from_dict(self):
        """Constructs from nested dict."""
        repo = RepositoryData(**{"name": "r", "owner": {"login": "o"}})
        assert repo.owner.login == "o"
