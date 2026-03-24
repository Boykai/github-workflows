/**
 * Sidebar — vertical navigation with Solune branding, route links, project selector, and recent interactions.
 */

import { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { NAV_ROUTES } from '@/constants';
import { Moon, PanelLeftClose, PanelLeft, Sun } from '@/lib/icons';
import { ProjectSelector } from './ProjectSelector';
import { Tooltip } from '@/components/ui/tooltip';
import { statusColorToCSS } from '@/components/board/colorUtils';
import type { RecentInteraction } from '@/types';
import type { Project } from '@/types';
import { cn } from '@/lib/utils';

interface SidebarProps {
  isCollapsed: boolean;
  onToggle: () => void;
  isDarkMode: boolean;
  onToggleTheme: () => void;
  isMobile?: boolean;
  selectedProject?: { project_id: string; name: string; owner_login: string };
  recentInteractions: RecentInteraction[];
  projects: Project[];
  projectsLoading: boolean;
  onSelectProject: (projectId: string) => void;
}

export function Sidebar({
  isCollapsed,
  onToggle,
  isDarkMode,
  onToggleTheme,
  isMobile = false,
  selectedProject,
  recentInteractions,
  projects,
  projectsLoading,
  onSelectProject,
}: SidebarProps) {
  const [selectorOpen, setSelectorOpen] = useState(false);
  const navigate = useNavigate();

  // On mobile when expanded, render as overlay with backdrop
  if (isMobile && !isCollapsed) {
    return (
      <>
        {/* Backdrop */}
        <div
          className="fixed inset-0 z-40 bg-black/50"
          onClick={onToggle}
          role="presentation"
        />
        <aside
          className="fixed inset-y-0 left-0 z-50 flex w-60 flex-col border-r border-border/70 bg-background shadow-xl"
        >
          {renderSidebarContent()}
        </aside>
      </>
    );
  }

  return (
    <aside
      className={cn('celestial-panel relative flex h-full shrink-0 flex-col border-r border-border/70 transition-all duration-300', isCollapsed ? 'w-16' : 'w-60')}
    >
      {renderSidebarContent()}
    </aside>
  );

  function renderSidebarContent() {
    return (
      <>
      <div className="pointer-events-none absolute inset-x-0 top-0 h-32 bg-[radial-gradient(circle_at_top,hsl(var(--glow)/0.22),transparent_70%)]" />
      <div className="pointer-events-none absolute left-4 top-6 h-10 w-10 rounded-full bg-primary/10 blur-xl celestial-pulse-glow" />
      <div className="pointer-events-none absolute right-4 top-24 h-24 w-24 rounded-full border border-border/20 celestial-orbit-spin" />

      {/* Brand */}
      <div className={cn('relative flex border-b border-border/70 px-4 py-4', isCollapsed ? 'flex-col items-center gap-3' : 'items-center justify-between')}>
        <div className={cn('flex items-center gap-3', isCollapsed && 'justify-center')}>
          <Tooltip contentKey="settings.theme.toggle">
            <button
              type="button"
              onClick={onToggleTheme}
              data-tour-step="theme-toggle"
              className={cn('celestial-sigil golden-ring flex h-10 w-10 items-center justify-center rounded-full border border-primary/30 bg-primary/10 shadow-[0_0_30px_hsl(var(--glow)/0.16)] transition-all hover:scale-[1.03] hover:border-primary/45 hover:bg-primary/14', isDarkMode ? 'text-primary' : 'text-gold')}
              aria-label={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
            >
              {isDarkMode ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
            </button>
          </Tooltip>
          {!isCollapsed && (
            <div>
              <span className="block text-lg font-display font-medium tracking-[0.08em] text-foreground">
                Solune
              </span>
              <span className="text-[10px] uppercase tracking-[0.28em] text-primary/85">
                Sun & Moon
              </span>
              <span className="mt-1 block text-[10px] uppercase tracking-[0.24em] text-muted-foreground/75">
                Guided solar orbit
              </span>
            </div>
          )}
        </div>
        <Tooltip contentKey="nav.sidebar.toggle">
          <button
            onClick={onToggle}
            className="celestial-focus rounded-full border border-transparent p-2 text-muted-foreground transition-all hover:border-border hover:bg-primary/10 hover:text-foreground focus-visible:outline-none"
            aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {isCollapsed ? <PanelLeft className="w-5 h-5" /> : <PanelLeftClose className="w-5 h-5" />}
          </button>
        </Tooltip>
      </div>

      {/* Navigation */}
      <nav data-tour-step="sidebar-nav" className="flex flex-1 flex-col gap-1 px-2 py-4">
        {NAV_ROUTES.map((route) => (
          <NavLink
            key={route.path}
            to={route.path}
            end={route.path === '/'}
            onClick={isMobile ? onToggle : undefined}
            data-tour-step={{
              '/projects': 'projects-link',
              '/pipeline': 'pipeline-link',
              '/agents': 'agents-link',
              '/tools': 'tools-link',
              '/chores': 'chores-link',
              '/settings': 'settings-link',
              '/apps': 'apps-link',
              '/activity': 'activity-link',
            }[route.path] ?? undefined}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-full px-3 py-2.5 text-sm font-medium transition-all ${
                isActive
                  ? 'bg-primary/14 text-primary shadow-sm ring-1 ring-primary/20'
                  : 'text-muted-foreground hover:bg-accent/14 hover:text-foreground'
              } ${isCollapsed ? 'justify-center' : ''}`
            }
            title={isCollapsed ? route.label : undefined}
          >
            <route.icon className="w-5 h-5 shrink-0" />
            {!isCollapsed && <span>{route.label}</span>}
          </NavLink>
        ))}

        {/* Recent Interactions section */}
        {!isCollapsed && (
          <div className="mt-6">
            <p className="mb-3 px-3 text-xs font-semibold uppercase tracking-[0.24em] text-primary/70">
              Recent Interactions
            </p>
            {recentInteractions.length > 0 ? (
              <div className="flex flex-col gap-0.5">
                {recentInteractions.slice(0, 8).map((item) => (
                  <button
                    key={item.item_id}
                    className="flex w-full items-center gap-2 rounded-2xl border-l-2 px-3 py-2 text-left text-xs text-muted-foreground transition-colors hover:bg-accent/14 hover:text-foreground"
                    style={{ borderLeftColor: statusColorToCSS(item.statusColor) }}
                    title={`${item.title} — ${item.status}`}
                    onClick={() => navigate('/projects')}
                  >
                    {item.number != null && (
                      <span className="text-muted-foreground/70">#{item.number}</span>
                    )}
                    <span className="truncate">{item.title}</span>
                  </button>
                ))}
              </div>
            ) : (
              <p className="px-3 text-xs text-muted-foreground/60">No recent parent issues</p>
            )}
          </div>
        )}
      </nav>

      {/* Project Selector (bottom) */}
      <div className="relative border-t border-border/70 px-2 py-3">
        {!isCollapsed && (
          <div className="pointer-events-none absolute inset-x-3 top-0 h-px bg-gradient-to-r from-transparent via-primary/35 to-transparent" />
        )}
        <button
          onClick={() => setSelectorOpen(!selectorOpen)}
          data-tour-step="project-selector"
          className={cn('flex w-full items-center gap-2 rounded-full px-3 py-2.5 text-sm transition-colors hover:bg-accent/14', isCollapsed ? 'justify-center' : '')}
          title={
            selectedProject
              ? `${selectedProject.owner_login}/${selectedProject.name}`
              : 'Select project'
          }
        >
          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/15 text-xs font-bold text-primary">
            {selectedProject ? selectedProject.name.charAt(0).toUpperCase() : '?'}
          </span>
          {!isCollapsed && (
            <div className="min-w-0 text-left">
              <span className="block truncate text-sm text-foreground">
                {selectedProject ? selectedProject.name : 'Select project'}
              </span>
              <span className="block truncate text-[10px] uppercase tracking-[0.22em] text-muted-foreground/80">
                {selectedProject ? selectedProject.owner_login : 'Moonboard'}
              </span>
            </div>
          )}
        </button>
        {!isCollapsed && (
          <ProjectSelector
            isOpen={selectorOpen}
            onClose={() => setSelectorOpen(false)}
            projects={projects}
            selectedProjectId={selectedProject?.project_id ?? null}
            isLoading={projectsLoading}
            onSelectProject={onSelectProject}
          />
        )}
      </div>
      </>
    );
  }
}
