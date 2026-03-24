/**
 * Onboarding tour SVG icons — monochrome line-art, 24×24, currentColor stroke.
 * Each icon matches the celestial/cosmic theme of Solune.
 */

interface IconProps {
  className?: string;
}

/** Welcome step — sun left, crescent moon right */
export function SunMoonIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" width={24} height={24} fill="none" stroke="currentColor" strokeWidth={1.5} className={className}>
      <circle cx={8} cy={12} r={4} />
      <line x1={8} y1={4} x2={8} y2={2} />
      <line x1={8} y1={22} x2={8} y2={20} />
      <line x1={2} y1={12} x2={0} y2={12} />
      <line x1={4} y1={7.5} x2={2.6} y2={6.1} />
      <line x1={4} y1={16.5} x2={2.6} y2={17.9} />
      <path d="M16 6a6 6 0 0 1 0 12 5 5 0 0 0 0-12z" />
    </svg>
  );
}

/** Sidebar navigation — compass rose */
export function CompassRoseIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" width={24} height={24} fill="none" stroke="currentColor" strokeWidth={1.5} className={className}>
      <circle cx={12} cy={12} r={9} />
      <polygon points="12,3.5 13.5,10.5 12,9 10.5,10.5" />
      <polygon points="12,20.5 13.5,13.5 12,15 10.5,13.5" />
      <polygon points="3.5,12 10.5,10.5 9,12 10.5,13.5" />
      <polygon points="20.5,12 13.5,10.5 15,12 13.5,13.5" />
    </svg>
  );
}

/** Project selector — star chart */
export function StarChartIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" width={24} height={24} fill="none" stroke="currentColor" strokeWidth={1.5} className={className}>
      <rect x={3} y={3} width={18} height={18} rx={2} />
      <circle cx={8} cy={8} r={1} />
      <circle cx={16} cy={7} r={1} />
      <circle cx={12} cy={13} r={1} />
      <circle cx={7} cy={17} r={1} />
      <circle cx={17} cy={16} r={1} />
      <line x1={8} y1={8} x2={12} y2={13} />
      <line x1={16} y1={7} x2={12} y2={13} />
      <line x1={12} y1={13} x2={7} y2={17} />
      <line x1={12} y1={13} x2={17} y2={16} />
    </svg>
  );
}

/** Chat toggle — chat bubble with stars */
export function ChatStarsIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" width={24} height={24} fill="none" stroke="currentColor" strokeWidth={1.5} className={className}>
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      <circle cx={9} cy={10} r={0.75} />
      <circle cx={15} cy={8} r={0.75} />
      <circle cx={12} cy={12} r={0.75} />
    </svg>
  );
}

/** Projects board — constellation grid */
export function ConstellationGridIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" width={24} height={24} fill="none" stroke="currentColor" strokeWidth={1.5} className={className}>
      <rect x={3} y={3} width={7} height={7} rx={1} />
      <rect x={14} y={3} width={7} height={7} rx={1} />
      <rect x={3} y={14} width={7} height={7} rx={1} />
      <rect x={14} y={14} width={7} height={7} rx={1} />
      <line x1={10} y1={6.5} x2={14} y2={6.5} />
      <line x1={6.5} y1={10} x2={6.5} y2={14} />
      <line x1={10} y1={17.5} x2={14} y2={17.5} />
    </svg>
  );
}

/** Agent pipelines — orbital rings */
export function OrbitalRingsIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" width={24} height={24} fill="none" stroke="currentColor" strokeWidth={1.5} className={className}>
      <circle cx={12} cy={12} r={3} />
      <ellipse cx={12} cy={12} rx={10} ry={4} />
      <ellipse cx={12} cy={12} rx={10} ry={4} transform="rotate(60 12 12)" />
      <ellipse cx={12} cy={12} rx={10} ry={4} transform="rotate(120 12 12)" />
    </svg>
  );
}

/** Agents — celestial hand (open palm with rays) */
export function CelestialHandIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" width={24} height={24} fill="none" stroke="currentColor" strokeWidth={1.5} className={className}>
      <path d="M8 13V6.5a1.5 1.5 0 0 1 3 0V11" />
      <path d="M11 10.5V5a1.5 1.5 0 0 1 3 0v6" />
      <path d="M14 11V6.5a1.5 1.5 0 0 1 3 0v5.5" />
      <path d="M8 13a4 4 0 0 0 0 4h6a4 4 0 0 0 4-4V12a1.5 1.5 0 0 0-3 0" />
      <line x1={12} y1={1} x2={12} y2={3} />
      <line x1={7} y1={2} x2={8} y2={4} />
      <line x1={17} y1={2} x2={16} y2={4} />
    </svg>
  );
}

/** Theme toggle — half sun, half moon */
export function SunMoonToggleIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" width={24} height={24} fill="none" stroke="currentColor" strokeWidth={1.5} className={className}>
      <circle cx={12} cy={12} r={5} />
      <path d="M12 7V2" />
      <path d="M12 22v-5" />
      <path d="M7 12H2" />
      <path d="M22 12h-5" />
      <path d="M12 7a5 5 0 0 1 0 10" strokeDasharray="3 2" />
    </svg>
  );
}

/** Activity page — timeline with markers at intervals */
export function TimelineStarsIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" width={24} height={24} fill="none" stroke="currentColor" strokeWidth={1.5} className={className}>
      <line x1={12} y1={2} x2={12} y2={22} />
      <circle cx={12} cy={5} r={1.25} />
      <circle cx={12} cy={12} r={1.25} />
      <circle cx={12} cy={19} r={1.25} />
      <line x1={12} y1={5} x2={17} y2={5} />
      <line x1={12} y1={12} x2={7} y2={12} />
      <line x1={12} y1={19} x2={17} y2={19} />
      <circle cx={4} cy={8} r={0.75} />
      <circle cx={20} cy={16} r={0.75} />
    </svg>
  );
}
/** Knowledge base — open book with stars */
export function BookStarsIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" width={24} height={24} fill="none" stroke="currentColor" strokeWidth={1.5} className={className}>
      <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
      <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
      <circle cx={6} cy={8} r={0.75} />
      <circle cx={18} cy={8} r={0.75} />
      <circle cx={12} cy={4} r={0.75} />
    </svg>
  );
}
