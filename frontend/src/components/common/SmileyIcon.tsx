/**
 * Smiley face icon component with tooltip
 */

import { useState } from 'react';
import './SmileyIcon.css';

export function SmileyIcon() {
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <div 
      className="smiley-icon-container"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
      role="img"
      aria-label="Have a nice day!"
    >
      <svg
        className="smiley-icon"
        viewBox="0 0 32 32"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        width="32"
        height="32"
        aria-hidden="true"
      >
        {/* Circle face */}
        <circle cx="16" cy="16" r="14" fill="#FFC83D" stroke="#333" strokeWidth="2" />
        
        {/* Left eye */}
        <circle cx="11" cy="12" r="2" fill="#333" />
        
        {/* Right eye */}
        <circle cx="21" cy="12" r="2" fill="#333" />
        
        {/* Smile */}
        <path 
          d="M 10 18 Q 16 24 22 18" 
          stroke="#333" 
          strokeWidth="2" 
          fill="none"
          strokeLinecap="round"
        />
      </svg>
      
      {showTooltip && (
        <div className="smiley-tooltip" role="tooltip">
          Have a nice day!
        </div>
      )}
    </div>
  );
}
