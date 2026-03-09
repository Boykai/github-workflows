import { useMemo, useState } from 'react';
import type { McpToolConfigCreate } from '@/types';

interface GitHubToolsetSelectorProps {
  onCreate: (data: McpToolConfigCreate) => Promise<unknown>;
  isSubmitting: boolean;
}

const TOOLSETS = [
  'repos',
  'issues',
  'users',
  'pull_requests',
  'code_security',
  'secret_protection',
  'actions',
  'web_search',
  'copilot_spaces',
] as const;

export function GitHubToolsetSelector({ onCreate, isSubmitting }: GitHubToolsetSelectorProps) {
  const [selectedToolsets, setSelectedToolsets] = useState<string[]>([
    'repos',
    'issues',
    'pull_requests',
    'actions',
  ]);
  const [fullAccess, setFullAccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const previewConfig = useMemo(() => {
    return JSON.stringify(
      {
        mcpServers: {
          github: {
            type: 'http',
            url: fullAccess
              ? 'https://api.githubcopilot.com/mcp/'
              : 'https://api.githubcopilot.com/mcp/readonly',
            tools: ['*'],
            headers: {
              'X-MCP-Toolsets': selectedToolsets.join(','),
            },
          },
        },
      },
      null,
      2
    );
  }, [fullAccess, selectedToolsets]);

  const toggleToolset = (toolset: string) => {
    setSelectedToolsets((current) =>
      current.includes(toolset) ? current.filter((item) => item !== toolset) : [...current, toolset]
    );
  };

  const handleCreate = async () => {
    if (selectedToolsets.length === 0) {
      setError('Select at least one GitHub toolset.');
      return;
    }
    setError(null);
    try {
      await onCreate({
        name: fullAccess ? 'GitHub MCP Server (Full Access)' : 'GitHub MCP Server',
        description: fullAccess
          ? 'GitHub MCP server with full access for custom agents.'
          : 'Read-only GitHub MCP server with selected toolsets for custom agents.',
        config_content: `${previewConfig}\n`,
        github_repo_target: '',
      });
    } catch (createError) {
      setError(
        createError instanceof Error ? createError.message : 'Failed to create GitHub MCP tool.'
      );
    }
  };

  return (
    <section className="ritual-stage rounded-[1.55rem] p-4 sm:rounded-[1.85rem] sm:p-6">
      <div>
        <p className="text-[11px] uppercase tracking-[0.24em] text-primary/80">GitHub MCP</p>
        <h4 className="mt-2 text-[1.35rem] font-display font-medium leading-tight sm:text-[1.6rem]">
          Configure GitHub toolsets
        </h4>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
          Build a GitHub MCP server config from current GitHub documentation, including the
          `X-MCP-Toolsets` header used by Copilot coding agents.
        </p>
      </div>

      <label className="mt-5 flex items-center gap-3 text-sm text-foreground">
        <input
          type="checkbox"
          checked={fullAccess}
          onChange={(event) => setFullAccess(event.target.checked)}
        />
        Use full-access endpoint instead of read-only
      </label>

      <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {TOOLSETS.map((toolset) => {
          const selected = selectedToolsets.includes(toolset);
          return (
            <button
              key={toolset}
              type="button"
              onClick={() => toggleToolset(toolset)}
              aria-pressed={selected}
              className={`rounded-[1rem] border px-4 py-3 text-left text-sm transition-colors ${selected ? 'border-primary/60 bg-primary/10 text-foreground' : 'border-border/70 bg-background/40 text-muted-foreground'}`}
            >
              {toolset}
            </button>
          );
        })}
      </div>

      <div className="mt-5 rounded-[1.2rem] border border-border/70 bg-background/40 p-4">
        <p className="text-xs uppercase tracking-[0.22em] text-primary/80">Generated config</p>
        <pre className="mt-3 overflow-x-auto whitespace-pre-wrap break-words text-xs text-muted-foreground">
          {previewConfig}
        </pre>
      </div>

      {error && <p className="mt-3 text-sm text-destructive">{error}</p>}

      <button
        type="button"
        onClick={handleCreate}
        disabled={isSubmitting}
        className="mt-4 rounded-full border border-border/70 px-4 py-2 text-sm font-medium text-foreground transition-colors hover:border-primary/50 hover:bg-primary/10 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isSubmitting ? 'Creating…' : 'Create GitHub MCP tool'}
      </button>
    </section>
  );
}
