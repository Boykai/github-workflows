/**
 * ToolsPage — MCP tool management page mirroring AgentsPage layout.
 */

import { useAuth } from '@/hooks/useAuth';
import { useProjects } from '@/hooks/useProjects';
import { useProjectBoard } from '@/hooks/useProjectBoard';
import { ToolsPanel } from '@/components/tools/ToolsPanel';
import { CelestialCatalogHero } from '@/components/common/CelestialCatalogHero';
import { Button } from '@/components/ui/button';

export function ToolsPage() {
  const { user } = useAuth();
  const { selectedProject } = useProjects(user?.selected_project_id);
  const projectId = selectedProject?.project_id ?? null;

  const { boardData } = useProjectBoard({ selectedProjectId: projectId });
  const repo = boardData?.columns.flatMap(c => c.items).find(i => i.repository)?.repository;

  return (
    <div className="flex h-full flex-col gap-5 overflow-auto rounded-[1.5rem] border border-border/70 bg-background/42 p-4 backdrop-blur-sm sm:gap-6 sm:rounded-[1.75rem] sm:p-6">
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
              <a href="https://docs.github.com/en/copilot/concepts/context/mcp" target="_blank" rel="noopener noreferrer">
                MCP docs
              </a>
            </Button>
            <Button variant="outline" size="lg" asChild>
              <a href="https://github.com/mcp" target="_blank" rel="noopener noreferrer" aria-label="Discover MCP integrations on GitHub">
                Discover
              </a>
            </Button>
          </>
        }
      />

      {/* No project selected */}
      {!projectId && (
        <div className="celestial-panel flex flex-1 flex-col items-center justify-center gap-4 rounded-[1.4rem] border border-dashed border-border/80 bg-background/26 p-8 text-center">
          <div className="text-4xl mb-2">🔧</div>
          <h3 className="text-xl font-semibold">Select a project</h3>
          <p className="text-muted-foreground">Choose a project from the sidebar to manage its MCP tools</p>
        </div>
      )}

      {projectId && (
        <div id="tools-catalog" className="min-w-0 scroll-mt-6">
          <ToolsPanel projectId={projectId} />
        </div>
      )}
    </div>
  );
}
