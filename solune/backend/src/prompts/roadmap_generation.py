"""Prompt templates for AI-driven roadmap batch generation (FR-004)."""

ROADMAP_GENERATION_SYSTEM_PROMPT = """You are a product engineering lead analyzing a codebase to propose the next batch of high-impact features.

Your task: generate a batch of feature proposals that align with the product owner's seed vision, are informed by the current codebase state, and avoid duplicating previously generated features.

For each feature proposal, produce a JSON object with these fields:
- "title": A clear, concise title (max 256 characters) summarizing the feature
- "body": A full GitHub issue body in markdown, including a user story, functional requirements, and technical notes
- "rationale": A 1–3 sentence explanation of why this feature was proposed given the seed vision and codebase context
- "priority": One of "P0", "P1", "P2", "P3" — higher priority for features that unblock other work or address critical gaps
- "size": One of "XS", "S", "M", "L", "XL" — t-shirt size estimate of implementation effort

Rules:
1. Generate EXACTLY the requested number of feature proposals.
2. Each title MUST be unique within this batch AND must NOT duplicate any title in the "already generated" list.
3. Features must be concrete, actionable, and independently implementable.
4. Prioritize features that align most closely with the seed vision.
5. Consider the codebase context to propose features that fit naturally into the existing architecture.
6. Output raw JSON ONLY — a JSON array of objects. No markdown code fences, no extra text."""


def create_roadmap_generation_prompt(
    seed: str,
    batch_size: int,
    codebase_context: str,
    recent_titles: list[str],
) -> list[dict[str, str]]:
    """Build system + user messages for roadmap generation.

    Args:
        seed: Product vision text from the project owner.
        batch_size: Number of feature proposals to generate.
        codebase_context: Summary of codebase signals (modules, deps, coverage).
        recent_titles: Previously generated titles to avoid duplicates.

    Returns:
        List of message dicts suitable for CompletionProvider.complete().
    """
    dedup_section = ""
    if recent_titles:
        titles_list = "\n".join(f"- {t}" for t in recent_titles)
        dedup_section = (
            f"\n\n## Already Generated (DO NOT duplicate these titles)\n{titles_list}"
        )

    user_message = (
        f"## Seed Vision\n{seed}\n\n"
        f"## Codebase Context\n{codebase_context}\n\n"
        f"## Request\nGenerate exactly {batch_size} feature proposals."
        f"{dedup_section}"
    )

    return [
        {"role": "system", "content": ROADMAP_GENERATION_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
