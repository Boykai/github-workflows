/**
 * AppPage — welcome/landing page with quick-access cards.
 */

import { useNavigate } from 'react-router-dom';
import { Kanban, GitBranch, Bot, ListChecks } from 'lucide-react';

const quickLinks = [
  { path: '/projects', label: 'Projects', description: 'View and manage your Kanban board', icon: Kanban },
  { path: '/pipeline', label: 'Agents Pipeline', description: 'Visualize your agent workflow', icon: GitBranch },
  { path: '/agents', label: 'Agents', description: 'Configure and manage agents', icon: Bot },
  { path: '/chores', label: 'Chores', description: 'Schedule and track chores', icon: ListChecks },
];

export function AppPage() {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center h-full gap-8 p-8">
      <div className="text-center max-w-lg">
        <h1 className="text-4xl font-bold tracking-tight mb-3">Welcome to Solune</h1>
        <p className="text-muted-foreground text-lg">
          Manage your GitHub Projects with AI-powered workflows
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full max-w-2xl">
        {quickLinks.map((link) => (
          <button
            key={link.path}
            onClick={() => navigate(link.path)}
            className="flex items-start gap-4 p-5 rounded-lg border border-border bg-card hover:bg-muted/50 hover:border-primary/30 transition-all text-left group"
          >
            <div className="p-2 rounded-md bg-primary/10 text-primary group-hover:bg-primary/20 transition-colors">
              <link.icon className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-semibold text-sm mb-1">{link.label}</h3>
              <p className="text-xs text-muted-foreground">{link.description}</p>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
