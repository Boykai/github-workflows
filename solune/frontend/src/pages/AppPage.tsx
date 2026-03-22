/**
 * AppPage — welcome/landing page with quick-access cards.
 */

import { useNavigate } from 'react-router-dom';
import { Kanban, GitBranch, Bot, ListChecks, Sparkles, Boxes, ArrowUpRight } from '@/lib/icons';

const quickLinks = [
  {
    path: '/projects',
    label: 'Projects',
    description: 'View and manage your Kanban board',
    icon: Kanban,
  },
  {
    path: '/pipeline',
    label: 'Agents Pipelines',
    description: 'Visualize and manage your agent workflows',
    icon: GitBranch,
  },
  { path: '/agents', label: 'Agents', description: 'Configure and manage agents', icon: Bot },
  { path: '/chores', label: 'Chores', description: 'Schedule and track chores', icon: ListChecks },
];

export function AppPage() {
  const navigate = useNavigate();

  return (
    <div className="starfield celestial-fade-in flex min-h-full flex-col justify-center p-8 lg:p-12">
      <div className="mx-auto grid w-full max-w-6xl gap-8 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
        <section className="flex min-h-[34rem] flex-col justify-between">
          <div className="mb-6 inline-flex items-center gap-3 rounded-full border border-primary/20 bg-primary/10 px-4 py-2 text-xs uppercase tracking-[0.28em] text-primary">
            <span>//</span>
            <span>Daily affirmations for delivery</span>
          </div>

          <div>
            <h1 className="max-w-xl text-5xl text-foreground sm:text-6xl lg:text-[5rem]">
              Change your project mindset.
            </h1>
            <p className="mt-6 max-w-lg text-lg leading-8 text-muted-foreground">
              Move across projects, pipelines, chores, and agent operations inside a shell that
              feels sunlit by day, lunar by night, and quieter than a typical utility dashboard.
            </p>
          </div>

          <div className="grid gap-6 lg:max-w-xl">
            <div className="flex flex-wrap gap-3 text-xs uppercase tracking-[0.24em] text-muted-foreground/80">
              <span className="rounded-full border border-border/70 px-4 py-2">
                Moon phase focus
              </span>
              <span className="rounded-full border border-border/70 px-4 py-2">
                Solar highlights
              </span>
              <span className="rounded-full border border-border/70 px-4 py-2">
                Ambient navigation
              </span>
            </div>

            <div className="celestial-panel rounded-[1.8rem] border border-border/70 p-6">
              <p className="text-[11px] uppercase tracking-[0.32em] text-primary/80">
                Daily affirmation
              </p>
              <div className="mt-4 flex items-start justify-between gap-6">
                <div>
                  <p className="max-w-sm text-2xl font-display font-medium leading-tight text-foreground">
                    Keep the active path bright and let the rest of the board fall quiet.
                  </p>
                  <p className="mt-3 text-sm leading-6 text-muted-foreground">
                    The shell, navigation, and calls to action now carry more solar lift in light
                    mode without crowding the app’s real work.
                  </p>
                </div>
                <div className="hidden shrink-0 rounded-full border border-primary/25 bg-primary/10 px-4 py-2 text-[11px] uppercase tracking-[0.28em] text-primary md:block">
                  Calm velocity
                </div>
              </div>
            </div>
          </div>
        </section>

        <div className="relative mx-auto flex h-[32rem] w-full max-w-[32rem] items-center justify-center">
          <div className="absolute inset-x-10 top-10 h-24 rounded-full bg-primary/10 blur-3xl" />
          <div className="hanging-stars absolute inset-x-8 top-0 hidden h-28 lg:block" />
          <div className="celestial-orbit inset-5" />
          <div className="celestial-orbit inset-14 border-primary/20" />
          <div className="solar-halo absolute left-10 top-14 h-16 w-16 rounded-full" />
          <div className="lunar-disc absolute right-8 top-12 h-14 w-14 rounded-full" />

          <div className="celestial-panel golden-ring relative w-full rounded-[2.2rem] border border-border/80 p-8 backdrop-blur-md">
            <div className="absolute left-1/2 top-0 h-16 w-px -translate-x-1/2 bg-gradient-to-b from-primary/55 to-transparent" />
            <div className="absolute left-1/2 top-16 h-2.5 w-2.5 -translate-x-1/2 rounded-full bg-primary" />
            <div className="mb-8 text-center">
              <button
                type="button"
                onClick={() => navigate('/apps')}
                aria-label="Open Apps page"
                title="Open Apps page"
                className="celestial-focus celestial-pulse-glow group relative mx-auto mb-4 flex h-24 w-24 items-center justify-center rounded-full border border-primary/35 bg-[radial-gradient(circle_at_30%_28%,hsl(var(--glow)/0.24),transparent_38%),linear-gradient(180deg,hsl(var(--primary)/0.12)_0%,hsl(var(--background)/0.66)_100%)] text-primary shadow-[0_0_28px_hsl(var(--glow)/0.18)] transition-[transform,border-color,box-shadow,background-color] duration-300 hover:-translate-y-0.5 hover:border-primary/55 hover:shadow-[0_0_40px_hsl(var(--glow)/0.28)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:ring-offset-2 focus-visible:ring-offset-background"
              >
                <Boxes className="celestial-float h-10 w-10 transition-transform duration-300 group-hover:scale-105" />
                <span className="pointer-events-none absolute -right-1.5 -top-1.5 flex h-8 w-8 items-center justify-center rounded-full border border-primary/30 bg-background/88 text-primary shadow-[0_0_18px_hsl(var(--glow)/0.14)]">
                  <Sparkles className="celestial-twinkle h-3.5 w-3.5" />
                </span>
                <span className="pointer-events-none absolute -bottom-1 right-1 flex items-center gap-1 rounded-full border border-primary/25 bg-background/90 px-2 py-1 text-[9px] font-semibold uppercase tracking-[0.22em] text-primary opacity-0 transition-opacity duration-300 group-hover:opacity-100">
                  Apps
                  <ArrowUpRight className="h-2.5 w-2.5" />
                </span>
              </button>
              <p className="text-xs uppercase tracking-[0.28em] text-primary/80">
                Navigate the cosmos
              </p>
              <p className="mt-3 text-sm leading-6 text-muted-foreground">
                Quick paths are arranged inside a more ceremonial composition, but their routing and
                behavior are unchanged.
              </p>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {quickLinks.map((link) => (
                <button
                  key={link.path}
                  onClick={() => navigate(link.path)}
                  className="rounded-[1.25rem] border border-border/70 bg-background/55 p-5 text-left transition-all hover:-translate-y-0.5 hover:border-primary/30 hover:bg-primary/10 hover:shadow-md"
                >
                  <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-full bg-primary/12 text-primary">
                    <link.icon className="h-5 w-5" />
                  </div>
                  <h3 className="mb-1 text-sm font-semibold uppercase tracking-[0.12em] text-foreground">
                    {link.label}
                  </h3>
                  <p className="text-xs leading-5 text-muted-foreground">{link.description}</p>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
