"""Unit tests for board API endpoints and models."""

from src.models.board import (
    Assignee,
    BoardColumn,
    BoardDataResponse,
    BoardItem,
    BoardProject,
    BoardProjectListResponse,
    ContentType,
    CustomFieldValue,
    LinkedPR,
    PRState,
    Repository,
    StatusColor,
    StatusField,
    StatusOption,
)

# ============ Model Tests ============


class TestBoardModels:
    """Tests for board Pydantic models."""

    def test_status_color_enum_values(self):
        """StatusColor enum should contain all GitHub predefined colors."""
        expected = {"GRAY", "BLUE", "GREEN", "YELLOW", "ORANGE", "RED", "PINK", "PURPLE"}
        actual = {c.value for c in StatusColor}
        assert actual == expected

    def test_content_type_enum_values(self):
        """ContentType enum should have issue, draft_issue, pull_request."""
        expected = {"issue", "draft_issue", "pull_request"}
        actual = {c.value for c in ContentType}
        assert actual == expected

    def test_pr_state_enum_values(self):
        """PRState enum should have open, closed, merged."""
        expected = {"open", "closed", "merged"}
        actual = {c.value for c in PRState}
        assert actual == expected

    def test_status_option_creation(self):
        """Should create a StatusOption with all fields."""
        opt = StatusOption(
            option_id="f75ad846",
            name="In Progress",
            color=StatusColor.YELLOW,
            description="Work in progress",
        )
        assert opt.option_id == "f75ad846"
        assert opt.name == "In Progress"
        assert opt.color == StatusColor.YELLOW
        assert opt.description == "Work in progress"

    def test_status_option_optional_description(self):
        """StatusOption description should be optional."""
        opt = StatusOption(
            option_id="abc123",
            name="Todo",
            color=StatusColor.GRAY,
        )
        assert opt.description is None

    def test_board_project_creation(self):
        """Should create a BoardProject with status field."""
        project = BoardProject(
            project_id="PVT_kwDOBWNFuc4AAgab",
            name="Development Board",
            description="Sprint board",
            url="https://github.com/users/octocat/projects/1",
            owner_login="octocat",
            status_field=StatusField(
                field_id="PVTSSF_lADOBWNFuc4AAqzs",
                options=[
                    StatusOption(option_id="opt1", name="Todo", color=StatusColor.GRAY),
                    StatusOption(option_id="opt2", name="Done", color=StatusColor.GREEN),
                ],
            ),
        )
        assert project.project_id == "PVT_kwDOBWNFuc4AAgab"
        assert project.name == "Development Board"
        assert len(project.status_field.options) == 2

    def test_board_item_with_all_fields(self):
        """Should create a BoardItem with all metadata fields."""
        item = BoardItem(
            item_id="PVTI_abc123",
            content_id="I_xyz789",
            content_type=ContentType.ISSUE,
            title="Add project board feature",
            number=164,
            repository=Repository(owner="octocat", name="github-workflows"),
            url="https://github.com/octocat/github-workflows/issues/164",
            body="Implement the board feature",
            status="In Progress",
            status_option_id="opt2",
            assignees=[
                Assignee(
                    login="octocat",
                    avatar_url="https://avatars.githubusercontent.com/u/583231",
                ),
            ],
            priority=CustomFieldValue(name="P1", color=StatusColor.RED),
            size=CustomFieldValue(name="M"),
            estimate=5.0,
            linked_prs=[
                LinkedPR(
                    pr_id="PR_abc",
                    number=165,
                    title="Implement board UI",
                    state=PRState.OPEN,
                    url="https://github.com/octocat/repo/pull/165",
                ),
            ],
        )
        assert item.item_id == "PVTI_abc123"
        assert item.content_type == ContentType.ISSUE
        assert item.number == 164
        assert len(item.assignees) == 1
        assert item.priority.name == "P1"
        assert item.estimate == 5.0
        assert len(item.linked_prs) == 1

    def test_board_item_draft_issue(self):
        """Draft issues should have nullable fields."""
        item = BoardItem(
            item_id="PVTI_draft",
            content_type=ContentType.DRAFT_ISSUE,
            title="Draft task",
            status="Todo",
            status_option_id="opt1",
        )
        assert item.content_id is None
        assert item.number is None
        assert item.repository is None
        assert item.url is None
        assert item.body is None
        assert item.priority is None
        assert item.size is None
        assert item.estimate is None
        assert item.assignees == []
        assert item.linked_prs == []

    def test_board_column_defaults(self):
        """BoardColumn should have sensible defaults."""
        col = BoardColumn(
            status=StatusOption(option_id="opt1", name="Todo", color=StatusColor.GRAY),
        )
        assert col.items == []
        assert col.item_count == 0
        assert col.estimate_total == 0.0

    def test_board_column_with_items(self):
        """BoardColumn should calculate item_count and estimate_total."""
        items = [
            BoardItem(
                item_id="1",
                content_type=ContentType.ISSUE,
                title="Task 1",
                status="Todo",
                status_option_id="opt1",
                estimate=3.0,
            ),
            BoardItem(
                item_id="2",
                content_type=ContentType.ISSUE,
                title="Task 2",
                status="Todo",
                status_option_id="opt1",
                estimate=5.0,
            ),
        ]
        col = BoardColumn(
            status=StatusOption(option_id="opt1", name="Todo", color=StatusColor.GRAY),
            items=items,
            item_count=2,
            estimate_total=8.0,
        )
        assert col.item_count == 2
        assert col.estimate_total == 8.0

    def test_board_data_response(self):
        """Should create a complete BoardDataResponse."""
        project = BoardProject(
            project_id="PVT_test",
            name="Test Project",
            url="https://github.com/test/project",
            owner_login="test",
            status_field=StatusField(
                field_id="SF_test",
                options=[
                    StatusOption(option_id="opt1", name="Todo", color=StatusColor.GRAY),
                ],
            ),
        )
        columns = [
            BoardColumn(
                status=StatusOption(option_id="opt1", name="Todo", color=StatusColor.GRAY),
                items=[],
                item_count=0,
                estimate_total=0.0,
            ),
        ]
        response = BoardDataResponse(project=project, columns=columns)
        assert response.project.name == "Test Project"
        assert len(response.columns) == 1

    def test_board_project_list_response(self):
        """Should create a BoardProjectListResponse."""
        project = BoardProject(
            project_id="PVT_test",
            name="Test",
            url="https://github.com/test",
            owner_login="test",
            status_field=StatusField(field_id="SF_1", options=[]),
        )
        response = BoardProjectListResponse(projects=[project])
        assert len(response.projects) == 1

    def test_custom_field_value_optional_color(self):
        """CustomFieldValue color should be optional."""
        val = CustomFieldValue(name="P2")
        assert val.color is None

    def test_linked_pr_creation(self):
        """Should create LinkedPR with all required fields."""
        pr = LinkedPR(
            pr_id="PR_test",
            number=42,
            title="Fix bug",
            state=PRState.MERGED,
            url="https://github.com/test/repo/pull/42",
        )
        assert pr.number == 42
        assert pr.state == PRState.MERGED


class TestBuildBoardColumnsSubIssueFiltering:
    """_build_board_columns filters sub-issues using both ID matching and label detection."""

    @staticmethod
    def _make_board_item(
        item_id: str,
        content_id: str,
        status_option_id: str,
        labels: list | None = None,
        sub_issues: list | None = None,
        **kwargs,
    ) -> BoardItem:
        from src.models.board import Label, SubIssue

        return BoardItem(
            item_id=item_id,
            content_id=content_id,
            content_type=ContentType.ISSUE,
            title=kwargs.get("title", f"Issue {item_id}"),
            status=kwargs.get("status", "In Progress"),
            status_option_id=status_option_id,
            labels=[Label(id=f"L_{lbl}", name=lbl, color="ededed") for lbl in (labels or [])],
            sub_issues=[
                SubIssue(id=si, number=i + 1, title=f"Sub {si}", url="", state="open")
                for i, si in enumerate(sub_issues or [])
            ],
        )

    def test_filters_sub_issue_by_label(self):
        """Items with the 'sub-issue' label are excluded even if not in any parent's sub_issues."""
        from src.services.github_projects.board import BoardMixin

        opt = StatusOption(option_id="opt1", name="In Progress", color="YELLOW")
        parent = self._make_board_item("P1", "C_P1", "opt1", sub_issues=[])
        sub = self._make_board_item("S1", "C_S1", "opt1", labels=["sub-issue"])

        columns = BoardMixin._build_board_columns(
            [parent, sub],
            [opt],
            {
                "BoardColumn": BoardColumn,
                "StatusOption": StatusOption,
                "StatusColor": StatusColor,
            },
        )

        assert len(columns) == 1
        assert len(columns[0].items) == 1
        assert columns[0].items[0].item_id == "P1"

    def test_filters_sub_issue_by_parent_reference(self):
        """Items referenced in a parent's sub_issues list are excluded (legacy behaviour)."""
        from src.services.github_projects.board import BoardMixin

        opt = StatusOption(option_id="opt1", name="In Progress", color="YELLOW")
        parent = self._make_board_item("P1", "C_P1", "opt1", sub_issues=["C_S1"])
        sub = self._make_board_item("S1", "C_S1", "opt1")

        columns = BoardMixin._build_board_columns(
            [parent, sub],
            [opt],
            {
                "BoardColumn": BoardColumn,
                "StatusOption": StatusOption,
                "StatusColor": StatusColor,
            },
        )

        assert len(columns[0].items) == 1
        assert columns[0].items[0].item_id == "P1"

    def test_keeps_parent_issues_without_sub_issue_label(self):
        """Parent issues without the sub-issue label remain on the board."""
        from src.services.github_projects.board import BoardMixin

        opt = StatusOption(option_id="opt1", name="Todo", color="GRAY")
        parent = self._make_board_item("P1", "C_P1", "opt1", labels=["feature", "active"])

        columns = BoardMixin._build_board_columns(
            [parent],
            [opt],
            {
                "BoardColumn": BoardColumn,
                "StatusOption": StatusOption,
                "StatusColor": StatusColor,
            },
        )

        assert len(columns[0].items) == 1
