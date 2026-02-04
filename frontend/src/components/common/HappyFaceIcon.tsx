/**
 * HappyFaceIcon component - displays a friendly happy face icon
 * with hover animation and tooltip.
 */

import { useState } from 'react';
import './HappyFaceIcon.css';

export function HappyFaceIcon() {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div
      className="happy-face-container"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      role="img"
      aria-label="Happy face - Have a great day!"
    >
      <svg
        className={`happy-face-icon ${isHovered ? 'hovered' : ''}`}
        width="32"
        height="32"
        viewBox="0 0 32 32"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Face circle */}
        <circle
          cx="16"
          cy="16"
          r="14"
          fill="#FFD93D"
          stroke="#FFA500"
          strokeWidth="2"
        />
        {/* Left eye */}
        <circle cx="11" cy="12" r="2" fill="#2D2D2D" />
        {/* Right eye */}
        <circle cx="21" cy="12" r="2" fill="#2D2D2D" />
        {/* Smile */}
        <path
          d="M 10 18 Q 16 24 22 18"
          stroke="#2D2D2D"
          strokeWidth="2"
          strokeLinecap="round"
          fill="none"
        />
      </svg>
      <span className="happy-face-tooltip">Have a great day! 😊</span>
    </div>
  );
}
