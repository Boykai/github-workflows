import type { CSSProperties } from 'react';

export type CelestialIconName =
  | 'sun-halo'
  | 'sunrise'
  | 'solar-crown'
  | 'crescent'
  | 'moon-phase'
  | 'eclipse'
  | 'north-star'
  | 'eight-point-star'
  | 'constellation'
  | 'twin-stars'
  | 'comet'
  | 'meteor'
  | 'orbit'
  | 'planet-ring'
  | 'nova'
  | 'aurora';

export interface CelestialIconOption {
  id: CelestialIconName;
  label: string;
  family: 'sun' | 'moon' | 'star' | 'orbit' | 'motion' | 'aurora';
  description: string;
}

export interface IconToneStyles {
  wrapper: CSSProperties;
  icon: CSSProperties;
  accent: CSSProperties;
  glow: CSSProperties;
}

export const CELESTIAL_ICON_CATALOG: CelestialIconOption[] = [
  { id: 'sun-halo', label: 'Sun Halo', family: 'sun', description: 'Radiant centered halo.' },
  { id: 'sunrise', label: 'Sunrise', family: 'sun', description: 'Rising sun over an arc.' },
  {
    id: 'solar-crown',
    label: 'Solar Crown',
    family: 'sun',
    description: 'Crowned sun with sharp rays.',
  },
  { id: 'crescent', label: 'Crescent', family: 'moon', description: 'Classic moon crescent.' },
  { id: 'moon-phase', label: 'Moon Phase', family: 'moon', description: 'Phase cycle with stars.' },
  { id: 'eclipse', label: 'Eclipse', family: 'moon', description: 'Shadowed sun ring.' },
  { id: 'north-star', label: 'North Star', family: 'star', description: 'Single guiding star.' },
  {
    id: 'eight-point-star',
    label: 'Eight-Point Star',
    family: 'star',
    description: 'Symmetric bright star.',
  },
  {
    id: 'constellation',
    label: 'Constellation',
    family: 'star',
    description: 'Connected star map.',
  },
  { id: 'twin-stars', label: 'Twin Stars', family: 'star', description: 'Paired stars in orbit.' },
  { id: 'comet', label: 'Comet', family: 'motion', description: 'Bright comet with long trail.' },
  { id: 'meteor', label: 'Meteor', family: 'motion', description: 'Fast meteor streak.' },
  { id: 'orbit', label: 'Orbit', family: 'orbit', description: 'Orbital rings and core.' },
  {
    id: 'planet-ring',
    label: 'Planet Ring',
    family: 'orbit',
    description: 'Saturn-like planet icon.',
  },
  { id: 'nova', label: 'Nova', family: 'star', description: 'Exploding starburst.' },
  { id: 'aurora', label: 'Aurora', family: 'aurora', description: 'Celestial wave and stars.' },
];

const ICON_SET = new Set<CelestialIconName>(CELESTIAL_ICON_CATALOG.map((icon) => icon.id));

const ICON_BY_SLUG: Record<string, CelestialIconName> = {
  human: 'sunrise',
  copilot: 'eclipse',
  'github-copilot': 'eclipse',
  'copilot-review': 'moon-phase',
  judge: 'planet-ring',
  linter: 'meteor',
  'speckit-specify': 'north-star',
  'speckit-clarify': 'twin-stars',
  'speckit-plan': 'crescent',
  'speckit-tasks': 'constellation',
  'speckit-implement': 'solar-crown',
  'speckit-analyze': 'orbit',
  'speckit-checklist': 'eight-point-star',
  'speckit-taskstoissues': 'comet',
  'mcp-appservice-builder': 'aurora',
  azqrcostoptimizeagent: 'nova',
  azurecostoptimizeagent: 'nova',
};

const HASH_ICONS = CELESTIAL_ICON_CATALOG.map((icon) => icon.id);

function normalizeSlug(slug?: string | null): string {
  return (slug ?? '')
    .trim()
    .toLowerCase()
    .replace(/[._\s]+/g, '-');
}

function hashString(value: string): number {
  let hash = 0;
  for (let index = 0; index < value.length; index += 1) {
    hash = (hash * 31 + value.charCodeAt(index)) >>> 0;
  }
  return hash;
}

export function isCelestialIconName(value?: string | null): value is CelestialIconName {
  return !!value && ICON_SET.has(value as CelestialIconName);
}

export function getThemedAgentIconName(slug?: string | null): CelestialIconName | null {
  const normalized = normalizeSlug(slug);
  if (!normalized) {
    return null;
  }

  if (ICON_BY_SLUG[normalized]) {
    return ICON_BY_SLUG[normalized];
  }

  if (normalized.startsWith('speckit-')) {
    if (normalized.includes('plan')) return 'crescent';
    if (normalized.includes('task')) return 'constellation';
    if (normalized.includes('implement')) return 'solar-crown';
    if (normalized.includes('analy')) return 'orbit';
    if (normalized.includes('clar')) return 'twin-stars';
    return 'north-star';
  }

  return HASH_ICONS[hashString(normalized) % HASH_ICONS.length];
}

export function resolveAgentIconName(
  iconName?: string | null,
  slug?: string | null
): CelestialIconName | null {
  if (isCelestialIconName(iconName)) {
    return iconName;
  }

  return getThemedAgentIconName(slug);
}

export function getIconToneStyles(iconName: CelestialIconName): IconToneStyles {
  const sunTone: IconToneStyles = {
    wrapper: {
      background:
        'radial-gradient(circle at 34% 30%, hsl(var(--glow) / 0.98) 0%, hsl(var(--gold) / 0.82) 24%, hsl(var(--background) / 0.94) 62%, hsl(var(--background) / 0.86) 100%)',
      borderColor: 'hsl(var(--gold) / 0.42)',
      boxShadow: '0 8px 22px hsl(var(--gold) / 0.14), inset 0 1px 0 hsl(var(--glow) / 0.4)',
    },
    icon: { color: 'hsl(var(--night))' },
    accent: { color: 'hsl(var(--gold))' },
    glow: { color: 'hsl(var(--glow))' },
  };

  const moonTone: IconToneStyles = {
    wrapper: {
      background:
        'radial-gradient(circle at 30% 24%, hsl(var(--glow) / 0.5) 0%, hsl(var(--panel) / 0.98) 34%, hsl(var(--background) / 0.9) 100%)',
      borderColor: 'hsl(var(--border) / 0.76)',
      boxShadow: '0 8px 18px hsl(var(--night) / 0.1), inset 0 1px 0 hsl(var(--glow) / 0.16)',
    },
    icon: { color: 'hsl(var(--foreground))' },
    accent: { color: 'hsl(var(--gold))' },
    glow: { color: 'hsl(var(--star-soft))' },
  };

  const nightTone: IconToneStyles = {
    wrapper: {
      background:
        'radial-gradient(circle at 28% 24%, hsl(var(--star-soft) / 0.22) 0%, hsl(var(--night) / 0.94) 42%, hsl(var(--night) / 0.98) 100%)',
      borderColor: 'hsl(var(--gold) / 0.2)',
      boxShadow: '0 10px 22px hsl(var(--night) / 0.24), inset 0 1px 0 hsl(var(--star-soft) / 0.18)',
    },
    icon: { color: 'hsl(var(--star))' },
    accent: { color: 'hsl(var(--star-soft))' },
    glow: { color: 'hsl(var(--glow))' },
  };

  const orbitTone: IconToneStyles = {
    wrapper: {
      background:
        'radial-gradient(circle at 34% 28%, hsl(var(--glow) / 0.34) 0%, hsl(var(--background) / 0.98) 38%, hsl(var(--panel) / 0.92) 100%)',
      borderColor: 'hsl(var(--gold) / 0.28)',
      boxShadow: '0 8px 18px hsl(var(--night) / 0.08), inset 0 1px 0 hsl(var(--glow) / 0.2)',
    },
    icon: { color: 'hsl(var(--foreground))' },
    accent: { color: 'hsl(var(--gold))' },
    glow: { color: 'hsl(var(--glow))' },
  };

  const motionTone: IconToneStyles = {
    wrapper: {
      background:
        'linear-gradient(145deg, hsl(var(--background) / 0.98) 0%, hsl(var(--panel) / 0.92) 44%, hsl(var(--glow) / 0.26) 100%)',
      borderColor: 'hsl(var(--gold) / 0.28)',
      boxShadow: '0 8px 20px hsl(var(--night) / 0.1), inset 0 1px 0 hsl(var(--glow) / 0.26)',
    },
    icon: { color: 'hsl(var(--foreground))' },
    accent: { color: 'hsl(var(--gold))' },
    glow: { color: 'hsl(var(--glow))' },
  };

  const auroraTone: IconToneStyles = {
    wrapper: {
      background:
        'radial-gradient(circle at 32% 22%, hsl(var(--glow) / 0.42) 0%, color-mix(in srgb, hsl(var(--background)) 88%, hsl(var(--accent)) 12%) 44%, hsl(var(--panel) / 0.94) 100%)',
      borderColor: 'hsl(var(--accent) / 0.22)',
      boxShadow: '0 8px 20px hsl(var(--night) / 0.1), inset 0 1px 0 hsl(var(--glow) / 0.24)',
    },
    icon: { color: 'hsl(var(--accent))' },
    accent: { color: 'hsl(var(--gold))' },
    glow: { color: 'hsl(var(--glow))' },
  };

  switch (iconName) {
    case 'sun-halo':
    case 'sunrise':
    case 'solar-crown':
      return sunTone;
    case 'crescent':
    case 'moon-phase':
    case 'eclipse':
      return moonTone;
    case 'north-star':
    case 'eight-point-star':
    case 'constellation':
    case 'twin-stars':
    case 'nova':
      return nightTone;
    case 'orbit':
    case 'planet-ring':
      return orbitTone;
    case 'comet':
    case 'meteor':
      return motionTone;
    case 'aurora':
      return auroraTone;
    default:
      return nightTone;
  }
}

export function CelestialGlyph({
  iconName,
  className,
}: {
  iconName: CelestialIconName;
  className: string;
}) {
  const styles = getIconToneStyles(iconName);

  switch (iconName) {
    case 'sun-halo':
      return (
        <svg viewBox="0 0 24 24" className={className} aria-hidden="true">
          <circle cx="12" cy="12" r="4.8" fill={styles.accent.color as string} opacity="0.95" />
          <circle cx="12" cy="12" r="3.1" fill={styles.glow.color as string} opacity="0.9" />
          <g stroke={styles.icon.color as string} strokeWidth="1.35" strokeLinecap="round">
            <path d="M12 2.8v3" />
            <path d="M12 18.2v3" />
            <path d="m5.5 5.5 2.2 2.2" />
            <path d="m16.3 16.3 2.2 2.2" />
            <path d="M2.8 12h3" />
            <path d="M18.2 12h3" />
            <path d="m5.5 18.5 2.2-2.2" />
            <path d="m16.3 7.7 2.2-2.2" />
          </g>
        </svg>
      );
    case 'sunrise':
      return (
        <svg viewBox="0 0 24 24" className={className} aria-hidden="true">
          <path
            d="M4.5 15.6h15"
            stroke={styles.icon.color as string}
            strokeWidth="1.25"
            strokeLinecap="round"
          />
          <path
            d="M7.2 15.4a4.8 4.8 0 0 1 9.6 0"
            fill={styles.accent.color as string}
            opacity="0.92"
          />
          <g stroke={styles.icon.color as string} strokeWidth="1.15" strokeLinecap="round">
            <path d="M12 4.2v2.4" />
            <path d="m8 6.5 1.6 1.5" />
            <path d="m16 6.5-1.6 1.5" />
          </g>
        </svg>
      );
    case 'solar-crown':
      return (
        <svg viewBox="0 0 24 24" className={className} aria-hidden="true">
          <circle cx="12" cy="12" r="3.7" fill={styles.glow.color as string} />
          <path
            d="M12 3.3 13.6 7l3.9-.9-2.1 3.3 3.3 2.1-3.9.8.8 3.9-3.2-2.2-3.2 2.2.8-3.9-3.9-.8 3.3-2.1-2.1-3.3 3.9.9L12 3.3Z"
            fill={styles.accent.color as string}
            opacity="0.9"
          />
        </svg>
      );
    case 'crescent':
      return (
        <svg viewBox="0 0 24 24" className={className} aria-hidden="true">
          <circle cx="11.4" cy="11.6" r="5.5" fill={styles.accent.color as string} opacity="0.92" />
          <circle cx="14.2" cy="10.2" r="5.2" fill="hsl(var(--background))" />
          <circle cx="6.4" cy="6.1" r="1.1" fill={styles.glow.color as string} />
          <circle cx="17.7" cy="16.9" r="0.95" fill={styles.glow.color as string} opacity="0.9" />
        </svg>
      );
    case 'moon-phase':
      return (
        <svg viewBox="0 0 24 24" className={className} aria-hidden="true">
          <circle cx="12" cy="12" r="5.7" fill={styles.accent.color as string} opacity="0.28" />
          <path
            d="M12 6.3a5.7 5.7 0 1 0 0 11.4c1.14-1.26 1.75-3.09 1.75-5.7S13.14 7.56 12 6.3Z"
            fill={styles.icon.color as string}
            opacity="0.88"
          />
          <circle cx="6.3" cy="7" r="1.05" fill={styles.glow.color as string} />
          <circle cx="17.9" cy="16.7" r="0.95" fill={styles.glow.color as string} />
        </svg>
      );
    case 'eclipse':
      return (
        <svg viewBox="0 0 24 24" className={className} aria-hidden="true">
          <circle cx="12" cy="12" r="6.8" fill={styles.accent.color as string} opacity="0.22" />
          <circle cx="12" cy="12" r="5.8" fill="hsl(var(--night))" />
          <path
            d="M16.4 6.8c1.15 1.18 1.86 2.8 1.86 4.58 0 3.62-2.91 6.56-6.5 6.62"
            stroke={styles.glow.color as string}
            strokeWidth="1.5"
            strokeLinecap="round"
          />
          <path
            d="M7.6 17.1c-1.2-1.18-1.96-2.82-1.96-4.64 0-3.66 2.97-6.63 6.63-6.63"
            stroke={styles.accent.color as string}
            strokeWidth="1.15"
            strokeLinecap="round"
            opacity="0.9"
          />
        </svg>
      );
    case 'north-star':
      return (
        <svg viewBox="0 0 24 24" className={className} aria-hidden="true">
          <path
            d="M12 3.5 13.1 10l6.4 2-6.4 2L12 20.5l-1.1-6.5L4.5 12l6.4-2L12 3.5Z"
            fill={styles.accent.color as string}
            opacity="0.9"
          />
          <circle cx="12" cy="12" r="1.2" fill={styles.glow.color as string} />
        </svg>
      );
    case 'eight-point-star':
      return (
        <svg viewBox="0 0 24 24" className={className} aria-hidden="true">
          <path
            d="M12 4.2 13.4 9.6 19 11l-5.6 1.4L12 17.8l-1.4-5.4L5 11l5.6-1.4L12 4.2Z"
            fill={styles.accent.color as string}
            opacity="0.92"
          />
          <path
            d="M12 1.9v4.1M12 18v4.1M1.9 12H6M18 12h4.1M4.4 4.4l2.9 2.9M16.7 16.7l2.9 2.9M4.4 19.6l2.9-2.9M16.7 7.3l2.9-2.9"
            stroke={styles.glow.color as string}
            strokeWidth="1.05"
            strokeLinecap="round"
          />
        </svg>
      );
    case 'constellation':
      return (
        <svg viewBox="0 0 24 24" className={className} aria-hidden="true">
          <g stroke={styles.accent.color as string} strokeWidth="1.1" strokeLinecap="round">
            <path d="M5.2 16.8 9 8.1" />
            <path d="M9 8.1 15.3 10.3" />
            <path d="M15.3 10.3 18.6 6.4" />
            <path d="M15.3 10.3 17.7 17.6" />
          </g>
          <circle cx="5.2" cy="16.8" r="1.55" fill={styles.glow.color as string} />
          <circle cx="9" cy="8.1" r="1.5" fill={styles.glow.color as string} />
          <circle cx="15.3" cy="10.3" r="1.75" fill={styles.accent.color as string} />
          <circle cx="18.6" cy="6.4" r="1.25" fill={styles.glow.color as string} />
          <circle cx="17.7" cy="17.6" r="1.35" fill={styles.glow.color as string} opacity="0.92" />
        </svg>
      );
    case 'twin-stars':
      return (
        <svg viewBox="0 0 24 24" className={className} aria-hidden="true">
          <path
            d="M8 7.2 8.9 10l2.8.9-2.8.9L8 14.6l-.9-2.8-2.8-.9 2.8-.9L8 7.2Z"
            fill={styles.accent.color as string}
          />
          <path
            d="M16.5 10.2 17.2 12.6l2.4.8-2.4.8-.7 2.4-.8-2.4-2.4-.8 2.4-.8.8-2.4Z"
            fill={styles.glow.color as string}
          />
          <path
            d="M8.8 11.1c1.64 0 3.05.39 4.24 1.2"
            stroke={styles.icon.color as string}
            strokeWidth="1.1"
            strokeLinecap="round"
            opacity="0.78"
          />
        </svg>
      );
    case 'comet':
      return (
        <svg viewBox="0 0 24 24" className={className} aria-hidden="true">
          <path
            d="M5.2 15.8c3.1-3.35 6.18-5.2 11.95-7.26"
            stroke={styles.glow.color as string}
            strokeWidth="1.35"
            strokeLinecap="round"
            opacity="0.9"
          />
          <path
            d="M4.6 12.7c2.65-2.06 5.3-3.36 9.45-4.54"
            stroke={styles.accent.color as string}
            strokeWidth="1.1"
            strokeLinecap="round"
            opacity="0.9"
          />
          <circle cx="17.5" cy="7.7" r="2.55" fill={styles.accent.color as string} />
          <circle cx="17.5" cy="7.7" r="1.2" fill={styles.icon.color as string} opacity="0.72" />
        </svg>
      );
    case 'meteor':
      return (
        <svg viewBox="0 0 24 24" className={className} aria-hidden="true">
          <path
            d="M4.3 14.8c2.3-1.2 5.3-2.1 9.7-2.7"
            stroke={styles.glow.color as string}
            strokeWidth="1.15"
            strokeLinecap="round"
          />
          <path
            d="M5.1 11.4c3.1-.9 6.1-1.3 10.3-1.35"
            stroke={styles.accent.color as string}
            strokeWidth="1.25"
            strokeLinecap="round"
          />
          <path
            d="m16.8 8.3 2.8 1.4-1.3 2.85-2.85 1.35-1.4-2.8 1.45-2.8Z"
            fill={styles.accent.color as string}
            opacity="0.9"
          />
        </svg>
      );
    case 'orbit':
      return (
        <svg viewBox="0 0 24 24" className={className} aria-hidden="true">
          <ellipse
            cx="12"
            cy="12"
            rx="7.5"
            ry="4.15"
            fill="none"
            stroke={styles.accent.color as string}
            strokeWidth="1.15"
            transform="rotate(-20 12 12)"
          />
          <ellipse
            cx="12"
            cy="12"
            rx="7.5"
            ry="4.15"
            fill="none"
            stroke={styles.glow.color as string}
            strokeWidth="0.95"
            transform="rotate(20 12 12)"
            opacity="0.86"
          />
          <circle cx="12" cy="12" r="2.3" fill={styles.icon.color as string} opacity="0.9" />
          <circle cx="17.6" cy="8.8" r="1.25" fill={styles.accent.color as string} />
        </svg>
      );
    case 'planet-ring':
      return (
        <svg viewBox="0 0 24 24" className={className} aria-hidden="true">
          <ellipse
            cx="12"
            cy="12.7"
            rx="8.1"
            ry="2.9"
            fill="none"
            stroke={styles.accent.color as string}
            strokeWidth="1.15"
            transform="rotate(-10 12 12.7)"
          />
          <circle cx="12" cy="12" r="3.95" fill={styles.glow.color as string} />
          <path
            d="M8.2 14.2a4.2 4.2 0 0 0 7.6-2.2"
            stroke={styles.icon.color as string}
            strokeWidth="1.05"
            strokeLinecap="round"
            opacity="0.78"
          />
        </svg>
      );
    case 'nova':
      return (
        <svg viewBox="0 0 24 24" className={className} aria-hidden="true">
          <path
            d="M12 3.2 13.6 9l5.6-1.6-3.4 4.5 4.5 2.1-5.8 1.05.78 5.75L12 16.7l-3.28 4.1.78-5.75L3.7 14l4.5-2.1L4.8 7.4 10.4 9 12 3.2Z"
            fill={styles.accent.color as string}
            opacity="0.88"
          />
          <path
            d="M12 6.7 12.85 10l3.3-.92-2 2.62 2.66 1.22-3.4.58.46 3.4L12 14.46l-1.87 2.44.44-3.4-3.38-.58 2.64-1.22-2-2.62 3.3.92.87-3.3Z"
            fill={styles.glow.color as string}
          />
        </svg>
      );
    case 'aurora':
      return (
        <svg viewBox="0 0 24 24" className={className} aria-hidden="true">
          <path
            d="M4.4 15.4c2.2-3.3 4.55-5.06 7.2-5.06 2.45 0 3.6 1.54 5.2 1.54 1.15 0 2.12-.56 2.88-1.74"
            stroke={styles.icon.color as string}
            strokeWidth="1.2"
            strokeLinecap="round"
            fill="none"
          />
          <path
            d="M4.6 18.1c1.7-1.8 3.84-2.8 6.2-2.8 2.48 0 3.86 1.25 5.4 1.25 1.28 0 2.22-.44 3.18-1.38"
            stroke={styles.accent.color as string}
            strokeWidth="1.15"
            strokeLinecap="round"
            fill="none"
          />
          <circle cx="8.2" cy="7.2" r="1.05" fill={styles.glow.color as string} />
          <circle cx="17.6" cy="6.1" r="0.92" fill={styles.glow.color as string} />
        </svg>
      );
    default:
      return null;
  }
}
