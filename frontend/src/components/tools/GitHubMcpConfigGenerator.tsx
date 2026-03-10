/**
 * GitHubMcpConfigGenerator — generates a ready-to-use GitHub.com MCP
 * configuration block from the user's active project tools plus built-in MCPs.
 *
 * Replaces the old GitHubToolsetSelector.  The output can be copied
 * into GitHub.com to configure remote Custom GitHub Agents.
 */

import { useCallback, useMemo, useState } from 'react';
import { Check, ClipboardCopy, Info } from 'lucide-react';
import type { McpToolConfig } from '@/types';
import { cn } from '@/lib/utils';
import { buildGitHubMcpConfig, BUILTIN_MCPS } from '@/lib/buildGitHubMcpConfig';

interface GitHubMcpConfigGeneratorProps {
  tools: McpToolConfig[];
}

export function GitHubMcpConfigGenerator({ tools }: GitHubMcpConfigGeneratorProps) {
  const [copied, setCopied] = useState(false);

  const { configJson, entries } = useMemo(() => buildGitHubMcpConfig(tools), [tools]);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(configJson);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback for older browsers / insecure contexts
      const textarea = document.createElement('textarea');
      textarea.value = configJson;
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }, [configJson]);

  const builtinServerKeys = new Set(BUILTIN_MCPS.map((b) => b.serverKey));
  const hasUserTools = entries.some((e) => !e.builtin);

  return (
    <section className="ritual-stage rounded-[1.55rem] p-4 sm:rounded-[1.85rem] sm:p-6">
      <div>
        <p className="text-[11px] uppercase tracking-[0.24em] text-primary/80">GitHub.com MCP</p>
        <h4 className="mt-2 text-[1.35rem] font-display font-medium leading-tight sm:text-[1.6rem]">
          MCP Configuration for GitHub Agents
        </h4>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
          Copy this configuration into GitHub.com to enable your remote Custom GitHub Agents with
          your active MCP servers.
        </p>
      </div>

      {/* Info callout */}
      <div className="mt-4 flex items-start gap-2 rounded-[1rem] border border-primary/20 bg-primary/5 px-4 py-3">
        <Info className="mt-0.5 h-4 w-4 shrink-0 text-primary/70" />
        <p className="text-xs leading-5 text-muted-foreground">
          This configuration is generated from your active project MCP tools and includes all
          Built-In MCPs. Paste it into your GitHub.com repository or organization settings to run
          remote Custom GitHub Agents.
        </p>
      </div>

      {/* MCP entry list with built-in badges */}
      <div className="mt-4">
        <p className="text-xs uppercase tracking-[0.22em] text-primary/80">Included MCP servers</p>
        {entries.length === 0 ? (
          <p className="mt-2 text-sm text-muted-foreground">No MCP servers configured.</p>
        ) : (
          <div className="mt-2 flex flex-wrap gap-2">
            {entries.map((entry) => (
              <span
                key={entry.key}
                className={cn(
                  'inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs',
                  entry.builtin
                    ? 'border-primary/40 bg-primary/10 text-foreground'
                    : 'border-border/70 bg-background/40 text-muted-foreground'
                )}
              >
                {entry.key}
                {builtinServerKeys.has(entry.key) && (
                  <span className="rounded-full bg-primary/20 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider text-primary">
                    Built-In
                  </span>
                )}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Empty state guidance */}
      {!hasUserTools && (
        <div className="mt-4 rounded-[1rem] border border-dashed border-border/70 bg-background/30 px-4 py-3 text-center">
          <p className="text-sm text-muted-foreground">
            No project MCP tools are active yet. Add tools from the preset gallery or upload a
            configuration to include them here. Built-In MCPs are always included.
          </p>
        </div>
      )}

      {/* Generated config code block */}
      <div className="mt-5 rounded-[1.2rem] border border-border/70 bg-background/40 p-4">
        <div className="flex items-center justify-between">
          <p className="text-xs uppercase tracking-[0.22em] text-primary/80">
            Generated configuration
          </p>
          <button
            type="button"
            onClick={() => {
              void handleCopy();
            }}
            className={cn(
              'inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition-colors',
              copied
                ? 'border-green-500/40 bg-green-500/10 text-green-600'
                : 'border-border/70 text-muted-foreground hover:border-primary/50 hover:bg-primary/10 hover:text-foreground'
            )}
          >
            {copied ? (
              <>
                <Check className="h-3 w-3" />
                Copied!
              </>
            ) : (
              <>
                <ClipboardCopy className="h-3 w-3" />
                Copy to Clipboard
              </>
            )}
          </button>
        </div>
        <pre className="mt-3 overflow-x-auto whitespace-pre-wrap break-words text-xs text-muted-foreground">
          {configJson}
        </pre>
      </div>
    </section>
  );
}
