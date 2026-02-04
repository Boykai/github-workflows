/**
 * Logo component displaying a smiley face.
 */

import './Logo.css';

export function Logo() {
  return (
    <div className="logo-container">
      <svg
        className="logo"
        width="48"
        height="48"
        viewBox="0 0 100 100"
        xmlns="http://www.w3.org/2000/svg"
        role="img"
        aria-label="Friendly smiley face logo"
      >
        {/* Face circle */}
        <circle cx="50" cy="50" r="45" fill="#FFD700" stroke="#FFA500" strokeWidth="3" />
        
        {/* Left eye */}
        <circle cx="35" cy="40" r="5" fill="#333" />
        
        {/* Right eye */}
        <circle cx="65" cy="40" r="5" fill="#333" />
        
        {/* Smile */}
        <path
          d="M 30 60 Q 50 75 70 60"
          stroke="#333"
          strokeWidth="3"
          strokeLinecap="round"
          fill="none"
        />
      </svg>
    </div>
  );
}
