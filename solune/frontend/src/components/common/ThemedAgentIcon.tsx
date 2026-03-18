import { useMemo, useState } from 'react';
import {
  CelestialGlyph,
  getIconToneStyles,
  resolveAgentIconName,
  type CelestialIconName,
} from '@/components/common/agentIcons';
import { cn } from '@/lib/utils';

const SIZE_STYLES = {
  sm: {
    wrapper: 'h-6 w-6 text-[10px]',
    icon: 'h-3.5 w-3.5',
  },
  md: {
    wrapper: 'h-8 w-8 text-xs',
    icon: 'h-[1.125rem] w-[1.125rem]',
  },
  lg: {
    wrapper: 'h-11 w-11 text-sm',
    icon: 'h-6 w-6',
  },
} as const;

interface ThemedAgentIconProps {
  slug?: string | null;
  name: string;
  avatarUrl?: string | null;
  iconName?: string | null;
  size?: keyof typeof SIZE_STYLES;
  className?: string;
  title?: string;
}

export {
  CELESTIAL_ICON_CATALOG,
  getThemedAgentIconName as getThemedAgentVariant,
  resolveAgentIconName,
} from '@/components/common/agentIcons';

function getInitial(name: string): string {
  const trimmed = name.trim();
  return trimmed ? trimmed.charAt(0).toUpperCase() : '?';
}

export function ThemedAgentIcon({
  slug,
  name,
  avatarUrl,
  iconName,
  size = 'md',
  className,
  title,
}: ThemedAgentIconProps) {
  const [imageErrored, setImageErrored] = useState(false);

  const [prevAvatarUrl, setPrevAvatarUrl] = useState(avatarUrl);
  if (avatarUrl !== prevAvatarUrl) {
    setPrevAvatarUrl(avatarUrl);
    setImageErrored(false);
  }

  const resolvedIconName = useMemo(() => resolveAgentIconName(iconName, slug), [iconName, slug]);
  const sizeStyle = SIZE_STYLES[size];
  const styles = resolvedIconName ? getIconToneStyles(resolvedIconName) : getIconToneStyles('nova');
  const initial = getInitial(name);

  return (
    <span
      className={cn(
        'relative inline-flex shrink-0 items-center justify-center overflow-hidden rounded-full border font-semibold tracking-[0.02em] select-none',
        sizeStyle.wrapper,
        className
      )}
      style={styles.wrapper}
      title={title ?? name}
      data-agent-icon={resolvedIconName ?? 'initial'}
      data-agent-variant={resolvedIconName ?? 'initial'}
    >
      {avatarUrl && !imageErrored ? (
        <img
          src={avatarUrl}
          alt={name}
          className="h-full w-full object-cover"
          onError={() => setImageErrored(true)}
        />
      ) : resolvedIconName ? (
        <CelestialGlyph
          iconName={resolvedIconName as CelestialIconName}
          className={sizeStyle.icon}
        />
      ) : (
        <span style={{ color: 'hsl(var(--foreground))' }}>{initial}</span>
      )}
    </span>
  );
}
