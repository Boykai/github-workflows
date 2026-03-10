import { cn } from '@/lib/utils';
/**
 * AgentAvatar — deterministic sun/moon themed SVG avatar for agents.
 *
 * Uses a djb2 hash of the agent slug to select from 12 celestial icon variants.
 * Sun variants (0–5) use warm colors; moon variants (6–11) use cool colors.
 */

const AVATAR_COUNT = 12;

const SIZE_MAP = { sm: 24, md: 32, lg: 48 } as const;

function djb2Hash(str: string): number {
  let hash = 5381;
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash + str.charCodeAt(i)) | 0;
  }
  return Math.abs(hash) % AVATAR_COUNT;
}

/** Each icon returns an SVG <g> element for the given size. */
const ICONS: ((s: number) => React.ReactNode)[] = [
  // 0: Full Sun
  (s) => (
    <g>
      <circle cx={s / 2} cy={s / 2} r={s * 0.25} fill="#fbbf24" />
      {[0, 45, 90, 135, 180, 225, 270, 315].map((deg) => (
        <line
          key={deg}
          x1={s / 2}
          y1={s * 0.12}
          x2={s / 2}
          y2={s * 0.04}
          stroke="#f59e0b"
          strokeWidth={s * 0.04}
          strokeLinecap="round"
          transform={`rotate(${deg} ${s / 2} ${s / 2})`}
        />
      ))}
    </g>
  ),
  // 1: Sunrise
  (s) => (
    <g>
      <path
        d={`M${s * 0.15},${s * 0.6} A${s * 0.35},${s * 0.35} 0 0,1 ${s * 0.85},${s * 0.6}`}
        fill="#fbbf24"
      />
      <line
        x1={s * 0.1}
        y1={s * 0.6}
        x2={s * 0.9}
        y2={s * 0.6}
        stroke="#f59e0b"
        strokeWidth={s * 0.03}
      />
      {[0, 30, 60, 90, 120, 150, 180].map((deg) => (
        <line
          key={deg}
          x1={s / 2}
          y1={s * 0.2}
          x2={s / 2}
          y2={s * 0.12}
          stroke="#fbbf24"
          strokeWidth={s * 0.03}
          strokeLinecap="round"
          transform={`rotate(${deg - 90} ${s / 2} ${s * 0.6})`}
        />
      ))}
    </g>
  ),
  // 2: Sun Face
  (s) => (
    <g>
      <circle cx={s / 2} cy={s / 2} r={s * 0.28} fill="#fcd34d" />
      <circle cx={s * 0.4} cy={s * 0.44} r={s * 0.03} fill="#92400e" />
      <circle cx={s * 0.6} cy={s * 0.44} r={s * 0.03} fill="#92400e" />
      <path
        d={`M${s * 0.4},${s * 0.56} Q${s / 2},${s * 0.64} ${s * 0.6},${s * 0.56}`}
        fill="none"
        stroke="#92400e"
        strokeWidth={s * 0.025}
        strokeLinecap="round"
      />
    </g>
  ),
  // 3: Sun Cloud
  (s) => (
    <g>
      <circle cx={s * 0.45} cy={s * 0.38} r={s * 0.2} fill="#fbbf24" />
      <ellipse cx={s * 0.5} cy={s * 0.65} rx={s * 0.3} ry={s * 0.12} fill="#cbd5e1" />
      <circle cx={s * 0.35} cy={s * 0.6} r={s * 0.1} fill="#cbd5e1" />
      <circle cx={s * 0.6} cy={s * 0.58} r={s * 0.08} fill="#cbd5e1" />
    </g>
  ),
  // 4: Solar Eclipse
  (s) => (
    <g>
      <circle cx={s / 2} cy={s / 2} r={s * 0.3} fill="#fbbf24" />
      <circle cx={s * 0.55} cy={s * 0.45} r={s * 0.26} fill="#1e293b" />
    </g>
  ),
  // 5: Sunburst
  (s) => (
    <g>
      <circle cx={s / 2} cy={s / 2} r={s * 0.18} fill="#fb923c" />
      {[0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330].map((deg) => (
        <line
          key={deg}
          x1={s / 2}
          y1={s * 0.24}
          x2={s / 2}
          y2={s * 0.08}
          stroke="#f97316"
          strokeWidth={s * 0.035}
          strokeLinecap="round"
          transform={`rotate(${deg} ${s / 2} ${s / 2})`}
        />
      ))}
    </g>
  ),
  // 6: Full Moon
  (s) => (
    <g>
      <circle cx={s / 2} cy={s / 2} r={s * 0.3} fill="#e2e8f0" />
      <circle cx={s * 0.4} cy={s * 0.38} r={s * 0.06} fill="#cbd5e1" opacity={0.7} />
      <circle cx={s * 0.58} cy={s * 0.55} r={s * 0.08} fill="#cbd5e1" opacity={0.6} />
      <circle cx={s * 0.35} cy={s * 0.6} r={s * 0.04} fill="#cbd5e1" opacity={0.5} />
    </g>
  ),
  // 7: Crescent Moon
  (s) => (
    <g>
      <circle cx={s / 2} cy={s / 2} r={s * 0.28} fill="#94a3b8" />
      <circle cx={s * 0.6} cy={s * 0.42} r={s * 0.24} fill="hsl(var(--background))" />
    </g>
  ),
  // 8: Half Moon
  (s) => (
    <g>
      <circle cx={s / 2} cy={s / 2} r={s * 0.28} fill="#94a3b8" />
      <path
        d={`M${s / 2},${s * 0.22} A${s * 0.28},${s * 0.28} 0 0,1 ${s / 2},${s * 0.78}`}
        fill="#e2e8f0"
      />
    </g>
  ),
  // 9: Waning Crescent
  (s) => (
    <g>
      <circle cx={s / 2} cy={s / 2} r={s * 0.28} fill="#818cf8" />
      <circle cx={s * 0.4} cy={s * 0.48} r={s * 0.22} fill="hsl(var(--background))" />
    </g>
  ),
  // 10: Moon + Stars
  (s) => (
    <g>
      <circle cx={s * 0.45} cy={s / 2} r={s * 0.22} fill="#93c5fd" />
      <circle cx={s * 0.56} cy={s * 0.42} r={s * 0.18} fill="hsl(var(--background))" />
      <circle cx={s * 0.78} cy={s * 0.25} r={s * 0.025} fill="#fcd34d" />
      <circle cx={s * 0.7} cy={s * 0.7} r={s * 0.02} fill="#fcd34d" />
      <circle cx={s * 0.85} cy={s * 0.5} r={s * 0.015} fill="#fcd34d" />
    </g>
  ),
  // 11: Moonrise
  (s) => (
    <g>
      <path
        d={`M${s * 0.15},${s * 0.6} A${s * 0.35},${s * 0.35} 0 0,1 ${s * 0.85},${s * 0.6}`}
        fill="#94a3b8"
      />
      <line
        x1={s * 0.1}
        y1={s * 0.6}
        x2={s * 0.9}
        y2={s * 0.6}
        stroke="#64748b"
        strokeWidth={s * 0.03}
      />
    </g>
  ),
];

interface AgentAvatarProps {
  slug: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function AgentAvatar({ slug, size = 'md', className }: AgentAvatarProps) {
  const idx = djb2Hash(slug);
  const px = SIZE_MAP[size];
  const icon = ICONS[idx];

  return (
    <span
      className={cn('inline-flex items-center justify-center rounded-full bg-muted/50 p-1 transition-shadow hover:shadow-[0_0_12px_hsl(var(--glow)/0.25)]', className ?? '')}
    >
      <svg
        width={px}
        height={px}
        viewBox={`0 0 ${px} ${px}`}
        role="img"
        aria-label={`Avatar for ${slug}`}
      >
        {icon(px)}
      </svg>
    </span>
  );
}
