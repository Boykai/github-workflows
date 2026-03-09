/**
 * FilePreviewChips — inline preview chips for selected files.
 * Renders between the ChatToolbar and the text input.
 */

import { X, FileText, ImageIcon, Loader2, Check, AlertTriangle, Paperclip } from 'lucide-react';
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
    <div className="border-b border-border bg-background/44 px-4 py-3">
      <div className="mb-2 flex items-center justify-between gap-3 text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-1.5 font-medium text-foreground">
          <Paperclip className="h-3.5 w-3.5 text-primary" />
          Attachments
        </span>
        <span>
          {files.length} ready to send
        </span>
      </div>
      <div className="flex flex-wrap items-start gap-3">
        {files.map((file) => {
          const hasImagePreview = isImageFile(file.contentType) && file.previewUrl;

          if (hasImagePreview) {
            return (
              <div key={file.id} className="flex max-w-[220px] items-center gap-3">
                <div
                  className={`relative h-20 w-20 shrink-0 overflow-hidden rounded-2xl border shadow-sm ${
                    file.status === 'error'
                      ? 'border-destructive/40 bg-destructive/5'
                      : 'border-border/70 bg-background/80'
                  }`}
                  title={file.error || file.filename}
                >
                  <img
                    src={file.previewUrl ?? undefined}
                    alt={file.filename}
                    className="h-full w-full object-cover"
                  />
                  <div className="absolute inset-x-0 bottom-0 flex items-center justify-between bg-gradient-to-t from-black/70 via-black/15 to-transparent px-2 py-1 text-[10px] text-white">
                    <span className="truncate">{formatFileSize(file.fileSize)}</span>
                    <StatusIcon status={file.status} />
                  </div>
                  <button
                    type="button"
                    onClick={() => onRemove(file.id)}
                    className="absolute right-1 top-1 flex h-6 w-6 items-center justify-center rounded-full bg-background/85 text-muted-foreground shadow-sm transition-colors hover:bg-background hover:text-foreground"
                    aria-label={`Remove ${file.filename}`}
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                </div>
                <div className="min-w-0">
                  <div className="mb-1 inline-flex items-center gap-1 rounded-full bg-primary/10 px-2 py-0.5 text-[11px] font-medium text-primary">
                    <ImageIcon className="h-3 w-3" />
                    Image
                  </div>
                  <p className="truncate text-sm font-medium text-foreground">{file.filename}</p>
                  {file.error ? (
                    <p className="text-xs text-destructive">{file.error}</p>
                  ) : (
                    <p className="text-xs text-muted-foreground">
                      {formatFileSize(file.fileSize)}
                    </p>
                  )}
                </div>
              </div>
            );
          }

          return (
            <div
              key={file.id}
              className={`flex max-w-full items-center gap-2 rounded-xl border px-3 py-2 text-xs shadow-sm ${
                file.status === 'error'
                  ? 'border-destructive/40 bg-destructive/5'
                  : 'border-border/70 bg-background/80'
              }`}
              title={file.error || file.filename}
            >
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
                <FileText className="h-4 w-4" />
              </div>
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-foreground">
                  {truncateFilename(file.filename, 28)}
                </p>
                <div className="flex items-center gap-1.5 text-muted-foreground">
                  <span>{formatFileSize(file.fileSize)}</span>
                  <StatusIcon status={file.status} />
                </div>
                {file.error && <p className="mt-0.5 text-destructive">{file.error}</p>}
              </div>
              <button
                type="button"
                onClick={() => onRemove(file.id)}
                className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-primary/10 hover:text-foreground"
                aria-label={`Remove ${file.filename}`}
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
