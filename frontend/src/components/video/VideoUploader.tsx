/**
 * VideoUploader — drag-and-drop video upload component with progress tracking.
 *
 * Features:
 * - Drag-and-drop and file picker support
 * - Format validation (MP4, MOV, AVI, MKV, WebM)
 * - File size validation (2 GB limit)
 * - Upload progress bar with percentage
 * - Processing/transcoding status indicator
 * - Error states with actionable messages
 * - Responsive and accessible
 */

import { useCallback, useRef, useState } from 'react';
import { Upload, Film, X, AlertTriangle, CheckCircle2, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { FILE_VALIDATION } from '@/types';
import { videoApi } from '@/services/api';
import type { VideoUploadResponse, VideoStatus } from '@/types';

interface VideoUploaderProps {
  /** Callback when upload completes successfully */
  onUploadComplete?: (video: VideoUploadResponse) => void;
  /** Callback on upload error */
  onUploadError?: (error: string) => void;
  /** Additional CSS classes */
  className?: string;
}

interface UploadState {
  file: File | null;
  progress: number;
  status: 'idle' | 'validating' | 'uploading' | 'processing' | 'complete' | 'error';
  error: string | null;
  videoStatus: VideoStatus | null;
}

const ACCEPTED_EXTENSIONS = FILE_VALIDATION.allowedVideoTypes;
const ACCEPTED_MIME_TYPES = [
  'video/mp4',
  'video/quicktime',
  'video/x-msvideo',
  'video/x-matroska',
  'video/webm',
];
const ACCEPT_STRING = ACCEPTED_EXTENSIONS.join(',') + ',' + ACCEPTED_MIME_TYPES.join(',');

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

function getFileExtension(filename: string): string {
  const dotIndex = filename.lastIndexOf('.');
  if (dotIndex < 0) return '';
  return filename.slice(dotIndex).toLowerCase();
}

export function VideoUploader({ onUploadComplete, onUploadError, className }: VideoUploaderProps) {
  const [state, setState] = useState<UploadState>({
    file: null,
    progress: 0,
    status: 'idle',
    error: null,
    videoStatus: null,
  });
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = useCallback((file: File): string | null => {
    const ext = getFileExtension(file.name);

    // Check format
    if (!ACCEPTED_EXTENSIONS.includes(ext as (typeof ACCEPTED_EXTENSIONS)[number])) {
      const supported = ACCEPTED_EXTENSIONS.join(', ');
      return `Unsupported format "${ext}". Please upload ${supported} files.`;
    }

    // Check file size (2 GB)
    if (file.size > FILE_VALIDATION.maxVideoFileSize) {
      return `File size (${formatFileSize(file.size)}) exceeds the 2 GB limit. Please compress or trim your video.`;
    }

    // Check empty file
    if (file.size === 0) {
      return 'The selected file is empty. Please choose a valid video file.';
    }

    return null;
  }, []);

  const handleUpload = useCallback(
    async (file: File) => {
      // Validate
      setState({
        file,
        progress: 0,
        status: 'validating',
        error: null,
        videoStatus: null,
      });

      const validationError = validateFile(file);
      if (validationError) {
        setState((prev) => ({
          ...prev,
          status: 'error',
          error: validationError,
        }));
        onUploadError?.(validationError);
        return;
      }

      // Upload
      setState((prev) => ({ ...prev, status: 'uploading', progress: 0 }));

      try {
        const response = await videoApi.uploadVideo(file, (progress) => {
          setState((prev) => ({ ...prev, progress }));
        });

        setState((prev) => ({
          ...prev,
          status: 'complete',
          progress: 100,
          videoStatus: response.status,
        }));

        onUploadComplete?.(response);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Upload failed. Please try again.';
        setState((prev) => ({
          ...prev,
          status: 'error',
          error: message,
        }));
        onUploadError?.(message);
      }
    },
    [validateFile, onUploadComplete, onUploadError]
  );

  const handleFileSelect = useCallback(
    (files: FileList | null) => {
      if (!files || files.length === 0) return;
      handleUpload(files[0]);
    },
    [handleUpload]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragOver(false);
      handleFileSelect(e.dataTransfer.files);
    },
    [handleFileSelect]
  );

  const handleReset = useCallback(() => {
    setState({
      file: null,
      progress: 0,
      status: 'idle',
      error: null,
      videoStatus: null,
    });
    if (fileInputRef.current) fileInputRef.current.value = '';
  }, []);

  return (
    <div className={cn('w-full', className)}>
      {state.status === 'idle' ? (
        /* Drop zone */
        <div
          className={cn(
            'flex flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed p-8 transition-colors cursor-pointer',
            isDragOver
              ? 'border-primary bg-primary/5'
              : 'border-border hover:border-primary/50 hover:bg-muted/30'
          )}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              fileInputRef.current?.click();
            }
          }}
          aria-label="Upload video — drag and drop or click to browse"
        >
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
            <Upload className="h-6 w-6 text-primary" />
          </div>
          <div className="text-center">
            <p className="text-sm font-medium">
              Drag & drop a video file, or{' '}
              <span className="text-primary underline">browse</span>
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              MP4, MOV, AVI, MKV, WebM — up to 2 GB
            </p>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept={ACCEPT_STRING}
            onChange={(e) => handleFileSelect(e.target.files)}
            className="hidden"
            aria-hidden="true"
          />
        </div>
      ) : (
        /* Upload progress / status */
        <div className="rounded-lg border border-border p-4">
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-muted">
              <Film className="h-5 w-5 text-muted-foreground" />
            </div>

            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">{state.file?.name}</p>
              <p className="text-xs text-muted-foreground">
                {state.file && formatFileSize(state.file.size)}
              </p>

              {/* Progress bar */}
              {(state.status === 'uploading' || state.status === 'validating') && (
                <div className="mt-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">
                      {state.status === 'validating' ? 'Validating…' : 'Uploading…'}
                    </span>
                    <span className="font-medium">{state.progress}%</span>
                  </div>
                  <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-muted">
                    <div
                      className="h-full rounded-full bg-primary transition-all duration-300"
                      style={{ width: `${state.progress}%` }}
                      role="progressbar"
                      aria-valuenow={state.progress}
                      aria-valuemin={0}
                      aria-valuemax={100}
                      aria-label="Upload progress"
                    />
                  </div>
                </div>
              )}

              {/* Processing status */}
              {state.status === 'processing' && (
                <div className="mt-2 flex items-center gap-1.5 text-xs text-muted-foreground">
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  Processing video…
                </div>
              )}

              {/* Complete status */}
              {state.status === 'complete' && (
                <div className="mt-2 flex items-center gap-1.5 text-xs text-green-600">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  Upload complete
                </div>
              )}

              {/* Error status */}
              {state.status === 'error' && (
                <div className="mt-2 flex items-center gap-1.5 text-xs text-destructive">
                  <AlertTriangle className="h-3.5 w-3.5" />
                  {state.error}
                </div>
              )}
            </div>

            {/* Close/cancel button */}
            <button
              type="button"
              onClick={handleReset}
              className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
              aria-label="Cancel upload"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
