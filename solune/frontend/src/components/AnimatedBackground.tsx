/**
 * AnimatedBackground — decorative celestial background elements for the login page.
 */

export function AnimatedBackground() {
  return (
    <>
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,hsl(var(--glow)/0.34),transparent_20%),radial-gradient(circle_at_70%_20%,hsl(var(--accent)/0.16),transparent_24%),linear-gradient(180deg,hsl(var(--background)/0.14),transparent)] dark:bg-[radial-gradient(circle_at_top,hsl(var(--glow)/0.14),transparent_18%),radial-gradient(circle_at_70%_20%,hsl(var(--accent)/0.18),transparent_22%),linear-gradient(180deg,hsl(var(--night)/0.4),hsl(var(--night)/0.06))]" />
      <div className="pointer-events-none absolute inset-0 opacity-80">
        <div className="celestial-orbit celestial-orbit-spin left-[54%] top-[14%] hidden h-[32rem] w-[32rem] lg:block" />
        <div className="celestial-orbit celestial-orbit-spin-reverse left-[58%] top-[18%] hidden h-[24rem] w-[24rem] border-primary/25 lg:block" />
        <div className="absolute left-[6%] top-[8%] h-32 w-32 rounded-full bg-primary/10 blur-3xl celestial-pulse-glow" />
        <div className="absolute left-[12%] top-[12%] hidden items-center gap-12 text-[11px] uppercase tracking-[0.3em] text-muted-foreground/70 lg:flex">
          <span>Meditation</span>
          <span>Tarot</span>
          <span>Mission</span>
          <span>Initiatives</span>
        </div>
      </div>
    </>
  );
}
