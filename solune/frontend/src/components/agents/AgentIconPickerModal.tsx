import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { X } from '@/lib/icons';
import { isCelestialIconName, type CelestialIconName } from '@/components/common/agentIcons';
import { AgentIconCatalog } from './AgentIconCatalog';
import { useScrollLock } from '@/hooks/useScrollLock';

interface AgentIconPickerModalProps {
  isOpen: boolean;
  agentName: string;
  slug?: string | null;
  currentIconName?: string | null;
  isSaving?: boolean;
  onClose: () => void;
  onSave: (iconName: CelestialIconName | null) => Promise<void> | void;
}

export function AgentIconPickerModal({
  isOpen,
  agentName,
  slug,
  currentIconName,
  isSaving = false,
  onClose,
  onSave,
}: AgentIconPickerModalProps) {
  const [selectedIconName, setSelectedIconName] = useState<CelestialIconName | null>(
    isCelestialIconName(currentIconName) ? currentIconName : null
  );

  const [prevCurrentIconName, setPrevCurrentIconName] = useState(currentIconName);
  const [prevIsOpen, setPrevIsOpen] = useState(isOpen);
  if (currentIconName !== prevCurrentIconName || isOpen !== prevIsOpen) {
    setPrevCurrentIconName(currentIconName);
    setPrevIsOpen(isOpen);
    setSelectedIconName(isCelestialIconName(currentIconName) ? currentIconName : null);
  }

  useScrollLock(isOpen);

  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return createPortal(
    <div
      className="fixed inset-0 z-[140] bg-black/55"
      role="presentation"
      onClick={onClose}
    >
      <div className="flex min-h-full items-start justify-center overflow-y-auto p-4 sm:p-6">
        {/* eslint-disable-next-line jsx-a11y/click-events-have-key-events, jsx-a11y/no-noninteractive-element-interactions */}
        <div
          className="celestial-panel celestial-fade-in relative my-4 flex max-h-[min(92vh,56rem)] w-full max-w-4xl flex-col overflow-hidden rounded-[1.5rem] border border-border/80 p-6 shadow-xl"
          role="dialog"
          aria-modal="true"
          aria-label={`Choose an icon for ${agentName}`}
          onClick={(event) => event.stopPropagation()}
        >
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-[11px] uppercase tracking-[0.24em] text-primary/80">
                Celestial Icon Catalog
              </p>
              <h3 className="mt-2 text-2xl font-display font-medium">
                Choose an icon for {agentName}
              </h3>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">
                Pick a specific celestial icon, or leave it on automatic to use the diversified
                slug-based mapping.
              </p>
            </div>
            <button
              type="button"
              className="solar-action flex h-10 w-10 items-center justify-center rounded-full"
              onClick={onClose}
              aria-label="Close icon picker"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="mt-5 min-h-0 flex-1 overflow-y-auto pr-1">
            <AgentIconCatalog
              slug={slug}
              agentName={agentName}
              selectedIconName={selectedIconName}
              onSelect={setSelectedIconName}
            />
          </div>

          <div className="mt-5 flex shrink-0 justify-end gap-2">
            <button
              type="button"
              className="celestial-focus solar-action rounded-full px-4 py-2 text-sm font-medium"
              onClick={onClose}
            >
              Cancel
            </button>
            <button
              type="button"
              className="celestial-focus rounded-full bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              disabled={isSaving}
              onClick={() => void onSave(selectedIconName)}
            >
              {isSaving ? 'Saving…' : 'Save Icon'}
            </button>
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
}
