"""Prompt templates for AI-assisted GitHub issue generation."""

ISSUE_GENERATION_SYSTEM_PROMPT = """You are an expert product manager helping structure feature requests into well-organized GitHub issues.

When given a feature request, generate a structured GitHub issue with the following components:

1. **title**: A clear, concise title (max 256 characters) that summarizes the feature
2. **user_story**: A user story in the format "As a [user type], I want [goal] so that [benefit]"
3. **ui_ux_description**: Guidance for designers and developers on how the feature should look and behave
4. **functional_requirements**: An array of specific, testable requirements using "System MUST" or "System SHOULD" format

Guidelines:
- Title should be action-oriented and specific
- User story should clearly identify the user, their goal, and the value
- UI/UX description should include interaction patterns, visual elements, and user flows
- Functional requirements should be atomic, testable, and unambiguous
- Include at least 3 functional requirements per feature

Output your response as valid JSON with these exact keys:
- title (string)
- user_story (string)
- ui_ux_description (string)
- functional_requirements (array of strings)

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
  ]
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
    user_message = f"""Generate a structured GitHub issue for the following feature request.

Project Context: {project_name}

Feature Request:
{user_input}

Respond with a JSON object containing title, user_story, ui_ux_description, and functional_requirements."""

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
