import {
  CELESTIAL_ICON_CATALOG,
  getThemedAgentIconName,
  type CelestialIconName,
} from '@/components/common/agentIcons';
import { ThemedAgentIcon } from '@/components/common/ThemedAgentIcon';
import { cn } from '@/lib/utils';

interface AgentIconCatalogProps {
  slug?: string | null;
  agentName: string;
  selectedIconName?: string | null;
  onSelect: (iconName: CelestialIconName | null) => void;
}

export function AgentIconCatalog({
  slug,
  agentName,
  selectedIconName,
  onSelect,
}: AgentIconCatalogProps) {
  const automaticIcon = getThemedAgentIconName(slug);

  return (
    <div className="flex flex-col gap-3">
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
        <button
          type="button"
          onClick={() => onSelect(null)}
          className={cn(
            'celestial-focus moonwell flex min-h-28 flex-col items-center justify-center gap-2 rounded-[1rem] border px-3 py-3 text-center transition-all hover:-translate-y-0.5 hover:border-primary/35',
            !selectedIconName ? 'border-primary/40 ring-1 ring-primary/20' : 'border-border/70'
          )}
        >
          <ThemedAgentIcon slug={slug} name={agentName} size="lg" />
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-foreground">
              Automatic
            </p>
            <p className="mt-1 text-[11px] leading-4 text-muted-foreground">
              {automaticIcon ? `Defaults to ${automaticIcon}` : 'Use slug-based fallback'}
            </p>
          </div>
        </button>

        {CELESTIAL_ICON_CATALOG.map((icon) => (
          <button
            key={icon.id}
            type="button"
            onClick={() => onSelect(icon.id)}
            className={cn(
              'celestial-focus moonwell flex min-h-28 flex-col items-center justify-center gap-2 rounded-[1rem] border px-3 py-3 text-center transition-all hover:-translate-y-0.5 hover:border-primary/35',
              selectedIconName === icon.id
                ? 'border-primary/40 ring-1 ring-primary/20'
                : 'border-border/70'
            )}
          >
            <ThemedAgentIcon iconName={icon.id} name={icon.label} size="lg" />
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-foreground">
                {icon.label}
              </p>
              <p className="mt-1 text-[11px] leading-4 text-muted-foreground">{icon.description}</p>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
