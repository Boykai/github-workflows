/**
 * HelpPage — /help route with FAQ, feature guides, slash commands, and tour replay.
 * Sections: Hero → Getting Started → FAQ → Feature Guides → Slash Commands
 */

import { Play, Kanban, GitBranch, Bot, Wrench, ListChecks, Settings, Boxes, LayoutDashboard, Clock } from '@/lib/icons';
import { CelestialCatalogHero } from '@/components/common/CelestialCatalogHero';
import { FaqAccordion } from '@/components/help/FaqAccordion';
import { FeatureGuideCard } from '@/components/help/FeatureGuideCard';
import { Button } from '@/components/ui/button';
import { useOnboarding } from '@/hooks/useOnboarding';
import { getAllCommands } from '@/lib/commands/registry';
import type { FaqEntry } from '@/types';

const FAQ_ENTRIES: FaqEntry[] = [
  // Getting Started
  {
    id: 'getting-started-1',
    question: 'How do I connect my GitHub repository?',
    answer: 'Click the project selector at the bottom of the sidebar, then choose a repository from your GitHub organizations. Solune will sync your project board automatically.',
    category: 'getting-started',
  },
  {
    id: 'getting-started-2',
    question: 'What is the Projects board?',
    answer: 'The Projects board is a Kanban-style view of your GitHub project issues. You can drag cards between status columns, and Solune keeps everything in sync with GitHub.',
    category: 'getting-started',
  },
  {
    id: 'getting-started-3',
    question: 'How do I create my first task?',
    answer: 'Open the chat and describe what you need in natural language. Solune will propose a task with title, description, and metadata. Confirm to create it as a GitHub issue.',
    category: 'getting-started',
  },
  // Agents & Pipelines
  {
    id: 'agents-pipelines-1',
    question: 'What are agent pipelines?',
    answer: 'Agent pipelines are automated multi-step workflows. Each stage is handled by a different AI agent — for example, one agent writes code, another reviews it, and a third creates tests.',
    category: 'agents-pipelines',
  },
  {
    id: 'agents-pipelines-2',
    question: 'How do I assign agents to a pipeline stage?',
    answer: 'Go to the Agents Pipelines page, select a pipeline, and drag agents into each stage slot. You can use built-in agents or configure custom ones from your repository.',
    category: 'agents-pipelines',
  },
  {
    id: 'agents-pipelines-3',
    question: 'Can I run a pipeline on an existing issue?',
    answer: 'Yes — use the @mention syntax in chat (e.g., @pipeline-name) followed by an issue description, or launch a pipeline directly from the pipeline page with a linked issue.',
    category: 'agents-pipelines',
  },
  // Chat & Voice
  {
    id: 'chat-voice-1',
    question: 'What slash commands are available?',
    answer: 'Type / in the chat to see all available commands. Common ones include /help, /theme, and /clear. See the Slash Commands section below for the full list.',
    category: 'chat-voice',
  },
  {
    id: 'chat-voice-2',
    question: 'Can I attach files to chat messages?',
    answer: 'Yes — click the attachment icon in the chat input or drag-and-drop files. Supported formats include images, PDFs, markdown, and code files up to 10 MB each.',
    category: 'chat-voice',
  },
  {
    id: 'chat-voice-3',
    question: 'Does Solune support voice input?',
    answer: 'Yes — click the microphone icon in the chat input to use speech-to-text. Your browser must support the Web Speech API (Chrome and Edge have the best support).',
    category: 'chat-voice',
  },
  // Settings & Integration
  {
    id: 'settings-integration-1',
    question: 'How do I switch between light and dark mode?',
    answer: 'Click the sun/moon icon in the sidebar header, or use the /theme command in chat. Your preference is saved and persists across sessions.',
    category: 'settings-integration',
  },
  {
    id: 'settings-integration-2',
    question: 'Can I customize AI model settings?',
    answer: 'Yes — go to Settings and adjust the AI provider, model, and temperature. You can choose between Copilot and Azure OpenAI backends.',
    category: 'settings-integration',
  },
  {
    id: 'settings-integration-3',
    question: 'How do notifications work?',
    answer: 'Solune sends in-app notifications for task status changes, agent completions, and new recommendations. Configure which notifications you receive in Settings.',
    category: 'settings-integration',
  },
  // New FAQ entries
  {
    id: 'getting-started-4',
    question: 'What is the Activity page?',
    answer: 'The Activity page shows a unified timeline of recent actions, events, and changes across your workspace — including issue updates, pipeline runs, and agent completions.',
    category: 'getting-started',
  },
  {
    id: 'settings-integration-4',
    question: 'How do I create a new app?',
    answer: 'Go to the Apps page and click "Create App." You can spin up a new repository, link an existing one, or configure an app template to get started quickly.',
    category: 'settings-integration',
  },
  {
    id: 'settings-integration-5',
    question: 'What are MCP tools?',
    answer: 'MCP (Model Context Protocol) tools are external capabilities you can attach to your agents. Upload tool configurations on the Tools page to extend what your agents can do — for example, running shell commands or querying APIs.',
    category: 'settings-integration',
  },
  {
    id: 'agents-pipelines-4',
    question: 'Can Solune monitor multiple projects?',
    answer: 'Yes — use the project selector at the bottom of the sidebar to switch between repositories. Each project has its own board, pipelines, and agent configurations.',
    category: 'agents-pipelines',
  },
];

const FEATURE_GUIDES = [
  { title: 'App Dashboard', description: 'Overview of your workspace activity and quick actions.', icon: LayoutDashboard, href: '/' },
  { title: 'Projects', description: 'Kanban board for managing GitHub project issues.', icon: Kanban, href: '/projects' },
  { title: 'Agent Pipelines', description: 'Define and run multi-step agent workflows.', icon: GitBranch, href: '/pipeline' },
  { title: 'Agents', description: 'Browse and configure AI agents for your workflows.', icon: Bot, href: '/agents' },
  { title: 'Tools', description: 'Manage MCP tools available to your agents.', icon: Wrench, href: '/tools' },
  { title: 'Chores', description: 'Recurring tasks and maintenance automation.', icon: ListChecks, href: '/chores' },
  { title: 'Apps', description: 'Explore and manage Solune app extensions.', icon: Boxes, href: '/apps' },
  { title: 'Settings', description: 'Configure AI, display, workflow, and notification preferences.', icon: Settings, href: '/settings' },
  { title: 'Activity', description: 'Track recent actions, events, and changes across your workspace.', icon: Clock, href: '/activity' },
];

export function HelpPage() {
  const { restart } = useOnboarding();
  const commands = getAllCommands();

  return (
    <div className="mx-auto max-w-4xl space-y-12 pb-16">
      {/* Hero */}
      <CelestialCatalogHero
        eyebrow="// Guidance & support"
        title="Help Center"
        description="Everything you need to navigate your celestial workspace."
        actions={
          <Button onClick={restart} variant="outline" size="sm">
            <Play className="mr-2 h-4 w-4" />
            Replay Tour
          </Button>
        }
      />

      {/* Getting Started */}
      <section>
        <h2 className="mb-4 text-lg font-semibold text-foreground">Getting Started</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <FeatureGuideCard
            title="Create a Project"
            description="Link a GitHub repository and start managing issues."
            icon={Kanban}
            href="/projects"
          />
          <FeatureGuideCard
            title="Build a Pipeline"
            description="Set up multi-step agent workflows for your issues."
            icon={GitBranch}
            href="/pipeline"
          />
          <FeatureGuideCard
            title="Chat with Solune"
            description="Create tasks and trigger workflows using natural language."
            icon={Bot}
            href="/"
          />
        </div>
      </section>

      {/* FAQ */}
      <section>
        <h2 className="mb-4 text-lg font-semibold text-foreground">Frequently Asked Questions</h2>
        <FaqAccordion entries={FAQ_ENTRIES} />
      </section>

      {/* Feature Guides */}
      <section>
        <h2 className="mb-4 text-lg font-semibold text-foreground">Feature Guides</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURE_GUIDES.map((guide) => (
            <FeatureGuideCard key={guide.href} {...guide} />
          ))}
        </div>
      </section>

      {/* Slash Commands */}
      <section>
        <h2 className="mb-4 text-lg font-semibold text-foreground">Slash Commands</h2>
        {commands.length > 0 ? (
          <div className="celestial-panel overflow-hidden rounded-2xl border border-border/50">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border/50">
                  <th className="px-5 py-3 text-left font-semibold text-foreground">Command</th>
                  <th className="px-5 py-3 text-left font-semibold text-foreground">Syntax</th>
                  <th className="px-5 py-3 text-left font-semibold text-foreground">Description</th>
                </tr>
              </thead>
              <tbody>
                {commands.map((cmd) => (
                  <tr key={cmd.name} className="border-b border-border/30 last:border-0">
                    <td className="px-5 py-3 font-mono text-xs text-primary">{cmd.name}</td>
                    <td className="px-5 py-3 font-mono text-xs text-muted-foreground">{cmd.syntax}</td>
                    <td className="px-5 py-3 text-muted-foreground">{cmd.description}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">No slash commands registered.</p>
        )}
      </section>
    </div>
  );
}
