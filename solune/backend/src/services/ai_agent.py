"""AI agent service for task generation and intent detection.

Supports multiple LLM providers:
- GitHub Copilot (default): Uses Copilot SDK with user's OAuth token
- Azure OpenAI (optional): Uses Azure OpenAI with static API keys

Microsoft Agent Framework (agent-framework-core) is available as a dependency
for advanced orchestration patterns.
"""

import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from src.logging_utils import get_logger, handle_service_error
from src.models.recommendation import (
    IssueMetadata,
    IssuePriority,
    IssueRecommendation,
    IssueSize,
    RecommendationStatus,
)
from src.prompts.issue_generation import (
    create_feature_request_detection_prompt,
    create_issue_generation_prompt,
)
from src.prompts.task_generation import (
    create_status_change_prompt,
    create_task_generation_prompt,
)
from src.prompts.transcript_analysis import create_transcript_analysis_prompt
from src.services.completion_providers import (
    CompletionProvider,
    create_completion_provider,
)
from src.utils import utcnow

logger = get_logger(__name__)


@dataclass
class GeneratedTask:
    """AI-generated task with title and description."""

    title: str
    description: str


@dataclass
class StatusChangeIntent:
    """Detected status change intent from user input."""

    task_reference: str
    target_status: str
    confidence: float


class AIAgentService:
    """Service for AI-powered task generation and intent detection.

    Uses a pluggable CompletionProvider for LLM calls:
    - CopilotCompletionProvider (default): GitHub Copilot via user's OAuth token
    - AzureOpenAICompletionProvider (optional): Azure OpenAI with static keys

    Set AI_PROVIDER env var to select the provider ("copilot" or "azure_openai").
    """

    def __init__(self, provider: CompletionProvider | None = None):
        if provider is not None:
            self._provider = provider
        else:
            self._provider = create_completion_provider()
        logger.info("AIAgentService initialized with provider: %s", self._provider.name)

    async def _call_completion(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        github_token: str | None = None,
    ) -> str:
        """Call the completion API using the configured provider.

        Args:
            messages: Chat messages [{"role": "system"|"user", "content": "..."}]
            temperature: Sampling temperature
            max_tokens: Maximum response tokens
            github_token: GitHub OAuth token (required for Copilot provider)

        Returns:
            The assistant's response content
        """
        return await self._provider.complete(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            github_token=github_token,
        )

    # ──────────────────────────────────────────────────────────────────
    # Issue Recommendation Methods (T011, T012, T013)
    # ──────────────────────────────────────────────────────────────────

    async def detect_feature_request_intent(
        self, user_input: str, github_token: str | None = None
    ) -> bool:
        """
        Detect if user input is a feature request (T013).

        Args:
            user_input: User's message
            github_token: GitHub OAuth token (required for Copilot provider)

        Returns:
            True if this appears to be a feature request
        """
        prompt_messages = create_feature_request_detection_prompt(user_input)

        try:
            messages = [
                {"role": "system", "content": prompt_messages[0]["content"]},
                {"role": "user", "content": prompt_messages[1]["content"]},
            ]

            content = await self._call_completion(
                messages, temperature=0.3, max_tokens=200, github_token=github_token
            )
            logger.debug("Feature request detection response: %s", content)

            data = self._parse_json_response(content)

            if data.get("intent") == "feature_request":
                confidence = float(data.get("confidence", 0))
                if confidence >= 0.6:
                    logger.info("Detected feature request with confidence: %.2f", confidence)
                    return True

            return False

        except Exception as e:
            logger.warning("Failed to detect feature request intent: %s", e)
            return False

    async def generate_issue_recommendation(
        self,
        user_input: str,
        project_name: str,
        session_id: str,
        github_token: str | None = None,
        metadata_context: dict | None = None,
    ) -> IssueRecommendation:
        """
        Generate a structured issue recommendation from feature request (T011).

        Args:
            user_input: User's feature request description
            project_name: Name of the target project for context
            session_id: Current session ID
            github_token: GitHub OAuth token (required for Copilot provider)
            metadata_context: Optional repo metadata (labels, branches, milestones,
                collaborators) to inject into the AI prompt.

        Returns:
            IssueRecommendation with AI-generated content

        Raises:
            ValueError: If AI response cannot be parsed
        """
        prompt_messages = create_issue_generation_prompt(
            user_input, project_name, metadata_context=metadata_context
        )

        try:
            messages = [
                {"role": "system", "content": prompt_messages[0]["content"]},
                {"role": "user", "content": prompt_messages[1]["content"]},
            ]

            content = await self._call_completion(
                messages, temperature=0.7, max_tokens=8000, github_token=github_token
            )
            logger.debug("Issue recommendation response: %s", content[:500])

            return self._parse_issue_recommendation_response(
                content, user_input, session_id, metadata_context=metadata_context
            )

        except Exception as e:
            # NOTE(001-code-quality-tech-debt): ValueError is used here
            # deliberately instead of an AppException subclass. Changing to
            # AppException would silently alter the API error-response shape
            # seen by callers. The string-based classification below is
            # fragile tech debt but must be preserved for behavioral
            # equivalence.
            error_msg = str(e)
            if "401" in error_msg or "Access denied" in error_msg:
                raise ValueError(
                    "AI provider authentication failed. Check your credentials "
                    "(GitHub OAuth token for Copilot, or API key for Azure OpenAI)."
                ) from e
            elif "404" in error_msg or "Resource not found" in error_msg:
                raise ValueError(
                    "AI model/deployment not found. Verify your provider configuration."
                ) from e
            else:
                handle_service_error(e, "generate recommendation", ValueError)

    async def analyze_transcript(
        self,
        transcript_content: str,
        project_name: str,
        session_id: str,
        github_token: str | None = None,
        metadata_context: dict | None = None,
    ) -> IssueRecommendation:
        """Analyse a meeting transcript and return an issue recommendation.

        Sends the transcript through the Transcribe agent prompt and parses
        the AI response into an ``IssueRecommendation``.

        Args:
            transcript_content: Raw transcript text.
            project_name: Name of the target project for context.
            session_id: Current session ID.
            github_token: GitHub OAuth token (required for Copilot provider).
            metadata_context: Optional repo metadata for prompt enrichment.

        Returns:
            IssueRecommendation with AI-generated content extracted from the
            transcript.

        Raises:
            ValueError: If AI response cannot be parsed.
        """
        prompt_messages = create_transcript_analysis_prompt(
            transcript_content, project_name, metadata_context=metadata_context
        )

        try:
            messages = [
                {"role": "system", "content": prompt_messages[0]["content"]},
                {"role": "user", "content": prompt_messages[1]["content"]},
            ]

            content = await self._call_completion(
                messages, temperature=0.7, max_tokens=8000, github_token=github_token
            )
            logger.debug("Transcript analysis response: %s", content[:500])

            # Use truncated transcript as original_input (max 500 chars)
            original_input = transcript_content[:500]
            recommendation = self._parse_issue_recommendation_response(
                content, original_input, session_id, metadata_context=metadata_context
            )
            # Preserve the full transcript in original_context (the parser
            # copies original_input into original_context, but for transcripts
            # we want the complete text available for downstream use).
            recommendation.original_context = transcript_content
            return recommendation

        except Exception as e:
            # NOTE(001-code-quality-tech-debt): ValueError preserved for
            # backward compatibility — see note in generate_issue_recommendation.
            error_msg = str(e)
            if "401" in error_msg or "Access denied" in error_msg:
                raise ValueError(
                    "AI provider authentication failed. Check your credentials "
                    "(GitHub OAuth token for Copilot, or API key for Azure OpenAI)."
                ) from e
            elif "404" in error_msg or "Resource not found" in error_msg:
                raise ValueError(
                    "AI model/deployment not found. Verify your provider configuration."
                ) from e
            else:
                handle_service_error(e, "analyse transcript", ValueError)

    def _parse_issue_recommendation_response(
        self,
        content: str,
        original_input: str,
        session_id: str,
        metadata_context: dict | None = None,
    ) -> IssueRecommendation:
        """
        Parse AI response into IssueRecommendation model (T012).

        Args:
            content: Raw AI response
            original_input: User's original input
            session_id: Current session ID
            metadata_context: Optional repo metadata for label validation

        Returns:
            IssueRecommendation instance

        Raises:
            ValueError: If response is invalid
        """
        data = self._parse_json_response(content)

        title = data.get("title", "").strip()
        user_story = data.get("user_story", "").strip()
        ui_ux_description = data.get("ui_ux_description", "").strip()
        functional_requirements = data.get("functional_requirements", [])
        technical_notes = data.get("technical_notes", "").strip()

        # Validate required fields
        if not title:
            raise ValueError("AI response missing title")
        if not user_story:
            raise ValueError("AI response missing user_story")
        if not functional_requirements or len(functional_requirements) < 1:
            raise ValueError("AI response missing functional_requirements")

        # Enforce max lengths
        if len(title) > 256:
            title = title[:253] + "..."

        # Always use the user's actual input as original_context (not from AI response)
        original_context = original_input

        # Parse metadata with defaults
        metadata = self._parse_issue_metadata(
            data.get("metadata", {}), metadata_context=metadata_context
        )

        return IssueRecommendation(
            session_id=UUID(session_id),
            original_input=original_input,
            original_context=original_context,
            title=title,
            user_story=user_story,
            ui_ux_description=ui_ux_description or "No UI/UX description provided.",
            functional_requirements=functional_requirements,
            technical_notes=technical_notes,
            metadata=metadata,
            status=RecommendationStatus.PENDING,
        )

    def _parse_issue_metadata(
        self,
        metadata_data: dict,
        metadata_context: dict | None = None,
    ) -> IssueMetadata:
        """
        Parse metadata from AI response with safe defaults.

        Args:
            metadata_data: Raw metadata dict from AI response
            metadata_context: Optional repo metadata with real label names.
                When provided, labels are validated against the actual
                repository label set instead of the hardcoded constants.

        Returns:
            IssueMetadata instance with validated values
        """

        # Parse priority with default
        priority_str = metadata_data.get("priority", "P2").upper()
        try:
            priority = IssuePriority(priority_str)
        except ValueError:
            priority = IssuePriority.P2
            logger.warning("Invalid priority '%s', defaulting to P2", priority_str)

        # Parse size with default
        size_str = metadata_data.get("size", "M").upper()
        try:
            size = IssueSize(size_str)
        except ValueError:
            size = IssueSize.M
            logger.warning("Invalid size '%s', defaulting to M", size_str)

        # Parse estimate hours with bounds
        estimate_hours = metadata_data.get("estimate_hours", 4.0)
        try:
            estimate_hours = float(estimate_hours)
            estimate_hours = max(0.5, min(40.0, estimate_hours))
        except (ValueError, TypeError):
            estimate_hours = 4.0

        # Parse dates with defaults
        today = utcnow()
        start_date = metadata_data.get("start_date", "")
        target_date = metadata_data.get("target_date", "")

        # Validate date format (YYYY-MM-DD)
        if start_date and not self._is_valid_date(start_date):
            start_date = today.strftime("%Y-%m-%d")
        if not start_date:
            start_date = today.strftime("%Y-%m-%d")

        if target_date and not self._is_valid_date(target_date):
            # Calculate based on size
            target_date = self._calculate_target_date(today, size)
        if not target_date:
            target_date = self._calculate_target_date(today, size)

        # Parse labels with default - validate against known labels
        labels = metadata_data.get("labels", [])
        if not isinstance(labels, list):
            labels = ["ai-generated"]

        # Build the set of valid labels.  When repo metadata is available
        # (dynamic context), use the actual repo labels so that AI-selected
        # repo-specific labels are preserved.  Fall back to the hardcoded
        # constants list when no metadata context is provided.
        from src.constants import LABELS

        valid_label_set: set[str] = set(LABELS)
        if metadata_context:
            repo_labels = metadata_context.get("labels", [])
            for lb in repo_labels:
                name = lb["name"] if isinstance(lb, dict) else lb
                if isinstance(name, str):
                    valid_label_set.add(name.lower())

        validated_labels = []
        for label in labels:
            if isinstance(label, str):
                label_lower = label.lower()
                if label_lower in valid_label_set:
                    validated_labels.append(label_lower)
                else:
                    logger.debug("Skipping invalid label: %s", label)

        # Ensure ai-generated is always present
        if "ai-generated" not in validated_labels:
            validated_labels.insert(0, "ai-generated")

        # If no type label was selected, default to "feature"
        type_labels = [
            "feature",
            "bug",
            "enhancement",
            "refactor",
            "documentation",
            "testing",
            "infrastructure",
        ]
        has_type = any(lbl in validated_labels for lbl in type_labels)
        if not has_type:
            validated_labels.append("feature")

        return IssueMetadata(
            priority=priority,
            size=size,
            estimate_hours=estimate_hours,
            start_date=start_date,
            target_date=target_date,
            labels=validated_labels,
            assignees=self._parse_string_list(metadata_data.get("assignees")),
            milestone=self._parse_optional_string(metadata_data.get("milestone")),
            branch=self._parse_optional_string(metadata_data.get("branch")),
        )

    def _is_valid_date(self, date_str: str) -> bool:
        """Check if date string is valid YYYY-MM-DD format."""
        try:
            from datetime import datetime

            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def _calculate_target_date(self, start: datetime, size: IssueSize) -> str:
        """Calculate target date based on size estimate."""
        from datetime import timedelta

        days_map = {
            IssueSize.XS: 0,  # Same day
            IssueSize.S: 0,  # Same day
            IssueSize.M: 1,  # Next day
            IssueSize.L: 2,  # 2 days
            IssueSize.XL: 4,  # 4 days
        }
        days = days_map.get(size, 1)
        target = start + timedelta(days=days)
        return target.strftime("%Y-%m-%d")

    @staticmethod
    def _parse_string_list(value: Any) -> list[str]:
        """Parse a value into a list of strings, returning empty list on failure."""
        if isinstance(value, list):
            return [str(v) for v in value if isinstance(v, str) and v.strip()]
        return []

    @staticmethod
    def _parse_optional_string(value: Any) -> str | None:
        """Parse a value into an optional string, returning None on failure."""
        if isinstance(value, str) and value.strip():
            return value.strip()
        return None

    # ──────────────────────────────────────────────────────────────────
    # Title Generation (metadata-only path for ai_enhance=False)
    # ──────────────────────────────────────────────────────────────────

    async def generate_title_from_description(
        self,
        user_input: str,
        project_name: str,
        github_token: str | None = None,
    ) -> str:
        """Generate a concise issue title from raw user input.

        Used when AI Enhance is disabled to generate only the title
        while preserving the user's exact input as the description.

        Args:
            user_input: User's raw chat input
            project_name: Name of the target project for context
            github_token: GitHub OAuth token (required for Copilot provider)

        Returns:
            A concise issue title string capped at 80 characters total.
            Falls back to truncated user input with an ellipsis if the
            AI call fails.
        """
        try:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a concise title generator for GitHub issues. "
                        f"Project: {project_name}. "
                        "Given a user's description, generate ONLY a short, clear "
                        "issue title (max 80 characters). "
                        "Return ONLY the title text, nothing else."
                    ),
                },
                {"role": "user", "content": user_input},
            ]

            title = await self._call_completion(
                messages, temperature=0.3, max_tokens=100, github_token=github_token
            )
            title = title.strip().strip('"').strip("'")

            if title:
                return self._truncate_title(title)

        except Exception as e:
            logger.warning("Failed to generate title from description: %s", e)

        return self._truncate_title(user_input)

    @staticmethod
    def _truncate_title(title: str) -> str:
        """Truncate a title to 80 characters total, adding an ellipsis when needed."""
        if len(title) > 80:
            return title[:77] + "..."
        return title

    # ──────────────────────────────────────────────────────────────────
    # Existing Task Generation Methods
    # ──────────────────────────────────────────────────────────────────

    async def generate_task_from_description(
        self, user_input: str, project_name: str, github_token: str | None = None
    ) -> GeneratedTask:
        """
        Generate a structured task from natural language description.

        Args:
            user_input: User's natural language task description
            project_name: Name of the target project for context
            github_token: GitHub OAuth token (required for Copilot provider)

        Returns:
            GeneratedTask with title and description

        Raises:
            ValueError: If AI response cannot be parsed
        """
        prompt_messages = create_task_generation_prompt(user_input, project_name)

        try:
            messages = [
                {"role": "system", "content": prompt_messages[0]["content"]},
                {"role": "user", "content": prompt_messages[1]["content"]},
            ]

            content = await self._call_completion(
                messages, temperature=0.7, max_tokens=1000, github_token=github_token
            )
            logger.debug("AI response: %s", content[:200] if content else "None")

            # Parse JSON response
            task_data = self._parse_json_response(content)
            return self._validate_generated_task(task_data)

        except Exception as e:
            # NOTE(001-code-quality-tech-debt): ValueError preserved for
            # backward compatibility — see note in generate_issue_recommendation.
            error_msg = str(e)
            if "401" in error_msg or "Access denied" in error_msg:
                raise ValueError(
                    "AI provider authentication failed. Check your credentials "
                    "(GitHub OAuth token for Copilot, or API key for Azure OpenAI). "
                    f"Original error: {error_msg}"
                ) from e
            elif "404" in error_msg or "Resource not found" in error_msg:
                raise ValueError(
                    f"AI model/deployment not found. Verify your provider configuration. "
                    f"Original error: {error_msg}"
                ) from e
            else:
                handle_service_error(e, "generate task", ValueError)

    async def parse_status_change_request(
        self,
        user_input: str,
        available_tasks: list[str],
        available_statuses: list[str],
        github_token: str | None = None,
    ) -> StatusChangeIntent | None:
        """
        Parse user input to detect status change intent.

        Args:
            user_input: User's message
            available_tasks: List of task titles in the project
            available_statuses: List of available status options
            github_token: GitHub OAuth token (required for Copilot provider)

        Returns:
            StatusChangeIntent if detected with high confidence, None otherwise
        """
        prompt_messages = create_status_change_prompt(
            user_input, available_tasks, available_statuses
        )

        try:
            messages = [
                {"role": "system", "content": prompt_messages[0]["content"]},
                {"role": "user", "content": prompt_messages[1]["content"]},
            ]

            content = await self._call_completion(
                messages, temperature=0.3, max_tokens=200, github_token=github_token
            )
            logger.debug("Status intent response: %s", content)

            data = self._parse_json_response(content)

            if data.get("intent") != "status_change":
                return None

            confidence = float(data.get("confidence", 0))
            if confidence < 0.5:
                logger.info("Low confidence status change intent: %.2f", confidence)
                return None

            return StatusChangeIntent(
                task_reference=data.get("task_reference", ""),
                target_status=data.get("target_status", ""),
                confidence=confidence,
            )

        except Exception as e:
            logger.warning("Failed to parse status change intent: %s", e)
            return None

    def identify_target_task(self, task_reference: str, available_tasks: list[Any]) -> Any | None:
        """
        Find the best matching task for a reference string.

        Args:
            task_reference: Reference string from AI (partial title/description)
            available_tasks: List of task objects with a 'title' attribute

        Returns:
            Best matching task or None
        """
        if not task_reference or not available_tasks:
            return None

        reference_lower = task_reference.lower()

        # Exact match
        for task in available_tasks:
            if task.title.lower() == reference_lower:
                return task

        # Partial match
        matches = []
        for task in available_tasks:
            title_lower = task.title.lower()
            if reference_lower in title_lower or title_lower in reference_lower:
                matches.append(task)

        if len(matches) == 1:
            return matches[0]

        # Fuzzy match - find task with most word overlap
        ref_words = set(reference_lower.split())
        best_match = None
        best_score = 0

        for task in available_tasks:
            title_words = set(task.title.lower().split())
            overlap = len(ref_words & title_words)
            if overlap > best_score:
                best_score = overlap
                best_match = task

        return best_match if best_score > 0 else None

    def _parse_json_response(self, content: str) -> dict:
        """Parse JSON from AI response, handling markdown code blocks, extra text, and truncation."""
        content = content.strip()

        # Remove markdown code blocks if present
        if "```" in content:
            # Try to extract content from a complete code fence first
            match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", content, re.DOTALL)
            if match:
                content = match.group(1).strip()
            else:
                # Truncated response: strip opening fence without a closing one
                content = re.sub(r"^```(?:json)?\s*\n?", "", content).strip()

        # Try direct parse first
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Try to extract the first JSON object from the text
        # Find the first '{' and match to its closing '}'
        start = content.find("{")
        if start != -1:
            depth = 0
            in_string = False
            escape_next = False
            for i in range(start, len(content)):
                c = content[i]
                if escape_next:
                    escape_next = False
                    continue
                if c == "\\":
                    if in_string:
                        escape_next = True
                    continue
                if c == '"' and not escape_next:
                    in_string = not in_string
                    continue
                if in_string:
                    continue
                if c == "{":
                    depth += 1
                elif c == "}":
                    depth -= 1
                    if depth == 0:
                        candidate = content[start : i + 1]
                        try:
                            return json.loads(candidate)
                        except json.JSONDecodeError:
                            break

            # If we get here, JSON is likely truncated - attempt repair
            repaired = self._repair_truncated_json(content[start:])
            if repaired is not None:
                logger.warning("Parsed response using JSON truncation repair")
                return repaired

        logger.error("Failed to parse JSON from response content: %s", content[:500])
        raise ValueError("Invalid JSON response: could not extract JSON object")

    def _repair_truncated_json(self, content: str) -> dict | None:
        """Attempt to repair truncated JSON by closing open strings, arrays, and objects."""
        # Walk the content tracking nesting state
        in_string = False
        escape_next = False
        stack: list[str] = []  # '{' or '['

        for c in content:
            if escape_next:
                escape_next = False
                continue
            if c == "\\" and in_string:
                escape_next = True
                continue
            if c == '"' and not escape_next:
                in_string = not in_string
                continue
            if in_string:
                continue
            if c == "{":
                stack.append("{")
            elif c == "[":
                stack.append("[")
            elif c == "}":
                if stack and stack[-1] == "{":
                    stack.pop()
            elif c == "]":
                if stack and stack[-1] == "[":
                    stack.pop()

        # Build repair suffix
        repair = ""
        if in_string:
            repair += '"'  # close open string
        # Close any open arrays/objects in reverse order
        for bracket in reversed(stack):
            repair += "]" if bracket == "[" else "}"

        if not repair:
            return None  # content wasn't actually truncated in a fixable way

        candidate = content + repair
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            # Try more aggressively: trim back to the last complete key-value
            # Find last comma or colon before truncation point
            trimmed = content.rstrip()
            for cutoff_char in [",", ":", '"']:
                idx = trimmed.rfind(cutoff_char)
                if idx > 0:
                    # Try trimming to just before the incomplete entry
                    attempt = trimmed[:idx].rstrip().rstrip(",")
                    suffix = ""
                    if in_string:
                        # Already handled above; recompute for trimmed
                        pass
                    # Recount stack for trimmed version
                    s_in_str = False
                    s_escape = False
                    s_stack: list[str] = []
                    for ch in attempt:
                        if s_escape:
                            s_escape = False
                            continue
                        if ch == "\\" and s_in_str:
                            s_escape = True
                            continue
                        if ch == '"' and not s_escape:
                            s_in_str = not s_in_str
                            continue
                        if s_in_str:
                            continue
                        if ch == "{":
                            s_stack.append("{")
                        elif ch == "[":
                            s_stack.append("[")
                        elif ch == "}":
                            if s_stack and s_stack[-1] == "{":
                                s_stack.pop()
                        elif ch == "]":
                            if s_stack and s_stack[-1] == "[":
                                s_stack.pop()
                    if s_in_str:
                        suffix += '"'
                    for bracket in reversed(s_stack):
                        suffix += "]" if bracket == "[" else "}"
                    try:
                        return json.loads(attempt + suffix)
                    except json.JSONDecodeError:
                        continue
            return None

    def _validate_generated_task(self, data: dict) -> GeneratedTask:
        """Validate and create GeneratedTask from parsed data."""
        title = data.get("title", "").strip()
        description = data.get("description", "").strip()

        if not title:
            raise ValueError("Generated task missing title")

        # Enforce max lengths
        if len(title) > 256:
            title = title[:253] + "..."

        if len(description) > 65535:
            description = description[:65532] + "..."

        return GeneratedTask(title=title, description=description)

    # ──────────────────────────────────────────────────────────────────
    # Agent Creator Methods
    # ──────────────────────────────────────────────────────────────────

    async def generate_agent_config(
        self,
        description: str,
        status_column: str,
        github_token: str | None = None,
    ) -> dict:
        """Generate an agent configuration from a natural language description.

        Calls the LLM with a structured prompt and returns a dict with
        ``name``, ``description``, and ``system_prompt`` keys.
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert at designing GitHub Custom Agents (also known as Copilot "
                    "coding agents). These agents are defined as Markdown files in "
                    ".github/agents/ and invoked via slash commands in GitHub Issues/PRs.\n\n"
                    "Given a user's description of what an agent should do, generate a JSON object with:\n"
                    '- "name": A concise kebab-case slug for the agent (lowercase, '
                    'hyphen-separated; e.g., "pr-architect-reviewer", "security-scanner", '
                    '"docs-updater"). '
                    "This becomes the filename slug and slash-command name.\n"
                    '- "description": A one-line summary of the agent\'s purpose (used in the '
                    "agent file's YAML frontmatter description field)\n"
                    '- "system_prompt": A detailed system prompt written as Markdown. This is the '
                    "full body of the agent definition file. Structure it with ## headings, "
                    "numbered execution steps, and clear instructions. Include a ## User Input "
                    "section at the top with `$ARGUMENTS` placeholder. Be specific and actionable. "
                    "The prompt should tell the agent exactly what to do step by step.\n"
                    '- "tools": A list of GitHub MCP tool identifiers the agent needs '
                    '(e.g., ["github/github-mcp-server/issue_write", '
                    '"github/github-mcp-server/search_code"]). '
                    "Only include tools if the agent genuinely needs specific MCP server tools. "
                    "An empty list is fine for agents that only need standard file/code access.\n\n"
                    "Respond ONLY with valid JSON, no markdown fences or extra text."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Create an agent that: {description}\n"
                    f"This agent will be assigned to the '{status_column}' status column."
                ),
            },
        ]

        content = await self._call_completion(
            messages, temperature=0.7, max_tokens=2000, github_token=github_token
        )
        result = self._parse_json_response(content)

        # Validate required keys
        for key in ("name", "description", "system_prompt"):
            if key not in result:
                raise ValueError(f"Generated config missing required key: {key}")

        return result

    async def edit_agent_config(
        self,
        current_config: dict,
        edit_instruction: str,
        github_token: str | None = None,
    ) -> dict:
        """Apply a natural language edit to an existing agent configuration.

        Sends the current config + edit instruction to the LLM for targeted
        modification and returns the updated config dict.
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert at designing GitHub Custom Agents. "
                    "The user wants to modify an existing agent configuration. "
                    "Apply the requested change and return the complete updated JSON object with "
                    'the same keys: "name" (kebab-case slug), "description" (one-line summary), '
                    '"system_prompt" (Markdown body with ## headings and steps), '
                    'and "tools" (list of MCP tool identifiers, can be empty).\n'
                    "Respond ONLY with valid JSON, no markdown fences or extra text."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Current configuration:\n{json.dumps(current_config, indent=2)}\n\n"
                    f"Requested change: {edit_instruction}"
                ),
            },
        ]

        content = await self._call_completion(
            messages, temperature=0.7, max_tokens=2000, github_token=github_token
        )
        result = self._parse_json_response(content)

        for key in ("name", "description", "system_prompt"):
            if key not in result:
                raise ValueError(f"Edited config missing required key: {key}")

        return result


# Global service instance (lazy initialization)
_ai_agent_service_instance: AIAgentService | None = None


def get_ai_agent_service() -> AIAgentService:
    """Get or create the global AI agent service instance.

    The provider is selected based on AI_PROVIDER env var:
    - "copilot" (default): GitHub Copilot via user's OAuth token
    - "azure_openai": Azure OpenAI with static API keys

    For the Copilot provider, no startup credentials are needed - the user's
    GitHub OAuth token is passed per-request.
    """
    global _ai_agent_service_instance
    if _ai_agent_service_instance is None:
        _ai_agent_service_instance = AIAgentService()
    return _ai_agent_service_instance


def reset_ai_agent_service() -> None:
    """Reset the global AI agent service instance (useful for testing)."""
    global _ai_agent_service_instance
    _ai_agent_service_instance = None
