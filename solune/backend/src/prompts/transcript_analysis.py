"""Prompt templates for AI-assisted transcript analysis.

Follows the same pattern as ``issue_generation.py`` — a system prompt constant
plus a factory function that returns a ``list[dict]`` of chat messages.
"""

from datetime import timedelta

from src.utils import utcnow

TRANSCRIPT_ANALYSIS_SYSTEM_PROMPT = """You are an expert product manager who specializes in extracting actionable requirements from meeting transcripts.

Given a multi-speaker meeting transcript, your task is to:

1. **Identify speakers** and their roles/perspectives (developer, designer, PM, stakeholder, etc.)
2. **Extract application features** discussed during the meeting
3. **Synthesize user stories** in the format "As a [user type], I want [goal] so that [benefit]"
4. **Derive functional requirements** from discussed needs using "System MUST" or "System SHOULD" format
5. **Capture UI/UX preferences** mentioned by speakers
6. **Note technical constraints** or decisions made during the discussion
7. **Assign priority** based on discussion emphasis and frequency of mention

IMPORTANT GUIDELINES:
- Capture EVERY feature, requirement, and constraint discussed — do not drop any detail
- If multiple speakers discuss the same feature, synthesize their perspectives into a unified requirement
- Distinguish between confirmed decisions and suggestions/ideas
- Prioritize items that received the most discussion time or explicit priority markers
- Include at least 5 functional requirements
- If the transcript is unclear about a feature, note the ambiguity in technical_notes

Output your response as valid JSON with these exact keys:
- title (string, max 256 chars — summarize the primary feature or project discussed)
- user_story (string — synthesize the main user need from the discussion)
- ui_ux_description (string — compile all UI/UX preferences and design decisions mentioned)
- functional_requirements (array of 5-8 strings using "System MUST/SHOULD" format)
- technical_notes (string — technical constraints, decisions, and implementation guidance from the discussion)
- metadata (object with priority, size, estimate_hours, labels)

For metadata:
- priority: P0 (Critical), P1 (High), P2 (Medium), or P3 (Low) — based on discussion urgency
- size: T-shirt sizing - XS (<1hr), S (1-4hrs), M (4-8hrs/1day), L (1-3days), XL (3-5days)
- estimate_hours: Numeric estimate in hours (0.5 to 40)
- labels: Array — ALWAYS include "ai-generated", plus relevant type/scope labels from: "feature", "enhancement", "frontend", "backend", "ux", "api", "security", "performance"

IMPORTANT: Output raw JSON ONLY. Do NOT wrap in markdown code fences. Keep each field value concise.
"""


def create_transcript_analysis_prompt(
    transcript_content: str,
    project_name: str,
    metadata_context: dict | None = None,
) -> list[dict]:
    """Create prompt messages for transcript analysis.

    Args:
        transcript_content: Raw transcript text to analyse.
        project_name: Name of the target GitHub project for context.
        metadata_context: Optional dict with repo metadata (labels, branches,
            milestones, collaborators) to inject into the prompt.

    Returns:
        List of message dicts with ``role`` and ``content`` keys.
    """
    today = utcnow()
    start_date = today.strftime("%Y-%m-%d")
    default_target = (today + timedelta(days=1)).strftime("%Y-%m-%d")

    metadata_section = ""
    if metadata_context:
        parts: list[str] = []

        repo_labels = metadata_context.get("labels", [])
        if repo_labels:
            label_names = [lb["name"] if isinstance(lb, dict) else lb for lb in repo_labels]
            parts.append(
                "AVAILABLE LABELS (from repository — select from this list ONLY):\n"
                + ", ".join(f'"{n}"' for n in label_names)
            )

        repo_branches = metadata_context.get("branches", [])
        if repo_branches:
            branch_names = [br["name"] if isinstance(br, dict) else br for br in repo_branches]
            parts.append("AVAILABLE BRANCHES:\n" + ", ".join(f'"{n}"' for n in branch_names))

        if parts:
            metadata_section = "\n".join(parts) + "\n"

    user_message = f"""Analyze the following meeting transcript and extract structured requirements for a GitHub issue.

Project Context: {project_name}
Today's Date: {start_date}
Suggested Start Date: {start_date}
Suggested Target Date: {default_target}
{metadata_section}
Meeting Transcript:
---
{transcript_content}
---

Extract ALL discussed features, requirements, and decisions into a structured GitHub issue. Respond with raw JSON only."""

    return [
        {"role": "system", "content": TRANSCRIPT_ANALYSIS_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
