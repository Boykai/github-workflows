/**
 * Sidebar — vertical navigation with Solune branding, route links, project selector, and recent interactions.
 */

import { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { NAV_ROUTES } from '@/constants';
import { PanelLeftClose, PanelLeft } from 'lucide-react';
import { ProjectSelector } from './ProjectSelector';
import type { RecentInteraction } from '@/types';
import type { Project } from '@/types';

interface SidebarProps {
  isCollapsed: boolean;
  onToggle: () => void;
  selectedProject?: { project_id: string; name: string; owner_login: string };
  recentInteractions: RecentInteraction[];
  projects: Project[];
  projectsLoading: boolean;
  onSelectProject: (projectId: string) => void;
}

export function Sidebar({
  isCollapsed,
  onToggle,
  selectedProject,
  recentInteractions,
  projects,
  projectsLoading,
  onSelectProject,
}: SidebarProps) {
  const [selectorOpen, setSelectorOpen] = useState(false);
  const navigate = useNavigate();
  return (
    <aside
      className={`celestial-panel relative flex h-full shrink-0 flex-col border-r border-border/70 transition-all duration-300 ${
        isCollapsed ? 'w-16' : 'w-60'
      }`}
    >
      <div className="pointer-events-none absolute inset-x-0 top-0 h-28 bg-[radial-gradient(circle_at_top,hsl(var(--glow)/0.16),transparent_70%)]" />
      <div className="pointer-events-none absolute right-4 top-24 h-24 w-24 rounded-full border border-border/20" />

      {/* Brand */}
      <div className="relative flex items-center justify-between border-b border-border/70 px-4 py-4">
        {!isCollapsed && (
          <div className="flex items-center gap-3">
            <span className="celestial-sigil flex h-10 w-10 items-center justify-center rounded-full border border-primary/30 bg-primary/10 text-lg text-primary golden-ring">
              <span className="relative z-10">☾</span>
            </span>
            <div>
              <span className="block text-lg font-display font-medium tracking-[0.08em] text-foreground">
                Solune
              </span>
              <span className="text-[10px] uppercase tracking-[0.28em] text-primary/80">
                Sun & Moon
              </span>
              <span className="mt-1 block text-[10px] uppercase tracking-[0.24em] text-muted-foreground/75">
                Guided project orbit
              </span>
            </div>
          </div>
        )}
        <button
          onClick={onToggle}
          className="rounded-full border border-transparent p-2 text-muted-foreground transition-all hover:border-border hover:bg-accent/70 hover:text-foreground"
          aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {isCollapsed ? <PanelLeft className="w-5 h-5" /> : <PanelLeftClose className="w-5 h-5" />}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex flex-1 flex-col gap-1 px-2 py-4">
        {NAV_ROUTES.map((route) => (
          <NavLink
            key={route.path}
            to={route.path}
            end={route.path === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-full px-3 py-2.5 text-sm font-medium transition-all ${
                isActive
                  ? 'bg-primary/12 text-primary shadow-sm ring-1 ring-primary/20'
                  : 'text-muted-foreground hover:bg-accent/45 hover:text-foreground'
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
                    className="flex w-full items-center gap-2 rounded-2xl px-3 py-2 text-left text-xs text-muted-foreground transition-colors hover:bg-accent/40 hover:text-foreground"
                    title={item.title}
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
              <p className="px-3 text-xs text-muted-foreground/60">No recent activity</p>
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
          className={`flex w-full items-center gap-2 rounded-full px-3 py-2.5 text-sm transition-colors hover:bg-accent/45 ${
            isCollapsed ? 'justify-center' : ''
          }`}
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
    </aside>
  );
}
