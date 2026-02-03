/**
 * Smiley Face Logo component for the application header
 */

import type { HTMLAttributes } from 'react';

interface SmileyLogoProps extends HTMLAttributes<HTMLDivElement> {
  size?: number;
}

export function SmileyLogo({ size = 32, ...props }: SmileyLogoProps) {
  return (
    <div className="smiley-logo" title="Welcome!" {...props}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 100 100"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-label="Smiley face logo"
      >
        {/* Circle face */}
        <circle
          cx="50"
          cy="50"
          r="45"
          fill="#FFD93D"
          stroke="#333333"
          strokeWidth="3"
        />
        {/* Left eye */}
        <circle cx="35" cy="40" r="5" fill="#333333" />
        {/* Right eye */}
        <circle cx="65" cy="40" r="5" fill="#333333" />
        {/* Smile */}
        <path
          d="M 30 60 Q 50 75 70 60"
          stroke="#333333"
          strokeWidth="3"
          strokeLinecap="round"
          fill="none"
        />
      </svg>
    </div>
  );
}
