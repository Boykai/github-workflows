/**
 * ToolsEditor — interactive ordered list of tools for the agent editor.
 *
 * Allows adding, removing, and reordering tools via arrow buttons.
 * Every change fires onToolsChange with the updated array.
 */

import { useEffect, useState } from 'react';
import { ChevronUp, ChevronDown, X, Plus } from '@/lib/icons';
import { ToolSelectorModal } from '@/components/tools/ToolSelectorModal';
import { Tooltip } from '@/components/ui/tooltip';

interface ToolsEditorProps {
  tools: string[];
  onToolsChange: (tools: string[]) => void;
  error?: string;
  projectId: string;
  onSelectorOpenChange?: (open: boolean) => void;
}

export function ToolsEditor({
  tools,
  onToolsChange,
  error,
  projectId,
  onSelectorOpenChange,
}: ToolsEditorProps) {
  const [showSelector, setShowSelector] = useState(false);

  useEffect(() => {
    onSelectorOpenChange?.(showSelector);
  }, [onSelectorOpenChange, showSelector]);

  const moveUp = (index: number) => {
    if (index <= 0) return;
    const next = [...tools];
    [next[index - 1], next[index]] = [next[index], next[index - 1]];
    onToolsChange(next);
  };

  const moveDown = (index: number) => {
    if (index >= tools.length - 1) return;
    const next = [...tools];
    [next[index], next[index + 1]] = [next[index + 1], next[index]];
    onToolsChange(next);
  };

  const remove = (index: number) => {
    onToolsChange(tools.filter((_, i) => i !== index));
  };

  const handleAddConfirm = (selectedIds: string[]) => {
    // Only add tools not already present
    const newTools = selectedIds.filter((id) => !tools.includes(id));
    if (newTools.length > 0) {
      onToolsChange([...tools, ...newTools]);
    }
    setShowSelector(false);
  };

  return (
    <div>
      {tools.length === 0 ? (
        <p className="text-sm text-muted-foreground py-2">
          No tools assigned. Click &quot;Add Tools&quot; to get started.
        </p>
      ) : (
        <ul className="flex flex-col gap-1">
          {tools.map((tool, index) => (
            <li
              key={tool}
              className="flex items-center gap-1.5 rounded-md border border-border/60 bg-background/50 px-2 py-1.5"
            >
              <span className="flex-1 truncate text-sm">{tool}</span>
              <Tooltip contentKey="agents.tools.moveUp">
                <button
                  type="button"
                  className="celestial-focus p-0.5 text-muted-foreground hover:text-foreground disabled:opacity-30"
                  onClick={() => moveUp(index)}
                  disabled={index === 0}
                  aria-label={`Move ${tool} up`}
                >
                  <ChevronUp className="h-4 w-4" />
                </button>
              </Tooltip>
              <Tooltip contentKey="agents.tools.moveDown">
                <button
                  type="button"
                  className="celestial-focus p-0.5 text-muted-foreground hover:text-foreground disabled:opacity-30"
                  onClick={() => moveDown(index)}
                  disabled={index === tools.length - 1}
                  aria-label={`Move ${tool} down`}
                >
                  <ChevronDown className="h-4 w-4" />
                </button>
              </Tooltip>
              <Tooltip contentKey="agents.tools.remove">
                <button
                  type="button"
                  className="celestial-focus p-0.5 text-muted-foreground hover:text-destructive"
                  onClick={() => remove(index)}
                  aria-label={`Remove ${tool}`}
                >
                  <X className="h-4 w-4" />
                </button>
              </Tooltip>
            </li>
          ))}
        </ul>
      )}

      {error && <p className="mt-1 text-sm text-destructive">{error}</p>}

      <button
        type="button"
        className="celestial-focus mt-2 inline-flex items-center gap-1.5 rounded-md border border-border/60 px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground hover:bg-muted/50"
        onClick={() => setShowSelector(true)}
      >
        <Plus className="h-4 w-4" />
        Add Tools
      </button>

      <ToolSelectorModal
        isOpen={showSelector}
        onClose={() => setShowSelector(false)}
        onConfirm={handleAddConfirm}
        initialSelectedIds={tools}
        projectId={projectId}
      />
    </div>
  );
}
