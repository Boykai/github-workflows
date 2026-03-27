/**
 * FilePreviewChips — inline preview chips for selected files.
 * Renders between the ChatToolbar and the text input.
 */

import { X, FileText, Image, Loader2, Check, AlertTriangle } from '@/lib/icons';
import type { FileAttachment } from '@/types';
import { cn } from '@/lib/utils';

interface FilePreviewChipsProps {
  files: FileAttachment[];
  onRemove: (fileId: string) => void;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/** @internal Exported for testing. */
export function truncateFilename(name: string, max = 20): string {
  if (name.length <= max) return name;
  const ext = name.lastIndexOf('.');
  if (ext > 0) {
    const extStr = name.slice(ext);
    const availableForBase = Math.max(1, max - extStr.length - 1);
    const base = name.slice(0, availableForBase);
    return `${base}…${extStr}`;
  }
  return `${name.slice(0, max - 1)}…`;
}

function isImageFile(contentType: string): boolean {
  return contentType.startsWith('image/');
}

function StatusIcon({ status }: { status: FileAttachment['status'] }) {
  switch (status) {
    case 'uploading':
      return <Loader2 className="w-3 h-3 animate-spin text-muted-foreground" />;
    case 'uploaded':
      return <Check className="w-3 h-3 text-green-500" />;
    case 'error':
      return <AlertTriangle className="w-3 h-3 text-destructive" />;
    default:
      return null;
  }
}

export function FilePreviewChips({ files, onRemove }: FilePreviewChipsProps) {
  if (files.length === 0) return null;

  return (
    <div className="flex items-center gap-2 overflow-x-auto border-b border-border bg-background/44 px-4 py-2">
      {files.map((file) => (
        <div
          key={file.id}
          className={cn('flex items-center gap-1.5 px-2 py-1 rounded-md text-xs border shrink-0', file.status === 'error'
              ? 'border-destructive/50 bg-destructive/5'
              : 'border-border bg-background/76')}
          title={file.error || file.filename}
        >
          {isImageFile(file.contentType) ? (
            <Image className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
          ) : (
            <FileText className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
          )}
          <span className="font-medium truncate max-w-[120px]">
            {truncateFilename(file.filename)}
          </span>
          <span className="text-muted-foreground whitespace-nowrap">
            {formatFileSize(file.fileSize)}
          </span>
          <StatusIcon status={file.status} />
          <button
            type="button"
            onClick={() => onRemove(file.id)}
            className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-primary/10 hover:text-foreground"
            aria-label={`Remove ${file.filename}`}
          >
            <X className="w-3 h-3" />
          </button>
        </div>
      ))}
    </div>
  );
}
