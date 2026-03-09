/**
 * Help & Support page.
 *
 * Provides a Getting Started guide, FAQ accordion, support channels,
 * and agent pipeline overview — all styled with the celestial theme.
 */

import { useState } from 'react';
import { CelestialCatalogHero } from '@/components/common/CelestialCatalogHero';
import { Button } from '@/components/ui/button';
import {
  ChevronDown,
  BookOpen,
  MessageCircleQuestion,
  LifeBuoy,
  Workflow,
  ExternalLink,
} from 'lucide-react';
import { cn } from '@/lib/utils';

/* ------------------------------------------------------------------ */
/*  FAQ Data                                                           */
/* ------------------------------------------------------------------ */

interface FaqItem {
  question: string;
  answer: string;
  category: 'Setup' | 'Usage' | 'Pipeline' | 'Contributing';
}

const FAQ_ITEMS: FaqItem[] = [
  {
    category: 'Setup',
    question: 'How do I create a GitHub OAuth App?',
    answer:
      'Go to GitHub Developer Settings → New OAuth App. Set the callback URL to http://localhost:5173/api/v1/auth/github/callback. Copy the Client ID and Client Secret into your .env file.',
  },
  {
    category: 'Setup',
    question: 'What are the system requirements?',
    answer:
      'Docker and Docker Compose (recommended), or Node.js 22+ and Python 3.13+ for local development. A GitHub Copilot subscription is required for the agent pipeline.',
  },
  {
    category: 'Setup',
    question: 'Can I use GitHub Codespaces instead of Docker?',
    answer:
      'Yes — Codespaces is the easiest way to start. Click Code → Codespaces → Create codespace on main and the dev container handles everything automatically.',
  },
  {
    category: 'Usage',
    question: 'How do I create an issue with the chat?',
    answer:
      'Type a natural language feature description in the chat input. The AI generates a structured GitHub Issue with title, body, labels, and priority that you can refine before submitting.',
  },
  {
    category: 'Usage',
    question: 'How do I configure which agents run on my issues?',
    answer:
      'Go to the Agents page, browse the catalog, and drag agents into board column slots. Each column can have different agents assigned. Changes are saved per-project.',
  },
  {
    category: 'Usage',
    question: 'What are chores and how do I use them?',
    answer:
      'Chores are recurring maintenance tasks (like dependency updates) that can be scheduled and tracked. Go to the Chores page to create, edit, and manage chores.',
  },
  {
    category: 'Pipeline',
    question: 'What is the agent pipeline?',
    answer:
      'An automated workflow that turns feature requests into code. Agents run in sequence: specify → plan → tasks → implement → review. Each agent gets a sub-issue and child PR.',
  },
  {
    category: 'Pipeline',
    question: 'Why is my pipeline not advancing?',
    answer:
      'Check that polling is running (GET /api/v1/workflow/polling/status) and that your project has the required columns: Backlog, Ready, In Progress, In Review. See the Troubleshooting guide for more details.',
  },
  {
    category: 'Contributing',
    question: 'How do I contribute to this project?',
    answer:
      'Fork the repository, create a feature branch, make changes following existing patterns, run tests, and open a pull request. See the Testing guide for details on the test suite.',
  },
  {
    category: 'Contributing',
    question: 'How do I create a custom agent?',
    answer:
      'Custom agents are markdown files in .github/agents/. Each file describes the agent role, instructions, and tools. See the Custom Agents Best Practices guide.',
  },
];

const FAQ_CATEGORIES = ['Setup', 'Usage', 'Pipeline', 'Contributing'] as const;

/* ------------------------------------------------------------------ */
/*  Collapsible FAQ Item                                               */
/* ------------------------------------------------------------------ */

function FaqAccordionItem({ item }: { item: FaqItem }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="rounded-2xl border border-border/60 bg-background/30 backdrop-blur-sm transition-colors hover:border-primary/30">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="celestial-focus flex w-full items-center gap-3 rounded-2xl px-5 py-4 text-left"
        aria-expanded={open}
      >
        <ChevronDown
          size={16}
          className={cn(
            'shrink-0 text-primary/70 transition-transform duration-200',
            !open && '-rotate-90'
          )}
        />
        <span className="text-sm font-medium text-foreground">{item.question}</span>
      </button>

      <div
        className={cn(
          'grid transition-[grid-template-rows] duration-200',
          open ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'
        )}
      >
        <div className="overflow-hidden">
          <p className="px-5 pb-4 pl-12 text-sm leading-relaxed text-muted-foreground">
            {item.answer}
          </p>
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Section Wrapper                                                    */
/* ------------------------------------------------------------------ */

interface SectionProps {
  icon: React.ElementType;
  eyebrow: string;
  title: string;
  children: React.ReactNode;
  id?: string;
}

function Section({ icon: Icon, eyebrow, title, children, id }: SectionProps) {
  return (
    <section id={id} className="scroll-mt-6">
      <div className="mb-4 flex items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
          <Icon size={16} className="text-primary" />
        </div>
        <div>
          <p className="text-[10px] uppercase tracking-[0.24em] text-primary/80">{eyebrow}</p>
          <h3 className="text-lg font-display font-medium tracking-[0.02em]">{title}</h3>
        </div>
      </div>
      {children}
    </section>
  );
}

/* ------------------------------------------------------------------ */
/*  Pipeline Stage Card                                                */
/* ------------------------------------------------------------------ */

interface StageProps {
  emoji: string;
  column: string;
  agent: string;
  output: string;
}

function PipelineStage({ emoji, column, agent, output }: StageProps) {
  return (
    <div className="flex items-start gap-3 rounded-2xl border border-border/50 bg-background/30 px-4 py-3 backdrop-blur-sm">
      <span className="mt-0.5 text-lg leading-none">{emoji}</span>
      <div className="min-w-0">
        <p className="text-sm font-medium text-foreground">{column}</p>
        <p className="text-xs text-muted-foreground">
          {agent} → <span className="text-primary/90">{output}</span>
        </p>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Help Page                                                          */
/* ------------------------------------------------------------------ */

export function HelpPage() {
  const [activeCategory, setActiveCategory] = useState<string>('all');

  const filteredFaq =
    activeCategory === 'all'
      ? FAQ_ITEMS
      : FAQ_ITEMS.filter((item) => item.category === activeCategory);

  return (
    <div className="celestial-fade-in flex h-full flex-col gap-5 overflow-auto rounded-[1.5rem] border border-border/70 bg-background/42 p-4 backdrop-blur-sm sm:gap-6 sm:rounded-[1.75rem] sm:p-6">
      {/* Hero */}
      <CelestialCatalogHero
        eyebrow="Support Center"
        title="Help & guidance for Solune."
        description="Find answers to common questions, learn how to get started, and explore the agent pipeline. Everything you need to make the most of Agent Projects."
        note="Browse getting started guides, FAQ, and pipeline documentation all in one place."
        stats={[
          { label: 'FAQ topics', value: String(FAQ_ITEMS.length) },
          { label: 'Categories', value: String(FAQ_CATEGORIES.length) },
        ]}
        actions={
          <>
            <Button variant="default" size="lg" asChild>
              <a href="#getting-started">Getting started</a>
            </Button>
            <Button variant="outline" size="lg" asChild>
              <a href="#faq">Browse FAQ</a>
            </Button>
            <Button variant="outline" size="lg" asChild>
              <a
                href="https://github.com/Boykai/github-workflows/issues"
                target="_blank"
                rel="noopener noreferrer"
              >
                Report an issue
              </a>
            </Button>
          </>
        }
      />

      {/* Content Grid */}
      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_22rem] xl:items-start">
        {/* Left Column — Main Content */}
        <div className="flex flex-col gap-6">
          {/* Getting Started */}
          <div className="celestial-panel rounded-[1.5rem] p-5 sm:p-6">
            <Section
              id="getting-started"
              icon={BookOpen}
              eyebrow="Onboarding"
              title="Getting Started"
            >
              <ol className="mt-3 flex flex-col gap-3 text-sm leading-relaxed text-muted-foreground">
                <li className="flex gap-3">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/15 text-xs font-semibold text-primary">
                    1
                  </span>
                  <span>
                    <strong className="text-foreground">Clone & configure</strong> — Clone the repo,
                    copy <code className="rounded bg-primary/10 px-1.5 py-0.5 text-xs text-primary">.env.example</code> to{' '}
                    <code className="rounded bg-primary/10 px-1.5 py-0.5 text-xs text-primary">.env</code>, and set your GitHub OAuth credentials.
                  </span>
                </li>
                <li className="flex gap-3">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/15 text-xs font-semibold text-primary">
                    2
                  </span>
                  <span>
                    <strong className="text-foreground">Start the app</strong> — Run{' '}
                    <code className="rounded bg-primary/10 px-1.5 py-0.5 text-xs text-primary">docker compose up --build -d</code> or use GitHub Codespaces.
                  </span>
                </li>
                <li className="flex gap-3">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/15 text-xs font-semibold text-primary">
                    3
                  </span>
                  <span>
                    <strong className="text-foreground">Sign in</strong> — Open{' '}
                    <code className="rounded bg-primary/10 px-1.5 py-0.5 text-xs text-primary">localhost:5173</code> and authenticate with GitHub.
                  </span>
                </li>
                <li className="flex gap-3">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/15 text-xs font-semibold text-primary">
                    4
                  </span>
                  <span>
                    <strong className="text-foreground">Create a project</strong> — Link a GitHub
                    Project board with Backlog, Ready, In Progress, In Review, and Done columns.
                  </span>
                </li>
                <li className="flex gap-3">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/15 text-xs font-semibold text-primary">
                    5
                  </span>
                  <span>
                    <strong className="text-foreground">Start building</strong> — Describe a feature
                    in the chat and the agent pipeline handles the rest.
                  </span>
                </li>
              </ol>
              <div className="mt-5">
                <Button variant="outline" size="sm" asChild>
                  <a href="https://github.com/Boykai/github-workflows/blob/main/docs/setup.md" target="_blank" rel="noopener noreferrer">
                    Full setup guide <ExternalLink size={14} className="ml-1.5" />
                  </a>
                </Button>
              </div>
            </Section>
          </div>

          {/* FAQ */}
          <div className="celestial-panel rounded-[1.5rem] p-5 sm:p-6">
            <Section id="faq" icon={MessageCircleQuestion} eyebrow="Knowledge Base" title="Frequently Asked Questions">
              {/* Category filter chips */}
              <div className="mb-4 mt-3 flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => setActiveCategory('all')}
                  className={cn(
                    'celestial-focus rounded-full border px-3 py-1 text-xs font-medium transition-colors',
                    activeCategory === 'all'
                      ? 'border-primary/40 bg-primary/15 text-primary'
                      : 'border-border/60 text-muted-foreground hover:border-primary/30 hover:text-foreground'
                  )}
                >
                  All
                </button>
                {FAQ_CATEGORIES.map((cat) => (
                  <button
                    key={cat}
                    type="button"
                    onClick={() => setActiveCategory(cat)}
                    className={cn(
                      'celestial-focus rounded-full border px-3 py-1 text-xs font-medium transition-colors',
                      activeCategory === cat
                        ? 'border-primary/40 bg-primary/15 text-primary'
                        : 'border-border/60 text-muted-foreground hover:border-primary/30 hover:text-foreground'
                    )}
                  >
                    {cat}
                  </button>
                ))}
              </div>

              {/* FAQ items */}
              <div className="flex flex-col gap-2">
                {filteredFaq.map((item) => (
                  <FaqAccordionItem key={item.question} item={item} />
                ))}
              </div>
            </Section>
          </div>
        </div>

        {/* Right Column — Support & Pipeline */}
        <div className="flex flex-col gap-5">
          {/* Support Channels */}
          <div className="celestial-panel rounded-[1.5rem] p-5 sm:p-6">
            <Section icon={LifeBuoy} eyebrow="Community" title="Support Channels">
              <div className="mt-3 flex flex-col gap-3">
                <a
                  href="https://github.com/Boykai/github-workflows/issues"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="celestial-focus group flex items-center gap-3 rounded-2xl border border-border/50 bg-background/30 px-4 py-3 backdrop-blur-sm transition-colors hover:border-primary/30"
                >
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 transition-colors group-hover:bg-primary/20">
                    <ExternalLink size={14} className="text-primary" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-foreground">GitHub Issues</p>
                    <p className="text-xs text-muted-foreground">Report bugs or request features</p>
                  </div>
                </a>
                <a
                  href="https://github.com/Boykai/github-workflows/discussions"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="celestial-focus group flex items-center gap-3 rounded-2xl border border-border/50 bg-background/30 px-4 py-3 backdrop-blur-sm transition-colors hover:border-primary/30"
                >
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 transition-colors group-hover:bg-primary/20">
                    <ExternalLink size={14} className="text-primary" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-foreground">GitHub Discussions</p>
                    <p className="text-xs text-muted-foreground">
                      Ask questions and share ideas
                    </p>
                  </div>
                </a>
              </div>
            </Section>
          </div>

          {/* Agent Pipeline Overview */}
          <div className="celestial-panel rounded-[1.5rem] p-5 sm:p-6">
            <Section
              id="pipeline-overview"
              icon={Workflow}
              eyebrow="Automation"
              title="Agent Pipeline"
            >
              <div className="mt-3 flex flex-col gap-2">
                <PipelineStage emoji="📋" column="Backlog" agent="speckit.specify" output="spec.md" />
                <PipelineStage emoji="📝" column="Ready" agent="speckit.plan" output="plan.md" />
                <PipelineStage emoji="📝" column="Ready" agent="speckit.tasks" output="tasks.md" />
                <PipelineStage emoji="🔄" column="In Progress" agent="speckit.implement" output="Code changes" />
                <PipelineStage emoji="👀" column="In Review" agent="Copilot review" output="PR ready" />
                <PipelineStage emoji="✅" column="Done" agent="Merged" output="Complete" />
              </div>
              <div className="mt-4">
                <Button variant="outline" size="sm" asChild>
                  <a href="https://github.com/Boykai/github-workflows/blob/main/docs/agent-pipeline.md" target="_blank" rel="noopener noreferrer">
                    Full pipeline docs <ExternalLink size={14} className="ml-1.5" />
                  </a>
                </Button>
              </div>
            </Section>
          </div>
        </div>
      </div>
    </div>
  );
}
