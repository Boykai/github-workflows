"""AI agent service for task generation using Azure OpenAI or Azure AI Foundry."""

import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from src.config import get_settings
from src.models.chat import (
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

logger = logging.getLogger(__name__)

# Azure OpenAI API version
AZURE_API_VERSION = "2024-02-15-preview"


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

    Supports both Azure OpenAI and Azure AI Foundry (Azure AI Inference SDK).
    """

    def __init__(self):
        settings = get_settings()
        self._deployment = settings.azure_openai_deployment
        self._client: Any = None
        self._use_azure_inference = False

        if not settings.azure_openai_endpoint or not settings.azure_openai_key:
            raise ValueError(
                "Azure OpenAI credentials not configured. "
                "Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY."
            )

        # Try Azure OpenAI SDK first (openai package)
        try:
            from openai import AzureOpenAI

            self._client = AzureOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_key,
                api_version=AZURE_API_VERSION,
            )
            self._use_azure_inference = False
            logger.info("Initialized Azure OpenAI client for deployment: %s", self._deployment)
        except ImportError:
            # Fall back to Azure AI Inference SDK
            from azure.ai.inference import ChatCompletionsClient
            from azure.core.credentials import AzureKeyCredential

            self._client = ChatCompletionsClient(
                endpoint=settings.azure_openai_endpoint,  # type: ignore[arg-type]
                credential=AzureKeyCredential(settings.azure_openai_key),  # type: ignore[arg-type]
            )
            self._use_azure_inference = True
            logger.info("Initialized Azure AI Inference client for model: %s", self._deployment)

    def _call_completion(
        self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 1000
    ) -> str:
        """Call the completion API using the appropriate SDK."""
        if self._use_azure_inference:
            from azure.ai.inference.models import SystemMessage, UserMessage

            response = self._client.complete(
                model=self._deployment,
                messages=[
                    (
                        SystemMessage(content=messages[0]["content"])
                        if messages[0]["role"] == "system"
                        else UserMessage(content=messages[0]["content"])
                    ),
                    UserMessage(content=messages[1]["content"]),
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
        else:
            response = self._client.chat.completions.create(
                model=self._deployment,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        return response.choices[0].message.content or ""

    # ──────────────────────────────────────────────────────────────────
    # Issue Recommendation Methods (T011, T012, T013)
    # ──────────────────────────────────────────────────────────────────

    async def detect_feature_request_intent(self, user_input: str) -> bool:
        """
        Detect if user input is a feature request (T013).

        Args:
            user_input: User's message

        Returns:
            True if this appears to be a feature request
        """
        prompt_messages = create_feature_request_detection_prompt(user_input)

        try:
            messages = [
                {"role": "system", "content": prompt_messages[0]["content"]},
                {"role": "user", "content": prompt_messages[1]["content"]},
            ]

            content = self._call_completion(messages, temperature=0.3, max_tokens=200)
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
        self, user_input: str, project_name: str, session_id: str
    ) -> IssueRecommendation:
        """
        Generate a structured issue recommendation from feature request (T011).

        Args:
            user_input: User's feature request description
            project_name: Name of the target project for context
            session_id: Current session ID

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

            content = self._call_completion(messages, temperature=0.7, max_tokens=2000)
            logger.debug("Issue recommendation response: %s", content[:500])

            return self._parse_issue_recommendation_response(content, user_input, session_id)

        except Exception as e:
            error_msg = str(e)
            logger.error("Failed to generate issue recommendation: %s", error_msg)

            if "401" in error_msg or "Access denied" in error_msg:
                raise ValueError(
                    "Azure OpenAI authentication failed. Please verify your API key."
                ) from e
            elif "404" in error_msg or "Resource not found" in error_msg:
                raise ValueError(f"Azure OpenAI deployment '{self._deployment}' not found.") from e
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

        # Parse metadata with defaults
        metadata = self._parse_issue_metadata(data.get("metadata", {}))

        return IssueRecommendation(
            session_id=UUID(session_id),
            original_input=original_input,
            title=title,
            user_story=user_story,
            ui_ux_description=ui_ux_description or "No UI/UX description provided.",
            functional_requirements=functional_requirements,
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
        from datetime import datetime

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
        today = datetime.now()
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
        from src.prompts.issue_generation import PREDEFINED_LABELS

        validated_labels = []
        for label in labels:
            if isinstance(label, str):
                label_lower = label.lower()
                if label_lower in PREDEFINED_LABELS:
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
        self, user_input: str, project_name: str
    ) -> GeneratedTask:
        """
        Generate a structured task from natural language description.

        Args:
            user_input: User's natural language task description
            project_name: Name of the target project for context

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

            content = self._call_completion(messages, temperature=0.7, max_tokens=1000)
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
                    "Azure OpenAI authentication failed. Please verify your API key and endpoint in .env file. "
                    f"Original error: {error_msg}"
                ) from e
            elif "404" in error_msg or "Resource not found" in error_msg:
                raise ValueError(
                    f"Azure OpenAI deployment '{self._deployment}' not found. "
                    "Please verify the AZURE_OPENAI_DEPLOYMENT name matches your Azure resource. "
                    f"Original error: {error_msg}"
                ) from e
            else:
                raise ValueError(f"Failed to generate task: {error_msg}") from e

    async def parse_status_change_request(
        self,
        user_input: str,
        available_tasks: list[str],
        available_statuses: list[str],
    ) -> StatusChangeIntent | None:
        """
        Parse user input to detect status change intent.

        Args:
            user_input: User's message
            available_tasks: List of task titles in the project
            available_statuses: List of available status options

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

            content = self._call_completion(messages, temperature=0.3, max_tokens=200)
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

    def identify_target_status(
        self, status_reference: str, available_statuses: list[str]
    ) -> str | None:
        """
        Find the best matching status for a reference string.

        Args:
            status_reference: Reference string from AI
            available_statuses: List of available status names

        Returns:
            Best matching status name or None
        """
        if not status_reference or not available_statuses:
            return None

        ref_lower = status_reference.lower().strip()

        # Exact match (case-insensitive)
        for status in available_statuses:
            if status.lower() == ref_lower:
                return status

        # Partial match
        for status in available_statuses:
            status_lower = status.lower()
            if ref_lower in status_lower or status_lower in ref_lower:
                return status

        # Common aliases
        aliases = {
            "todo": ["to do", "backlog", "not started"],
            "in progress": ["doing", "started", "working", "in-progress"],
            "done": ["complete", "completed", "finished", "closed"],
        }

        for status in available_statuses:
            status_key = status.lower()
            if status_key in aliases:
                for alias in aliases[status_key]:
                    if alias in ref_lower or ref_lower in alias:
                        return status

        return None

    def _parse_json_response(self, content: str) -> dict:
        """Parse JSON from AI response, handling markdown code blocks."""
        content = content.strip()

        # Remove markdown code blocks if present
        if content.startswith("```"):
            # Remove ```json or ``` at start
            content = re.sub(r"^```(?:json)?\s*\n?", "", content)
            # Remove ``` at end
            content = re.sub(r"\n?```\s*$", "", content)

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON: %s\nContent: %s", e, content[:500])
            raise ValueError(f"Invalid JSON response: {e}") from e

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
    """Get or create the global AI agent service instance."""
    global _ai_agent_service_instance
    if _ai_agent_service_instance is None:
        settings = get_settings()
        if not settings.azure_openai_endpoint or not settings.azure_openai_key:
            raise ValueError("Azure OpenAI credentials not configured")
        _ai_agent_service_instance = AIAgentService()
    return _ai_agent_service_instance
