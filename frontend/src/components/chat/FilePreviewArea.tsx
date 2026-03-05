/**
 * File preview area component.
 * Container rendering list of FilePreviewItem components with validation errors.
 */

import type { QueuedFile } from '@/hooks/useFileUpload';
import { FilePreviewItem } from './FilePreviewItem';

interface FilePreviewAreaProps {
  queuedFiles: QueuedFile[];
  validationError: string | null;
  onRemoveFile: (id: string) => void;
  onClearError: () => void;
}

export function FilePreviewArea({
  queuedFiles,
  validationError,
  onRemoveFile,
  onClearError,
}: FilePreviewAreaProps) {
  if (queuedFiles.length === 0 && !validationError) return null;

  return (
    <div className="px-4 pt-3">
      {/* Validation error message */}
      {validationError && (
        <div
          role="alert"
          className="flex items-center justify-between mb-2 px-3 py-2 rounded-lg bg-destructive/10 border border-destructive/30 text-destructive text-xs"
        >
          <span>{validationError}</span>
          <button
            type="button"
            onClick={onClearError}
            aria-label="Dismiss error"
            className="ml-2 text-destructive hover:text-destructive/80 font-medium"
          >
            ✕
          </button>
        </div>
      )}

      {/* File previews */}
      {queuedFiles.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {queuedFiles.map((qf) => (
            <FilePreviewItem key={qf.id} queuedFile={qf} onRemove={onRemoveFile} />
          ))}
        </div>
      )}
    </div>
  );
}
