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

/**
 * Detect raw slug-style identifiers (all lowercase, no spaces, only letters,
 * digits, hyphens, underscores, and dots).
 * These are display names that were never explicitly set and fall back to the raw slug.
 */
const RAW_SLUG_RE = /^[a-z][a-z0-9._-]*$/;

/**
 * Format a slug-like string, handling both dots (segment separator) and
 * hyphens/underscores (word separators within a segment).
 * e.g. "quality-assurance" → "Quality Assurance"
 *      "quality_assurance" → "Quality Assurance"
 *      "speckit.tasks"     → "Spec Kit - Tasks"
 */
function formatSlugString(slug: string): string {
  const dotSegments = slug.split('.').filter((s) => s.length > 0);
  if (dotSegments.length === 0) return '';

  const formatted = dotSegments.map((segment) => {
    const lower = segment.toLowerCase();
    if (lower === 'speckit') return 'Spec Kit';
    if (/^v\d+$/i.test(segment)) return segment.toUpperCase();
    // Handle hyphen/underscore-separated words within a segment
    const parts = lower.split(/[-_]/).filter((p) => p.length > 0);
    return parts.map((p) => p.charAt(0).toUpperCase() + p.slice(1)).join(' ');
  });

  return formatted.join(' - ');
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
  options?: FormatAgentNameOptions
): string {
  const isSpecKitSlug = /^speckit(?:[.-]|$)/i.test(slug);

  if (options?.specKitStyle === 'suffix' && isSpecKitSlug) {
    return formatSpecKitSuffixName(slug);
  }

  if (displayName != null && displayName.length > 0) {
    // If displayName looks like a raw slug (all lowercase, no spaces), treat
    // it as a slug for proper title-casing rather than returning it verbatim.
    if (RAW_SLUG_RE.test(displayName)) {
      return formatSlugString(displayName);
    }
    return displayName;
  }

  if (!slug) return '';

  return formatSlugString(slug);
}
