"""AI agent service for task generation and intent detection.

Supports multiple LLM providers:
- GitHub Copilot (default): Uses Copilot SDK with user's OAuth token
- Azure OpenAI (optional): Uses Azure OpenAI with static API keys

Microsoft Agent Framework (agent-framework-core) is available as a dependency
for advanced orchestration patterns.
"""

import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

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
from src.services.completion_providers import (
    CompletionProvider,
    create_completion_provider,
)
from src.utils import utcnow

logger = logging.getLogger(__name__)


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
    ) -> IssueRecommendation:
        """
        Generate a structured issue recommendation from feature request (T011).

        Args:
            user_input: User's feature request description
            project_name: Name of the target project for context
            session_id: Current session ID
            github_token: GitHub OAuth token (required for Copilot provider)

        Returns:
            IssueRecommendation with AI-generated content

        Raises:
            ValueError: If AI response cannot be parsed
        """
        prompt_messages = create_issue_generation_prompt(user_input, project_name)

        try:
            messages = [
                {"role": "system", "content": prompt_messages[0]["content"]},
                {"role": "user", "content": prompt_messages[1]["content"]},
            ]

            content = await self._call_completion(
                messages, temperature=0.7, max_tokens=8000, github_token=github_token
            )
            logger.debug("Issue recommendation response: %s", content[:500])

            return self._parse_issue_recommendation_response(content, user_input, session_id)

        except Exception as e:
            error_msg = str(e)
            logger.error("Failed to generate issue recommendation: %s", error_msg)

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
                raise ValueError(f"Failed to generate recommendation: {error_msg}") from e

    def _parse_issue_recommendation_response(
        self, content: str, original_input: str, session_id: str
    ) -> IssueRecommendation:
        """
        Parse AI response into IssueRecommendation model (T012).

        Args:
            content: Raw AI response
            original_input: User's original input
            session_id: Current session ID

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
        metadata = self._parse_issue_metadata(data.get("metadata", {}))

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

    def _parse_issue_metadata(self, metadata_data: dict) -> IssueMetadata:
        """
        Parse metadata from AI response with safe defaults.

        Args:
            metadata_data: Raw metadata dict from AI response

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

        # Parse labels with default - validate against pre-defined labels
        labels = metadata_data.get("labels", [])
        if not isinstance(labels, list):
            labels = ["ai-generated"]

        # Filter to only include valid pre-defined labels
        from src.constants import LABELS

        validated_labels = []
        for label in labels:
            if isinstance(label, str):
                label_lower = label.lower()
                if label_lower in LABELS:
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
            error_msg = str(e)
            logger.error("Failed to generate task: %s", error_msg)

            # Provide helpful error messages
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
                raise ValueError(f"Failed to generate task: {error_msg}") from e

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
