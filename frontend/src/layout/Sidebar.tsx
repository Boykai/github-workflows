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
      className={`flex flex-col h-full bg-card border-r border-border transition-all duration-200 shrink-0 ${
        isCollapsed ? 'w-16' : 'w-60'
      }`}
    >
      {/* Brand */}
      <div className="flex items-center justify-between px-4 py-4 border-b border-border">
        {!isCollapsed && (
          <span className="text-lg font-display font-bold tracking-tight text-primary">
            Solune
          </span>
        )}
        <button
          onClick={onToggle}
          className="p-1.5 rounded-md hover:bg-muted transition-colors text-muted-foreground"
          aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {isCollapsed ? <PanelLeft className="w-5 h-5" /> : <PanelLeftClose className="w-5 h-5" />}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex flex-col gap-1 px-2 py-3 flex-1">
        {NAV_ROUTES.map((route) => (
          <NavLink
            key={route.path}
            to={route.path}
            end={route.path === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-primary/10 text-primary border-l-3 border-primary'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground'
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
            <p className="px-3 mb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Recent Interactions
            </p>
            {recentInteractions.length > 0 ? (
              <div className="flex flex-col gap-0.5">
                {recentInteractions.slice(0, 8).map((item) => (
                  <button
                    key={item.item_id}
                    className="flex items-center gap-2 px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground hover:bg-muted rounded-md transition-colors text-left w-full"
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
      <div className="border-t border-border px-2 py-3 relative">
        <button
          onClick={() => setSelectorOpen(!selectorOpen)}
          className={`flex items-center gap-2 w-full px-3 py-2 rounded-md text-sm hover:bg-muted transition-colors ${
            isCollapsed ? 'justify-center' : ''
          }`}
          title={selectedProject ? `${selectedProject.owner_login}/${selectedProject.name}` : 'Select project'}
        >
          <span className="w-5 h-5 rounded-md bg-primary/20 text-primary flex items-center justify-center text-xs font-bold shrink-0">
            {selectedProject ? selectedProject.name.charAt(0).toUpperCase() : '?'}
          </span>
          {!isCollapsed && (
            <span className="truncate text-foreground">
              {selectedProject ? selectedProject.name : 'Select project'}
            </span>
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
