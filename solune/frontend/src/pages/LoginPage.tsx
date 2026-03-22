/**
 * LoginPage — Solune-branded login page for unauthenticated users.
 * Renders outside AppLayout (no sidebar/topbar).
 */

import { LoginButton } from '@/components/auth/LoginButton';
import { AnimatedBackground } from '@/components/AnimatedBackground';
import { useTheme } from '@/components/ThemeProvider';
import { MoonStar, SunMedium } from '@/lib/icons';

export function LoginPage() {
  const { theme, setTheme } = useTheme();
  const isDark =
    theme === 'dark' ||
    (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);

  const toggleTheme = () => {
    setTheme(isDark ? 'light' : 'dark');
  };

  return (
    <div className="starfield celestial-fade-in relative flex min-h-screen items-center justify-center overflow-hidden bg-background px-6 py-12">
      <AnimatedBackground />
      <div className="relative grid w-full max-w-6xl gap-10 lg:grid-cols-[1.2fr_0.8fr] lg:items-center">
        <section className="flex min-h-[560px] max-w-2xl flex-col justify-between py-6">
          <div className="mb-6 inline-flex items-center gap-3 rounded-full border border-primary/20 bg-primary/10 px-4 py-2 text-xs uppercase tracking-[0.3em] text-primary">
            <span>//</span>
            <span>Sun & Moon Workspace</span>
          </div>
          <div>
            <h1 className="max-w-xl text-5xl text-foreground sm:text-6xl lg:text-[5.4rem]">
              Change your workflow mindset.
            </h1>
            <p className="mt-6 max-w-lg text-base leading-7 text-muted-foreground sm:text-lg">
              Solune reframes GitHub operations with a brighter solar shell by day, a lunar shell by
              night, and calmer hierarchy throughout.
            </p>
          </div>

          <div className="grid gap-6 lg:max-w-xl">
            <div className="grid gap-3 text-xs uppercase tracking-[0.24em] text-muted-foreground/80 sm:grid-cols-3">
              <span className="rounded-full border border-border/70 px-4 py-2 text-center">
                Moonlit triage
              </span>
              <span className="rounded-full border border-border/70 px-4 py-2 text-center">
                Solar signals
              </span>
              <span className="rounded-full border border-border/70 px-4 py-2 text-center">
                Ambient focus
              </span>
            </div>

            <div>
              <p className="text-[11px] uppercase tracking-[0.32em] text-primary/80">
                Daily affirmations
              </p>
              <p className="mt-3 max-w-sm text-2xl font-display font-medium leading-tight text-foreground">
                Guide active work with brighter highlights and quieter night around it.
              </p>
            </div>
          </div>
        </section>

        <div className="relative mx-auto flex min-h-[560px] w-full max-w-[30rem] items-center justify-center">
          <div className="hanging-stars absolute inset-x-10 top-6 hidden h-28 lg:block" />
          <div className="celestial-orbit celestial-orbit-spin inset-5 hidden lg:block" />
          <div className="celestial-orbit celestial-orbit-spin-reverse inset-16 hidden border-primary/25 lg:block" />
          <div className="solar-halo celestial-pulse-glow absolute left-8 top-16 h-16 w-16 rounded-full" />
          <div className="lunar-disc celestial-float absolute right-7 top-12 h-14 w-14 rounded-full" />

          <div className="relative flex h-[29rem] w-full items-center justify-center">
            <div className="absolute bottom-20 h-[18rem] w-[18rem] rounded-full bg-[linear-gradient(180deg,hsl(var(--muted)),color-mix(in_srgb,hsl(var(--muted))_82%,black))] opacity-90" />
            <div className="absolute bottom-24 h-[19rem] w-[11rem] rounded-[999px] border border-border/50 bg-card/65 backdrop-blur-md" />
            <div className="absolute bottom-[16.5rem] left-1/2 h-14 w-14 -translate-x-1/2 rounded-full border border-border/60 bg-background/90" />
            <div className="absolute bottom-[14rem] left-[calc(50%-6.8rem)] h-28 w-24 rounded-[999px_999px_1.5rem_1.5rem] border border-border/45 bg-card/90" />
            <div className="absolute bottom-[14rem] right-[calc(50%-6.8rem)] h-28 w-24 rounded-[999px_999px_1.5rem_1.5rem] border border-border/45 bg-card/90" />
            <div className="absolute bottom-[15.6rem] left-[calc(50%-1.1rem)] h-10 w-[2.2rem] rounded-full bg-card" />
            <div className="absolute bottom-[21rem] left-1/2 h-8 w-[15rem] -translate-x-1/2 rounded-full bg-primary/90 shadow-[0_0_48px_hsl(var(--glow)/0.32)]" />
            <div className="absolute bottom-[20.6rem] left-[calc(50%-8.6rem)] h-10 w-20 rounded-full bg-primary/90" />
            <div className="absolute bottom-[20.6rem] right-[calc(50%-8.6rem)] h-10 w-20 rounded-full bg-primary/90" />
            <div className="absolute bottom-[20.9rem] left-[calc(50%-10.6rem)] h-12 w-20 rounded-full bg-primary/90" />
            <div className="absolute bottom-[20.9rem] right-[calc(50%-10.6rem)] h-12 w-20 rounded-full bg-primary/90" />
            <div className="absolute bottom-[6.8rem] h-[7rem] w-[13rem] rounded-[48%_48%_38%_38%] bg-night/95" />
            <div className="absolute bottom-[7.4rem] h-[6rem] w-[11rem] rounded-[48%_48%_38%_38%] bg-[radial-gradient(circle_at_center,hsl(var(--gold)/0.6)_0_2px,transparent_3px)] bg-[length:24px_24px]" />
            <div className="absolute bottom-[17.5rem] left-[calc(50%-1.4rem)] h-2 w-2 rounded-full bg-primary" />
            <div className="absolute bottom-[17.2rem] left-[calc(50%-3.2rem)] h-px w-7 bg-border/60" />
            <div className="absolute bottom-[17.2rem] right-[calc(50%-3.2rem)] h-px w-7 bg-border/60" />
          </div>

          <div className="celestial-panel celestial-fade-in golden-ring absolute bottom-0 left-1/2 z-10 flex w-full max-w-md -translate-x-1/2 flex-col items-center gap-6 rounded-[2rem] border border-border/80 p-8 backdrop-blur-md">
            <button
              type="button"
              onClick={toggleTheme}
              aria-label={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
              title={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
              className="flex h-16 w-16 items-center justify-center rounded-full border border-primary/25 bg-primary/12 text-2xl text-primary transition-[transform,background-color,border-color,color] duration-300 hover:border-primary/45 hover:bg-primary/18 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:ring-offset-2 focus-visible:ring-offset-background active:scale-95"
            >
              {isDark ? <MoonStar className="h-8 w-8" /> : <SunMedium className="h-8 w-8" />}
            </button>
            <div className="text-center">
              <h2 className="mb-2 text-4xl font-display font-medium tracking-[0.08em] text-foreground">
                Solune
              </h2>
              <p className="text-sm leading-6 text-muted-foreground">
                Enter the Sun & Moon workspace and continue where your project flow left off.
              </p>
            </div>
            <div className="w-full">
              <LoginButton />
            </div>
            <p className="text-center text-xs uppercase tracking-[0.24em] text-muted-foreground/80">
              GitHub sign in required
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
