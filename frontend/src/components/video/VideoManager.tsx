/**
 * VideoManager — gallery view for managing uploaded videos.
 *
 * Features:
 * - Grid layout with video thumbnails
 * - Inline metadata editing (title, description)
 * - Delete with confirmation
 * - Responsive grid layout
 * - Video playback on click
 */

import { useCallback, useState } from 'react';
import { Film, Pencil, Trash2, X, Check, Clock, AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { VideoMetadata, VideoUpdateRequest } from '@/types';
import { VideoPlayer } from './VideoPlayer';

interface VideoManagerProps {
  /** List of videos to display */
  videos: VideoMetadata[];
  /** Callback when a video is updated */
  onUpdate?: (videoId: string, update: VideoUpdateRequest) => void;
  /** Callback when a video is deleted */
  onDelete?: (videoId: string) => void;
  /** Whether operations are in progress */
  isLoading?: boolean;
  /** Additional CSS classes */
  className?: string;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

function formatDuration(seconds: number | null): string {
  if (!seconds || seconds <= 0) return '--:--';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  return `${m}:${String(s).padStart(2, '0')}`;
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

function StatusBadge({ status }: { status: VideoMetadata['status'] }) {
  switch (status) {
    case 'processing':
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-yellow-100 px-2 py-0.5 text-xs font-medium text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400">
          <Clock className="h-3 w-3" />
          Processing
        </span>
      );
    case 'error':
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-destructive/10 px-2 py-0.5 text-xs font-medium text-destructive">
          <AlertTriangle className="h-3 w-3" />
          Error
        </span>
      );
    case 'ready':
      return null;
    default:
      return null;
  }
}

export function VideoManager({
  videos,
  onUpdate,
  onDelete,
  isLoading = false,
  className,
}: VideoManagerProps) {
  const [playingVideoId, setPlayingVideoId] = useState<string | null>(null);
  const [editingVideoId, setEditingVideoId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  const startEditing = useCallback((video: VideoMetadata) => {
    setEditingVideoId(video.id);
    setEditTitle(video.title);
    setEditDescription(video.description);
  }, []);

  const saveEditing = useCallback(() => {
    if (editingVideoId) {
      onUpdate?.(editingVideoId, {
        title: editTitle,
        description: editDescription,
      });
      setEditingVideoId(null);
    }
  }, [editingVideoId, editTitle, editDescription, onUpdate]);

  const cancelEditing = useCallback(() => {
    setEditingVideoId(null);
  }, []);

  const handleDelete = useCallback(
    (videoId: string) => {
      onDelete?.(videoId);
      setConfirmDeleteId(null);
    },
    [onDelete]
  );

  if (videos.length === 0) {
    return (
      <div
        className={cn(
          'flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-border p-12 text-center',
          className
        )}
      >
        <Film className="h-10 w-10 text-muted-foreground/50" />
        <p className="text-sm text-muted-foreground">No videos uploaded yet</p>
      </div>
    );
  }

  // Show player overlay
  const playingVideo = playingVideoId ? videos.find((v) => v.id === playingVideoId) : null;

  return (
    <div className={cn('space-y-4', className)}>
      {/* Video player overlay */}
      {playingVideo && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4">
          <div className="relative w-full max-w-4xl">
            <button
              type="button"
              onClick={() => setPlayingVideoId(null)}
              className="absolute -top-10 right-0 flex h-8 w-8 items-center justify-center rounded-full text-white hover:bg-white/20 transition-colors"
              aria-label="Close video player"
            >
              <X className="h-5 w-5" />
            </button>
            <VideoPlayer
              src={playingVideo.file_url}
              poster={playingVideo.thumbnail_url ?? undefined}
              title={playingVideo.title}
              className="aspect-video w-full"
            />
          </div>
        </div>
      )}

      {/* Video grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {videos.map((video) => (
          <div
            key={video.id}
            className={cn(
              'group rounded-lg border border-border bg-background overflow-hidden transition-shadow hover:shadow-md',
              isLoading && 'opacity-60 pointer-events-none'
            )}
          >
            {/* Thumbnail / click to play */}
            <button
              type="button"
              onClick={() => video.status === 'ready' && setPlayingVideoId(video.id)}
              className="relative aspect-video w-full bg-muted"
              aria-label={`Play ${video.title || video.filename}`}
              disabled={video.status !== 'ready'}
            >
              {video.thumbnail_url ? (
                <img
                  src={video.thumbnail_url}
                  alt={video.title || video.filename}
                  className="h-full w-full object-cover"
                />
              ) : (
                <div className="flex h-full w-full items-center justify-center">
                  <Film className="h-10 w-10 text-muted-foreground/40" />
                </div>
              )}
              {video.status === 'ready' && (
                <div className="absolute inset-0 flex items-center justify-center bg-black/0 group-hover:bg-black/20 transition-colors">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/80 text-primary-foreground opacity-0 group-hover:opacity-100 transition-opacity">
                    <Film className="h-6 w-6" />
                  </div>
                </div>
              )}
              {/* Duration badge */}
              {video.duration && (
                <span className="absolute bottom-1 right-1 rounded bg-black/70 px-1.5 py-0.5 text-xs text-white">
                  {formatDuration(video.duration)}
                </span>
              )}
            </button>

            {/* Video info */}
            <div className="p-3">
              {editingVideoId === video.id ? (
                /* Edit mode */
                <div className="space-y-2">
                  <input
                    type="text"
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    className="w-full rounded-md border border-border bg-background px-2 py-1 text-sm"
                    placeholder="Video title"
                    aria-label="Video title"
                    maxLength={200}
                  />
                  <textarea
                    value={editDescription}
                    onChange={(e) => setEditDescription(e.target.value)}
                    className="w-full rounded-md border border-border bg-background px-2 py-1 text-sm resize-none"
                    placeholder="Description"
                    rows={2}
                    aria-label="Video description"
                    maxLength={2000}
                  />
                  <div className="flex justify-end gap-1">
                    <button
                      type="button"
                      onClick={cancelEditing}
                      className="flex h-7 w-7 items-center justify-center rounded text-muted-foreground hover:bg-muted transition-colors"
                      aria-label="Cancel editing"
                    >
                      <X className="h-4 w-4" />
                    </button>
                    <button
                      type="button"
                      onClick={saveEditing}
                      className="flex h-7 w-7 items-center justify-center rounded text-primary hover:bg-primary/10 transition-colors"
                      aria-label="Save changes"
                    >
                      <Check className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ) : (
                /* Display mode */
                <>
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0 flex-1">
                      <h3 className="truncate text-sm font-medium">
                        {video.title || video.filename}
                      </h3>
                      {video.description && (
                        <p className="mt-0.5 line-clamp-2 text-xs text-muted-foreground">
                          {video.description}
                        </p>
                      )}
                    </div>
                    <StatusBadge status={video.status} />
                  </div>

                  <div className="mt-2 flex items-center justify-between">
                    <span className="text-xs text-muted-foreground">
                      {formatFileSize(video.file_size)} · {formatDate(video.created_at)}
                    </span>

                    <div className="flex items-center gap-0.5">
                      <button
                        type="button"
                        onClick={() => startEditing(video)}
                        className="flex h-7 w-7 items-center justify-center rounded text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                        aria-label={`Edit ${video.title || video.filename}`}
                      >
                        <Pencil className="h-3.5 w-3.5" />
                      </button>

                      {confirmDeleteId === video.id ? (
                        <div className="flex items-center gap-0.5">
                          <button
                            type="button"
                            onClick={() => handleDelete(video.id)}
                            className="flex h-7 items-center gap-1 rounded bg-destructive px-2 text-xs text-destructive-foreground hover:bg-destructive/90 transition-colors"
                            aria-label="Confirm delete"
                          >
                            Delete
                          </button>
                          <button
                            type="button"
                            onClick={() => setConfirmDeleteId(null)}
                            className="flex h-7 w-7 items-center justify-center rounded text-muted-foreground hover:bg-muted transition-colors"
                            aria-label="Cancel delete"
                          >
                            <X className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      ) : (
                        <button
                          type="button"
                          onClick={() => setConfirmDeleteId(video.id)}
                          className="flex h-7 w-7 items-center justify-center rounded text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors"
                          aria-label={`Delete ${video.title || video.filename}`}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      )}
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
