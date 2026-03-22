import { forwardRef, useCallback, useEffect, useImperativeHandle, useMemo, useState } from 'react';
import { Info } from '@/lib/icons';
import type { AgentConfig } from '@/services/api';
import { useUpdateAgent } from '@/hooks/useAgents';
import { AgentIconCatalog } from '@/components/agents/AgentIconCatalog';
import { isCelestialIconName, type CelestialIconName } from '@/components/common/agentIcons';
import { EntityHistoryPanel } from '@/components/activity/EntityHistoryPanel';
import { ToolsEditor } from './ToolsEditor';
import { Button } from '@/components/ui/button';

const MAX_PROMPT_LENGTH = 30000;

export interface AgentInlineEditorHandle {
  save: () => Promise<boolean>;
  discard: () => void;
}

interface AgentInlineEditorProps {
  agent: AgentConfig;
  projectId: string;
  onDirtyChange: (isDirty: boolean) => void;
  onCancel: () => void;
  onSaved: (prUrl: string, agentName: string) => void;
}

export const AgentInlineEditor = forwardRef<AgentInlineEditorHandle, AgentInlineEditorProps>(
  function AgentInlineEditor({ agent, projectId, onDirtyChange, onCancel, onSaved }, ref) {
    const updateMutation = useUpdateAgent(projectId);
    const [name, setName] = useState(agent.name);
    const [systemPrompt, setSystemPrompt] = useState(agent.system_prompt || '');
    const [selectedToolIds, setSelectedToolIds] = useState<string[]>([...(agent.tools ?? [])]);
    const [selectedIconName, setSelectedIconName] = useState<CelestialIconName | null>(
      isCelestialIconName(agent.icon_name) ? agent.icon_name : null
    );
    const [error, setError] = useState<string | null>(null);
    const [toolsError, setToolsError] = useState<string | null>(null);

    const snapshot = useMemo(
      () => ({
        name: agent.name,
        systemPrompt: agent.system_prompt || '',
        tools: [...(agent.tools ?? [])],
        iconName: isCelestialIconName(agent.icon_name) ? agent.icon_name : null,
      }),
      [agent]
    );

    const [prevAgentId, setPrevAgentId] = useState(agent.id);
    if (agent.id !== prevAgentId) {
      setPrevAgentId(agent.id);
      setName(agent.name);
      setSystemPrompt(agent.system_prompt || '');
      setSelectedToolIds([...(agent.tools ?? [])]);
      setSelectedIconName(isCelestialIconName(agent.icon_name) ? agent.icon_name : null);
      setError(null);
      setToolsError(null);
    }

    const isDirty = useMemo(() => {
      if (name !== snapshot.name) return true;
      if (systemPrompt !== snapshot.systemPrompt) return true;
      if (selectedIconName !== snapshot.iconName) return true;
      if (selectedToolIds.length !== snapshot.tools.length) return true;
      return selectedToolIds.some((id, index) => id !== snapshot.tools[index]);
    }, [name, selectedIconName, selectedToolIds, snapshot, systemPrompt]);

    useEffect(() => {
      let active = true;
      queueMicrotask(() => {
        if (active) onDirtyChange(isDirty);
      });
      return () => { active = false; };
    }, [isDirty, onDirtyChange]);

    // Clear tools error when tools are selected (render-time adjustment)
    if (selectedToolIds.length > 0 && toolsError) {
      setToolsError(null);
    }

    const handleDiscard = useCallback(() => {
      setName(snapshot.name);
      setSystemPrompt(snapshot.systemPrompt);
      setSelectedToolIds([...snapshot.tools]);
      setSelectedIconName(snapshot.iconName);
      setError(null);
      setToolsError(null);
      onDirtyChange(false);
    }, [onDirtyChange, snapshot]);

    const handleSave = useCallback(async () => {
      setError(null);
      setToolsError(null);

      const trimmedName = name.trim();
      const trimmedPrompt = systemPrompt.trim();

      if (!trimmedName) {
        setError('Name is required');
        return false;
      }
      if (trimmedName.length > 100) {
        setError('Name must be 100 characters or fewer');
        return false;
      }
      if (!trimmedPrompt) {
        setError('System prompt is required');
        return false;
      }
      if (trimmedPrompt.length > MAX_PROMPT_LENGTH) {
        setError(`System prompt must be ${MAX_PROMPT_LENGTH.toLocaleString()} characters or fewer`);
        return false;
      }
      try {
        const result = await updateMutation.mutateAsync({
          agentId: agent.id,
          data: {
            name: trimmedName,
            system_prompt: trimmedPrompt,
            tools: selectedToolIds,
            ...(selectedIconName !== null || agent.icon_name != null
              ? { icon_name: selectedIconName }
              : {}),
          },
        });
        onDirtyChange(false);
        onSaved(result.pr_url, trimmedName);
        return true;
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Failed to save agent');
        return false;
      }
    }, [
      agent.id,
      agent.icon_name,
      name,
      onDirtyChange,
      onSaved,
      selectedIconName,
      selectedToolIds,
      systemPrompt,
      updateMutation,
    ]);

    useImperativeHandle(
      ref,
      () => ({
        save: handleSave,
        discard: handleDiscard,
      }),
      [handleDiscard, handleSave]
    );

    return (
      <>
      <section className="ritual-stage rounded-[1.55rem] p-4 sm:rounded-[1.85rem] sm:p-6">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="text-[11px] uppercase tracking-[0.24em] text-primary/80">
              Editing agent definition
            </p>
            <h4 className="mt-2 text-[1.35rem] font-display font-medium leading-tight sm:text-[1.6rem]">
              {agent.name}
            </h4>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
              Update the prompt, tools, or icon directly on the page. Saving opens a pull request
              with the agent file changes.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {isDirty && (
              <span className="solar-chip-warning rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em]">
                Unsaved changes
              </span>
            )}
            <Button variant="outline" onClick={onCancel} disabled={updateMutation.isPending}>
              Close Editor
            </Button>
            <Button
              variant="outline"
              onClick={handleDiscard}
              disabled={!isDirty || updateMutation.isPending}
            >
              Discard
            </Button>
            <Button onClick={() => void handleSave()} disabled={updateMutation.isPending}>
              {updateMutation.isPending ? 'Saving…' : 'Save Changes'}
            </Button>
          </div>
        </div>

        <div className="mt-6 grid gap-5 xl:grid-cols-[minmax(0,1.2fr)_minmax(20rem,0.8fr)]">
          <div className="flex flex-col gap-5">
            <div>
              <label htmlFor="inline-agent-name" className="mb-1.5 block text-sm font-medium">
                Name
              </label>
              <input
                id="inline-agent-name"
                type="text"
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="e.g., Security Reviewer"
                className="celestial-focus w-full rounded-xl border border-border bg-background/72 px-3 py-2.5 text-sm outline-none transition-colors focus:border-primary/40"
                maxLength={100}
              />
            </div>

            <div>
              <label
                htmlFor="inline-agent-system-prompt"
                className="mb-1.5 block text-sm font-medium"
              >
                System Prompt
                <span className="ml-2 font-normal text-muted-foreground">
                  {systemPrompt.length.toLocaleString()} / {MAX_PROMPT_LENGTH.toLocaleString()}
                </span>
              </label>
              <textarea
                id="inline-agent-system-prompt"
                value={systemPrompt}
                onChange={(event) => setSystemPrompt(event.target.value)}
                placeholder="Detailed instructions for the agent's behavior..."
                className="celestial-focus min-h-[280px] w-full resize-y rounded-[1.1rem] border border-border bg-background/72 px-3 py-3 font-mono text-xs leading-relaxed outline-none transition-colors focus:border-primary/40"
                maxLength={MAX_PROMPT_LENGTH}
              />
            </div>

            <div>
              <span className="mb-1 block text-sm font-medium">MCP Tools</span>
              <ToolsEditor
                tools={selectedToolIds}
                onToolsChange={setSelectedToolIds}
                error={toolsError ?? undefined}
                projectId={projectId}
              />
              <div className="mt-2 flex items-start gap-1.5 rounded-lg border border-emerald-500/20 bg-emerald-500/5 px-3 py-2">
                <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-600 dark:text-emerald-400" />
                <p className="text-[11px] leading-4 text-muted-foreground">
                  This agent enforces{' '}
                  <code className="rounded bg-emerald-500/10 px-1 py-0.5 font-mono text-[10px] font-medium text-emerald-700 dark:text-emerald-300">
                    tools: [&quot;*&quot;]
                  </code>{' '}
                  — all activated and built-in MCPs are available.
                </p>
              </div>
            </div>

            {updateMutation.isPending && (
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <div className="h-3 w-3 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                Creating a pull request with the updated agent files...
              </div>
            )}

            {error && (
              <div className="rounded-[1rem] bg-destructive/10 p-3 text-sm text-destructive">
                {error}
              </div>
            )}
          </div>

          <div>
            <span className="mb-2 block text-sm font-medium">Celestial Icon</span>
            <p className="mb-3 text-xs text-muted-foreground">
              Choose a specific celestial icon, or leave it on automatic to use the diversified
              slug-based mapping for this agent.
            </p>
            <AgentIconCatalog
              slug={agent.slug}
              agentName={name || agent.name}
              selectedIconName={selectedIconName}
              onSelect={setSelectedIconName}
            />
          </div>
        </div>
      </section>

      <EntityHistoryPanel projectId={projectId} entityType="agent" entityId={agent.slug} />
    </>
    );
  }
);
