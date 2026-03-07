/**
 * Format an agent identifier for display.
 *
 * Priority: displayName (if provided and non-empty) > slug formatting.
 * Slug rules:
 *   1. Split on "."
 *   2. Filter empty segments
 *   3. Title-case each segment (first char upper, rest lower)
 *   4. Special compound: "speckit" → "Spec Kit"
 *   5. Join segments with " - "
 *
 * @param slug - Agent identifier (e.g., "speckit.tasks", "linter")
 * @param displayName - Optional explicit display name (takes precedence)
 * @returns Formatted display string
 */
export function formatAgentName(slug: string, displayName?: string | null): string {
  if (displayName != null && displayName.length > 0) {
    return displayName;
  }

  if (!slug) return '';

  const segments = slug.split('.').filter((s) => s.length > 0);
  if (segments.length === 0) return '';

  const formatted = segments.map((segment) => {
    const lower = segment.toLowerCase();
    if (lower === 'speckit') return 'Spec Kit';
    return lower.charAt(0).toUpperCase() + lower.slice(1);
  });

  return formatted.join(' - ');
}
