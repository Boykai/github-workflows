/**
 * Format an agent identifier for display.
 *
 * Priority: displayName (if provided and non-empty) > slug formatting,
 * unless a specific formatting option overrides that behavior.
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
export interface FormatAgentNameOptions {
  specKitStyle?: 'default' | 'suffix';
}

const SPEC_KIT_LABELS: Record<string, string> = {
  analyze: 'Analyze',
  checklist: 'Checklist',
  clarify: 'Clarify',
  constitution: 'Constitution',
  implement: 'Implement',
  plan: 'Plan',
  specify: 'Specify',
  tasks: 'Tasks',
  taskstoissues: 'Tasks To Issues',
};

function titleCaseSegment(segment: string): string {
  const lower = segment.toLowerCase();
  if (!lower) return '';
  if (/^v\d+$/i.test(segment)) return segment.toUpperCase();
  return lower.charAt(0).toUpperCase() + lower.slice(1);
}

function formatSpecKitSuffixName(slug: string): string {
  const remainder = slug.replace(/^speckit[.-]*/i, '');
  const segments = remainder.split(/[.-]/).filter((segment) => segment.length > 0);
  if (segments.length === 0) return 'Spec Kit';

  const normalizedKey = segments.join('').toLowerCase();
  const knownLabel = SPEC_KIT_LABELS[normalizedKey];
  const label = knownLabel ?? segments.map(titleCaseSegment).join(' ');
  return `${label} (Spec Kit)`;
}

export function formatAgentName(
  slug: string,
  displayName?: string | null,
  options?: FormatAgentNameOptions,
): string {
  const isSpecKitSlug = /^speckit(?:[.-]|$)/i.test(slug);

  if (options?.specKitStyle === 'suffix' && isSpecKitSlug) {
    return formatSpecKitSuffixName(slug);
  }

  if (displayName != null && displayName.length > 0) {
    return displayName;
  }

  if (!slug) return '';

  const segments = slug.split('.').filter((s) => s.length > 0);
  if (segments.length === 0) return '';

  const formatted = segments.map((segment) => {
    const lower = segment.toLowerCase();
    if (lower === 'speckit') return 'Spec Kit';
    return titleCaseSegment(segment);
  });

  return formatted.join(' - ');
}
