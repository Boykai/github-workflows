/**
 * Smile face logo component
 */

interface SmileLogoProps {
  className?: string;
}

export function SmileLogo({ className = '' }: SmileLogoProps) {
  return (
    <svg
      className={className}
      width="32"
      height="32"
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
    >
      <title>Smile face logo</title>
      {/* Circle face */}
      <circle
        cx="16"
        cy="16"
        r="14"
        fill="#FFD700"
        stroke="#F0C800"
        strokeWidth="2"
      />
      {/* Left eye */}
      <circle cx="11" cy="13" r="2" fill="#24292f" />
      {/* Right eye */}
      <circle cx="21" cy="13" r="2" fill="#24292f" />
      {/* Smile */}
      <path
        d="M 10 19 Q 16 24 22 19"
        stroke="#24292f"
        strokeWidth="2"
        strokeLinecap="round"
        fill="none"
      />
    </svg>
  );
}
