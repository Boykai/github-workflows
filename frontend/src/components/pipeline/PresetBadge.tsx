/**
 * PresetBadge — visual indicator for system preset pipelines.
 * Shows a lock icon with the preset name in accent colors.
 */

import { Lock } from 'lucide-react';

interface PresetBadgeProps {
  presetId: string;
  className?: string;
}

const PRESET_STYLES: Record<string, { label: string; classes: string }> = {
  'spec-kit': {
    label: 'Spec Kit',
    classes: 'bg-violet-100/80 text-violet-700 dark:bg-violet-950/40 dark:text-violet-300',
  },
  'github-copilot': {
    label: 'GitHub Copilot',
    classes: 'bg-emerald-100/80 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300',
  },
};

export function PresetBadge({ presetId, className = '' }: PresetBadgeProps) {
  const style = PRESET_STYLES[presetId] ?? {
    label: presetId,
    classes: 'bg-muted text-muted-foreground',
  };

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium ${style.classes} ${className}`}
    >
      <Lock className="h-2.5 w-2.5" />
      {style.label}
    </span>
  );
}
