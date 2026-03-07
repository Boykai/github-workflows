/**
 * FilePreviewChips — inline preview chips for selected files.
 * Renders between the ChatToolbar and the text input.
 */

import { X, FileText, Image, Loader2, Check, AlertTriangle } from 'lucide-react';
import type { FileAttachment } from '@/types';

interface FilePreviewChipsProps {
  files: FileAttachment[];
  onRemove: (fileId: string) => void;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function truncateFilename(name: string, max = 20): string {
  if (name.length <= max) return name;
  const ext = name.lastIndexOf('.');
  if (ext > 0) {
    const extStr = name.slice(ext);
    const base = name.slice(0, max - extStr.length - 1);
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
    <div className="flex items-center gap-2 px-4 py-2 overflow-x-auto border-b border-border bg-muted/30">
      {files.map((file) => (
        <div
          key={file.id}
          className={`flex items-center gap-1.5 px-2 py-1 rounded-md text-xs border shrink-0 ${
            file.status === 'error'
              ? 'border-destructive/50 bg-destructive/5'
              : 'border-border bg-background'
          }`}
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
            className="w-4 h-4 flex items-center justify-center rounded-full hover:bg-muted transition-colors text-muted-foreground hover:text-foreground shrink-0"
            aria-label={`Remove ${file.filename}`}
          >
            <X className="w-3 h-3" />
          </button>
        </div>
      ))}
    </div>
  );
}
