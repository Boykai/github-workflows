"""Prompt templates for AI-assisted GitHub issue generation."""

from datetime import datetime, timedelta

# Pre-defined labels that can be assigned to issues
PREDEFINED_LABELS = [
    # Type labels (pick ONE primary type)
    "feature",  # New functionality
    "bug",  # Bug fix
    "enhancement",  # Improvement to existing feature
    "refactor",  # Code refactoring
    "documentation",  # Documentation updates
    "testing",  # Test-related work
    "infrastructure",  # DevOps, CI/CD, config
    # Scope labels (pick all that apply)
    "frontend",  # Frontend/UI work
    "backend",  # Backend/API work
    "database",  # Database changes
    "api",  # API changes
    # Domain labels (pick if relevant)
    "security",  # Security-related
    "performance",  # Performance optimization
    "accessibility",  # A11y improvements
    "ux",  # User experience
    # Auto-applied
    "ai-generated",  # Always included - marks AI-created issues
]

ISSUE_GENERATION_SYSTEM_PROMPT = """You are an expert product manager helping structure feature requests into well-organized GitHub issues.

When given a feature request, generate a structured GitHub issue with the following components:

1. **title**: A clear, concise title (max 256 characters) that summarizes the feature
2. **user_story**: A user story in the format "As a [user type], I want [goal] so that [benefit]"
3. **ui_ux_description**: Guidance for designers and developers on how the feature should look and behave
4. **functional_requirements**: An array of specific, testable requirements using "System MUST" or "System SHOULD" format
5. **metadata**: Project management metadata including:
   - **priority**: P0 (Critical), P1 (High), P2 (Medium), or P3 (Low)
   - **size**: T-shirt sizing - XS (<1hr), S (1-4hrs), M (4-8hrs/1day), L (1-3days), XL (3-5days)
   - **estimate_hours**: Numeric estimate in hours (0.5 to 40)
   - **labels**: Array of labels from the PRE-DEFINED list below

PRE-DEFINED LABELS (select from this list ONLY):
Type labels (pick ONE primary type):
- "feature" - New functionality
- "bug" - Bug fix
- "enhancement" - Improvement to existing feature
- "refactor" - Code refactoring
- "documentation" - Documentation updates
- "testing" - Test-related work
- "infrastructure" - DevOps, CI/CD, config

Scope labels (pick all that apply):
- "frontend" - Frontend/UI work
- "backend" - Backend/API work
- "database" - Database changes
- "api" - API changes

Domain labels (pick if relevant):
- "security" - Security-related
- "performance" - Performance optimization
- "accessibility" - A11y improvements
- "ux" - User experience

Auto-applied:
- "ai-generated" - ALWAYS include this label

IMPORTANT: An AI Coding Agent will implement this issue, so estimates should reflect automated development:
- Most features can be implemented in 1-8 hours by an AI agent
- Use XS/S for simple changes, M for typical features, L/XL for complex multi-file changes
- Keep estimates realistic but efficient for AI implementation

Guidelines:
- Title should be action-oriented and specific
- User story should clearly identify the user, their goal, and the value
- UI/UX description should include interaction patterns, visual elements, and user flows
- Functional requirements should be atomic, testable, and unambiguous
- Include at least 3 functional requirements per feature
- Priority: P0 for blockers, P1 for important features, P2 for standard work, P3 for nice-to-haves
- Labels: Always include "ai-generated", plus ONE type label, and relevant scope/domain labels

Output your response as valid JSON with these exact keys:
- title (string)
- user_story (string)
- ui_ux_description (string)
- functional_requirements (array of strings)
- metadata (object with priority, size, estimate_hours, labels)

Example output:
{
  "title": "Add CSV export functionality for user data",
  "user_story": "As a user, I want to export my data as CSV so that I can analyze it in spreadsheet applications.",
  "ui_ux_description": "Add an 'Export' button in the user profile section. Show a loading indicator during export. Download should trigger automatically when ready.",
  "functional_requirements": [
    "System MUST generate CSV with all user profile fields",
    "System MUST include timestamps in ISO 8601 format",
    "System MUST handle exports up to 10MB",
    "System SHOULD show progress indicator for large exports"
  ],
  "metadata": {
    "priority": "P2",
    "size": "M",
    "estimate_hours": 4,
    "labels": ["ai-generated", "feature", "backend", "api"]
  }
}
"""

FEATURE_REQUEST_DETECTION_PROMPT = """You are an intent classifier. Analyze the user input and determine if it's a feature request or something else.

A FEATURE REQUEST is when the user:
- Wants to add new functionality
- Describes a capability they need
- Uses phrases like "I need", "I want", "add feature", "implement", "build", "create a new"
- Describes a problem that needs a new solution

NOT a feature request:
- Status update requests ("move task to done", "mark as complete")
- Questions about existing functionality
- Bug reports without feature suggestions
- General conversation

Respond with JSON:
{
  "intent": "feature_request" or "other",
  "confidence": 0.0 to 1.0,
  "reasoning": "brief explanation"
}
"""


def create_issue_generation_prompt(user_input: str, project_name: str) -> list[dict]:
    """
    Create prompt messages for issue recommendation generation.

    Args:
        user_input: User's feature request description
        project_name: Name of the target GitHub project for context

    Returns:
        List of message dicts with role and content
    """
    # Calculate suggested dates (AI agent can complete quickly)
    today = datetime.now()
    start_date = today.strftime("%Y-%m-%d")
    # Default target is tomorrow for typical features
    default_target = (today + timedelta(days=1)).strftime("%Y-%m-%d")

    user_message = f"""Generate a structured GitHub issue for the following feature request.

Project Context: {project_name}
Today's Date: {start_date}
Suggested Start Date: {start_date}
Suggested Target Date: {default_target} (adjust based on size - XS/S: same day, M: +1 day, L: +2-3 days, XL: +4-5 days)

Feature Request:
{user_input}

Respond with a JSON object containing title, user_story, ui_ux_description, functional_requirements, and metadata (with priority, size, estimate_hours, labels).
Calculate appropriate start_date and target_date based on the size estimate."""

    return [
        {"role": "system", "content": ISSUE_GENERATION_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]


def create_feature_request_detection_prompt(user_input: str) -> list[dict]:
    """
    Create prompt messages for detecting feature request intent.

    Args:
        user_input: User's message

    Returns:
        List of message dicts with role and content
    """
    user_message = f"""Classify this user input:

"{user_input}"

Is this a feature request? Respond with JSON containing intent, confidence, and reasoning."""

    return [
        {"role": "system", "content": FEATURE_REQUEST_DETECTION_PROMPT},
        {"role": "user", "content": user_message},
    ]
