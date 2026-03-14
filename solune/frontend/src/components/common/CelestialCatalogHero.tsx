import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface CatalogHeroStat {
  label: string;
  value: string;
}

interface CelestialCatalogHeroProps {
  eyebrow: string;
  title: string;
  description: string;
  badge?: string;
  note?: string;
  stats?: CatalogHeroStat[];
  actions?: ReactNode;
  className?: string;
}

export function CelestialCatalogHero({
  eyebrow,
  title,
  description,
  badge,
  note,
  stats = [],
  actions,
  className,
}: CelestialCatalogHeroProps) {
  return (
    <section
      className={cn(
        'section-aurora golden-ring starfield relative overflow-hidden rounded-[1.9rem] border border-border/70 px-5 py-6 shadow-lg sm:rounded-[2.2rem] sm:px-8 sm:py-9 lg:px-10 lg:py-10',
        className
      )}
    >
      {/* Decorative celestial background elements with animations */}
      <div className="catalog-hero-decor pointer-events-none absolute inset-0 opacity-90 dark:opacity-50">
        <div className="catalog-hero-ambient-glow absolute left-8 top-8 h-24 w-24 rounded-full bg-primary/10 blur-3xl celestial-pulse-glow dark:bg-primary/5" />
        <div className="catalog-hero-orbit catalog-hero-orbit-outer celestial-orbit celestial-orbit-spin left-[54%] top-1/2 h-[24rem] w-[24rem] -translate-x-1/2 -translate-y-1/2 border-primary/20 dark:border-primary/10" />
        <div className="catalog-hero-orbit catalog-hero-orbit-mid celestial-orbit celestial-orbit-spin-reverse left-[54%] top-1/2 h-[17rem] w-[17rem] -translate-x-1/2 -translate-y-1/2 border-border/35 dark:border-border/20" />
        <div className="catalog-hero-orbit catalog-hero-orbit-inner celestial-orbit celestial-orbit-spin left-[54%] top-1/2 h-[8rem] w-[8rem] -translate-x-1/2 -translate-y-1/2 border-primary/25 dark:border-primary/12" />
        <div className="catalog-hero-moon absolute right-10 top-12 h-16 w-16 rounded-full lunar-disc celestial-float opacity-95" />
        <div className="catalog-hero-star catalog-hero-star-top absolute left-[58%] top-[18%] h-3 w-3 rounded-full bg-primary/70 shadow-[0_0_20px_hsl(var(--gold)/0.35)] celestial-twinkle dark:bg-primary/50 dark:shadow-[0_0_12px_hsl(var(--gold)/0.2)]" />
        <div className="catalog-hero-star catalog-hero-star-bottom absolute bottom-10 left-[52%] h-5 w-5 rounded-full bg-primary/80 shadow-[0_0_30px_hsl(var(--gold)/0.35)] celestial-twinkle-delayed dark:bg-primary/50 dark:shadow-[0_0_16px_hsl(var(--gold)/0.2)]" />
        <div className="catalog-hero-beam absolute inset-x-10 top-0 h-px bg-gradient-to-r from-transparent via-primary/40 to-transparent dark:via-primary/20" />
      </div>

      <div className="relative z-10 grid gap-8 lg:grid-cols-[minmax(0,1.08fr)_22rem] lg:items-center lg:gap-10">
        <div className="max-w-3xl">
          <div className="flex flex-wrap items-center gap-3">
            <span className="celestial-sigil h-6 w-6 text-primary/90">
              <span className="h-1.5 w-1.5 rounded-full bg-primary" />
            </span>
            <p className="text-xs uppercase tracking-[0.32em] text-primary/85">{eyebrow}</p>
            {badge && (
              <span className="rounded-full border border-primary/25 bg-primary/10 px-3 py-1 text-[11px] uppercase tracking-[0.2em] text-primary">
                {badge}
              </span>
            )}
          </div>

          <h2 className="mt-5 max-w-3xl text-[2.7rem] font-display font-medium leading-[0.92] tracking-[0.02em] text-foreground sm:text-5xl xl:text-[4.6rem]">
            {title}
          </h2>
          <p className="mt-4 max-w-2xl text-sm leading-7 text-muted-foreground sm:mt-5 sm:text-base">
            {description}
          </p>

          {(actions || stats.length > 0) && (
            <div className="mt-8 flex flex-col gap-6">
              {actions && (
                <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
                  {actions}
                </div>
              )}
              {stats.length > 0 && (
                <div className="flex flex-wrap items-start gap-3">
                  {stats.map((stat) => (
                    <div
                      key={stat.label}
                      className="moonwell inline-flex max-w-full min-w-0 flex-col rounded-[1.2rem] px-4 py-3 sm:rounded-[1.3rem]"
                    >
                      <p className="text-[10px] uppercase tracking-[0.22em] text-muted-foreground/80">
                        {stat.label}
                      </p>
                      <p className="mt-2 break-words text-xl font-semibold leading-tight text-foreground">
                        {stat.value}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        <div className="catalog-hero-aside-wrap relative hidden min-h-[20rem] lg:block">
          <div className="hanging-stars absolute inset-x-6 top-0 h-28" />
          <div className="catalog-hero-aside absolute inset-x-3 bottom-0 top-12 rounded-[2rem] border border-border/70 bg-background/42 p-6 backdrop-blur-md dark:bg-background/60 dark:border-border/40">
            <div className="catalog-hero-aside-beam absolute inset-x-8 top-10 h-px bg-gradient-to-r from-transparent via-primary/40 to-transparent dark:via-primary/20" />
            <div className="catalog-hero-aside-star absolute left-1/2 top-10 h-3 w-3 -translate-x-1/2 rounded-full bg-primary celestial-twinkle-slow dark:bg-primary/60" />
            <div className="catalog-hero-aside-sun absolute left-10 top-16 h-14 w-14 rounded-full solar-halo celestial-pulse-glow dark:opacity-40" />
            <div className="catalog-hero-aside-moon absolute bottom-10 right-10 h-16 w-16 rounded-full lunar-disc celestial-float-delayed" />
            <div className="catalog-hero-aside-orbit-outer celestial-orbit celestial-orbit-spin absolute left-1/2 top-1/2 h-32 w-32 -translate-x-1/2 -translate-y-1/2 border-primary/30 bg-background/30 dark:border-primary/15 dark:bg-transparent" />
            <div className="catalog-hero-aside-orbit-inner celestial-orbit celestial-orbit-spin-reverse absolute left-1/2 top-1/2 h-20 w-20 -translate-x-1/2 -translate-y-1/2 bg-primary/10 ring-1 ring-primary/30 dark:bg-transparent dark:ring-primary/15" />
            <div className="catalog-hero-aside-core absolute left-1/2 top-1/2 h-7 w-7 -translate-x-1/2 -translate-y-1/2 rounded-full border border-primary/35 bg-background/60 celestial-pulse-glow dark:border-primary/20" />
            <div className="catalog-hero-note absolute bottom-6 left-6 right-6 rounded-[1.35rem] border border-border/60 bg-background/55 px-4 py-4">
              <p className="text-[10px] uppercase tracking-[0.24em] text-primary/80">
                Current Ritual
              </p>
              <p className="mt-2 text-sm leading-6 text-foreground">{note ?? description}</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
