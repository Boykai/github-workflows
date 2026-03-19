/**
 * ToolsPage — MCP tool management page mirroring AgentsPage layout.
 */

import { useAuth } from '@/hooks/useAuth';
import { useProjects } from '@/hooks/useProjects';
import { useProjectBoard } from '@/hooks/useProjectBoard';
import { useToolsList } from '@/hooks/useTools';
import { ToolsPanel } from '@/components/tools/ToolsPanel';
import { CelestialCatalogHero } from '@/components/common/CelestialCatalogHero';
import { ProjectSelectionEmptyState } from '@/components/common/ProjectSelectionEmptyState';
import { Skeleton } from '@/components/ui/skeleton';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import { Button } from '@/components/ui/button';

export function ToolsPage() {
  const { user } = useAuth();
  const {
    selectedProject,
    projects,
    isLoading: projectsLoading,
    selectProject,
  } = useProjects(user?.selected_project_id);
  const projectId = selectedProject?.project_id ?? null;

  const { boardData } = useProjectBoard({ selectedProjectId: projectId });
  const { isLoading: toolsLoading } = useToolsList(projectId);
  const repo = boardData?.columns.flatMap((c) => c.items).find((i) => i.repository)?.repository;

  return (
    <div className="celestial-fade-in flex h-full flex-col gap-5 overflow-auto rounded-[1.5rem] border border-border/70 bg-background/42 p-4 backdrop-blur-sm sm:gap-6 sm:rounded-[1.75rem] sm:p-6">
      <CelestialCatalogHero
        eyebrow="Tool Forge"
        title="Equip your agents with MCP tools."
        description="Upload and manage MCP configurations that sync to your repository and can be embedded into GitHub Custom Agent definitions. Assign tools to agents during creation for enhanced capabilities."
        badge={repo ? repo.name : 'Awaiting repository'}
        note="Uploaded MCP configs are stored in both .copilot/mcp.json and .vscode/mcp.json, then embedded into assigned .github/agents/*.agent.md files when you save an agent."
        stats={[
          { label: 'Repository', value: repo ? repo.name : 'Unlinked' },
          { label: 'Project', value: selectedProject?.name ?? 'Unselected' },
        ]}
        actions={
          <>
            <Button variant="default" size="lg" asChild>
              <a href="#tools-catalog">Browse tools</a>
            </Button>
            <Button variant="outline" size="lg" asChild>
              <a
                href="https://docs.github.com/en/copilot/concepts/context/mcp"
                target="_blank"
                rel="noopener noreferrer"
              >
                MCP docs
              </a>
            </Button>
            <Button variant="outline" size="lg" asChild>
              <a
                href="https://github.com/mcp"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="Discover MCP integrations on GitHub"
              >
                Discover
              </a>
            </Button>
          </>
        }
      />

      {/* No project selected */}
      {!projectId && (
        <ProjectSelectionEmptyState
          projects={projects}
          isLoading={projectsLoading}
          selectedProjectId={projectId}
          onSelectProject={selectProject}
          description="Choose a GitHub Project to manage its MCP tools, repository-linked configs, and agent tool attachments."
        />
      )}

      {projectId && (
        <ErrorBoundary>
          <div id="tools-catalog" className="min-w-0 scroll-mt-6">
            {toolsLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 6 }).map((_, i) => (
                  <div key={i} className="celestial-panel flex items-start gap-3 rounded-[1.25rem] border border-border/75 p-4">
                    <Skeleton variant="shimmer" className="h-10 w-10 rounded-lg" />
                    <div className="flex-1 space-y-2">
                      <Skeleton variant="shimmer" className="h-4 w-40" />
                      <Skeleton variant="shimmer" className="h-3 w-64" />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <ToolsPanel projectId={projectId} />
            )}
          </div>
        </ErrorBoundary>
      )}
    </div>
  );
}
