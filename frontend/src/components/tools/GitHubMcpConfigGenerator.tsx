/**
 * GitHubMcpConfigGenerator — generates a ready-to-use GitHub.com MCP
 * configuration block from the user's active project tools plus built-in MCPs.
 *
 * Replaces the old GitHubToolsetSelector.  The output can be copied
 * into GitHub.com to configure remote Custom GitHub Agents.
 */

import { Fragment, useCallback, useMemo, useState } from 'react';
import { Check, ClipboardCopy, Info, Sparkles } from 'lucide-react';
import type { McpToolConfig } from '@/types';
import { cn } from '@/lib/utils';
import { buildGitHubMcpConfig, BUILTIN_MCPS } from '@/lib/buildGitHubMcpConfig';

interface GitHubMcpConfigGeneratorProps {
  tools: McpToolConfig[];
}

function highlightJsonLine(line: string) {
  const segments: Array<{ value: string; className?: string }> = [];
  const tokenPattern =
    /("(?:\\.|[^"])*")(\s*:)?|\btrue\b|\bfalse\b|\bnull\b|-?\d+(?:\.\d+)?/g;
  let lastIndex = 0;

  for (const match of line.matchAll(tokenPattern)) {
    const matchText = match[0];
    const startIndex = match.index ?? 0;

    if (startIndex > lastIndex) {
      segments.push({ value: line.slice(lastIndex, startIndex) });
    }

    if (match[1]) {
      segments.push({
        value: match[1],
        className: match[2] ? 'text-sky-300' : 'text-emerald-300',
      });
      if (match[2]) {
        segments.push({ value: match[2] });
      }
    } else {
      segments.push({
        value: matchText,
        className:
          matchText === 'true' || matchText === 'false' || matchText === 'null'
            ? 'text-violet-300'
            : 'text-amber-300',
      });
    }

    lastIndex = startIndex + matchText.length;
  }

  if (lastIndex < line.length) {
    segments.push({ value: line.slice(lastIndex) });
  }

  return segments.map((segment, index) => (
    <span key={`${segment.value}-${index}`} className={segment.className}>
      {segment.value}
    </span>
  ));
}

export function GitHubMcpConfigGenerator({ tools }: GitHubMcpConfigGeneratorProps) {
  const [copied, setCopied] = useState(false);
  const activeTools = useMemo(() => tools.filter((tool) => tool.is_active), [tools]);

  const { configJson, entries } = useMemo(() => buildGitHubMcpConfig(activeTools), [activeTools]);
  const configLines = useMemo(() => configJson.split('\n'), [configJson]);

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

  const hasUserTools = entries.some((e) => !e.builtin);
  const activeCustomCount = entries.filter((entry) => !entry.builtin).length;

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

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <div className="moonwell rounded-[1.1rem] border border-border/60 p-3">
          <p className="text-[11px] uppercase tracking-[0.22em] text-primary/80">Active project MCPs</p>
          <p className="mt-2 text-2xl font-display text-foreground">{activeCustomCount}</p>
          <p className="mt-1 text-xs leading-5 text-muted-foreground">
            Included from the MCP tools currently active in this project.
          </p>
        </div>
        <div className="moonwell rounded-[1.1rem] border border-primary/20 bg-primary/5 p-3">
          <p className="text-[11px] uppercase tracking-[0.22em] text-primary/80">Always included</p>
          <p className="mt-2 text-2xl font-display text-foreground">{BUILTIN_MCPS.length}</p>
          <p className="mt-1 text-xs leading-5 text-muted-foreground">
            Built-In MCPs ship with every generated GitHub.com configuration.
          </p>
        </div>
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
                {entry.builtin && (
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
        <div className="mt-4 flex items-start gap-3 rounded-[1.1rem] border border-dashed border-border/70 bg-background/30 px-4 py-4">
          <div className="rounded-full border border-primary/25 bg-primary/10 p-2 text-primary">
            <Sparkles className="h-4 w-4" />
          </div>
          <div>
            <p className="text-sm font-medium text-foreground">No active project MCPs yet</p>
            <p className="mt-1 text-sm leading-6 text-muted-foreground">
              Activate an MCP from the presets gallery or upload your own configuration to include
              it here. Built-In MCPs stay ready by default, so this config is still valid for
              remote GitHub Agents while you finish wiring up project-specific tools.
            </p>
          </div>
        </div>
      )}

      {/* Generated config code block */}
      <div className="mt-5 rounded-[1.2rem] border border-border/70 bg-background/40 p-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.22em] text-primary/80">
              Generated configuration
            </p>
            <p className="mt-1 text-xs leading-5 text-muted-foreground">
              Syntax-highlighted JSON ready to copy into GitHub.com.
            </p>
          </div>
          <button
            type="button"
            onClick={() => {
              void handleCopy();
            }}
            aria-live="polite"
            className={cn(
              'inline-flex items-center gap-1.5 self-start rounded-full border px-3 py-1.5 text-xs font-medium transition-colors',
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
        <div
          className="mt-3 overflow-x-auto rounded-[1rem] border border-white/6 bg-slate-950/90 shadow-inner"
          data-testid="github-mcp-config-code"
        >
          <div className="min-w-max">
            {configLines.map((line, index) => (
              <div
                key={`${line}-${index}`}
                className="grid grid-cols-[auto_1fr] gap-4 border-b border-white/6 px-4 py-1.5 font-mono text-xs leading-6 last:border-b-0"
              >
                <span className="select-none text-[10px] text-slate-500">{index + 1}</span>
                <span className="whitespace-pre text-slate-100">
                  {line.length > 0 ? highlightJsonLine(line) : <Fragment>&nbsp;</Fragment>}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
