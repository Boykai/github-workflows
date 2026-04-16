"""AI prompt templates for task generation."""

TASK_GENERATION_SYSTEM_PROMPT = """You are an AI assistant that helps developers create well-structured tasks for GitHub Projects.

When a user describes a task they want to create, you must:
1. Generate a concise, action-oriented title (max 100 characters)
2. Generate a detailed description with context and acceptance criteria

Your output must be valid JSON in exactly this format:
{
  "title": "Short, action-oriented task title",
  "description": "## Overview\\nBrief description of what needs to be done.\\n\\n## Technical Details\\n- Key implementation points\\n- Dependencies or considerations\\n\\n## Acceptance Criteria\\n- [ ] First acceptance criterion\\n- [ ] Second acceptance criterion"
}

Guidelines for titles:
- Start with a verb (Add, Fix, Update, Implement, Create, etc.)
- Be specific but concise
- Avoid generic words like "thing", "stuff", "work on"
- Include the key subject/feature

Guidelines for descriptions:
- Use markdown formatting
- Include Overview, Technical Details, and Acceptance Criteria sections
- Be specific about what needs to be done
- Include 2-5 acceptance criteria as checkboxes
- Keep it focused on the task at hand

Important:
- Output ONLY valid JSON, no additional text
- Do not include code blocks or markdown formatting around the JSON
- Ensure all strings are properly escaped for JSON"""

TASK_GENERATION_USER_PROMPT_TEMPLATE = """Create a task based on this description:

"{user_input}"

Project context: {project_name}

Generate a well-structured task with a clear title and detailed description."""


STATUS_CHANGE_SYSTEM_PROMPT = """You are an AI assistant that helps developers update task statuses in GitHub Projects.

When a user asks to change a task's status, extract:
1. The task being referenced (by title, number, or description)
2. The target status (e.g., "In Progress", "Done", "Todo")

Your output must be valid JSON in exactly this format:
{
  "intent": "status_change",
  "task_reference": "The task title or description the user mentioned",
  "target_status": "The status they want to change to",
  "confidence": 0.0 to 1.0
}

If you cannot determine the task or status with confidence, set confidence below 0.5.

Examples:
- "Move fix login to in progress" -> {"intent": "status_change", "task_reference": "fix login", "target_status": "In Progress", "confidence": 0.9}
- "Mark the auth task as done" -> {"intent": "status_change", "task_reference": "auth task", "target_status": "Done", "confidence": 0.85}

Important:
- Output ONLY valid JSON, no additional text
- Do not include code blocks or markdown formatting around the JSON"""


def create_task_generation_prompt(user_input: str, project_name: str) -> list[dict]:
    """Create messages for task generation API call."""
    return [
        {"role": "system", "content": TASK_GENERATION_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": TASK_GENERATION_USER_PROMPT_TEMPLATE.format(
                user_input=user_input, project_name=project_name
            ),
        },
    ]


def create_status_change_prompt(
    user_input: str, available_tasks: list[str], available_statuses: list[str]
) -> list[dict]:
    """Create messages for status change intent detection."""
    context = f"""Available tasks in the project:
{chr(10).join(f'- {task}' for task in available_tasks[:20])}

Available statuses:
{', '.join(available_statuses)}"""

    return [
        {"role": "system", "content": STATUS_CHANGE_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"{context}\n\nUser request: {user_input}",
        },
    ]
