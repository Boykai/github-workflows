/**
 * Single file preview component.
 * Shows image thumbnail or file-name chip with type icon and dismiss button.
 */

import { FileText, FileImage, File, X } from 'lucide-react';
import type { QueuedFile } from '@/hooks/useFileUpload';

interface FilePreviewItemProps {
  queuedFile: QueuedFile;
  onRemove: (id: string) => void;
}

function getFileIcon(mimeType: string) {
  if (mimeType.startsWith('image/')) return FileImage;
  if (mimeType === 'application/pdf' || mimeType === 'text/plain') return FileText;
  return File;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function FilePreviewItem({ queuedFile, onRemove }: FilePreviewItemProps) {
  const { id, file, previewUrl, status, error } = queuedFile;
  const isImage = file.type.startsWith('image/');
  const IconComponent = getFileIcon(file.type);

  return (
    <div
      className={`relative group flex items-center gap-2 p-2 rounded-lg border transition-colors ${
        status === 'error'
          ? 'border-destructive bg-destructive/10'
          : status === 'uploading'
            ? 'border-primary/50 bg-primary/5'
            : 'border-border bg-muted/50'
      }`}
      aria-label={`Attached file: ${file.name}`}
    >
      {/* Preview / Icon */}
      {isImage && previewUrl ? (
        <img
          src={previewUrl}
          alt={`Preview of ${file.name}`}
          className="w-10 h-10 rounded object-cover shrink-0"
        />
      ) : (
        <div className="w-10 h-10 rounded bg-muted flex items-center justify-center shrink-0">
          <IconComponent size={20} className="text-muted-foreground" />
        </div>
      )}

      {/* File info */}
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium text-foreground truncate">{file.name}</p>
        <p className="text-xs text-muted-foreground">
          {status === 'uploading' ? 'Uploading...' : status === 'error' ? error : formatFileSize(file.size)}
        </p>
      </div>

      {/* Dismiss button */}
      <button
        type="button"
        onClick={() => onRemove(id)}
        aria-label={`Remove ${file.name}`}
        className="w-6 h-6 flex items-center justify-center rounded-full text-muted-foreground transition-colors hover:text-foreground hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
      >
        <X size={14} />
      </button>
    </div>
  );
}
