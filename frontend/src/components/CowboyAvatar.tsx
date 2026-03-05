import React from 'react';

// Using imports to ensure Vite bundles them if needed, or point to public/assets. 
// Since we placed them in src/assets/avatars, let's use standard imports.
import sheriffLogo from '@/assets/avatars/sheriff.svg';
import banditLogo from '@/assets/avatars/bandit.svg';
import genericLogo from '@/assets/avatars/generic.svg';

interface CowboyAvatarProps {
  slug: string;
  className?: string;
  srcOverride?: string | null;
}

export function CowboyAvatar({ slug, className = '', srcOverride }: CowboyAvatarProps) {
  let logoSrc = genericLogo;
  
  if (srcOverride) {
    logoSrc = srcOverride;
  } else if (slug.includes('review') || slug.includes('sheriff')) {
    logoSrc = sheriffLogo;
  } else if (slug.includes('script') || slug.includes('coder') || slug.includes('bandit')) {
    logoSrc = banditLogo;
  }
  
  return (
    <img 
      src={logoSrc} 
      alt={`${slug} avatar`} 
      className={`w-full h-full object-cover transition-transform hover:rotate-12 ${className}`} 
    />
  );
}
