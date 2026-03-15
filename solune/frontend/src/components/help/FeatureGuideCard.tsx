/**
 * FeatureGuideCard — clickable card linking to a feature page.
 * Uses moonwell background class, hover lift, and primary icon color.
 */

import { Link } from 'react-router-dom';
import { cn } from '@/lib/utils';

interface FeatureGuideCardProps {
  title: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  href: string;
}

export function FeatureGuideCard({ title, description, icon: Icon, href }: FeatureGuideCardProps) {
  return (
    <Link
      to={href}
      className={cn(
        'moonwell group flex flex-col gap-3 rounded-[1.25rem] border border-border/50 p-5',
        'transition-all duration-200 hover:-translate-y-0.5 hover:border-primary/20 hover:shadow-md',
      )}
    >
      <div className="flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded-full bg-primary/15 text-primary">
        <Icon className="h-5 w-5 shrink-0" />
      </div>
      <div>
        <h4 className="text-sm font-semibold text-foreground">{title}</h4>
        <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{description}</p>
      </div>
    </Link>
  );
}
