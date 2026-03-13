/**
 * VideosPage — video upload, playback, and management page.
 */

import { useCallback, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { videoApi } from '@/services/api';
import { VideoUploader } from '@/components/video/VideoUploader';
import { VideoManager } from '@/components/video/VideoManager';
import { CelestialCatalogHero } from '@/components/common/CelestialCatalogHero';
import type { VideoUploadResponse, VideoUpdateRequest } from '@/types';

export function VideosPage() {
  const queryClient = useQueryClient();
  const [uploadKey, setUploadKey] = useState(0);

  const { data, isLoading } = useQuery({
    queryKey: ['videos'],
    queryFn: () => videoApi.listVideos(),
  });

  const updateMutation = useMutation({
    mutationFn: ({ videoId, update }: { videoId: string; update: VideoUpdateRequest }) =>
      videoApi.updateVideo(videoId, update),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (videoId: string) => videoApi.deleteVideo(videoId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] });
    },
  });

  const handleUploadComplete = useCallback(
    (_video: VideoUploadResponse) => {
      queryClient.invalidateQueries({ queryKey: ['videos'] });
      // Reset uploader after successful upload
      setUploadKey((k) => k + 1);
    },
    [queryClient]
  );

  const handleUpdate = useCallback(
    (videoId: string, update: VideoUpdateRequest) => {
      updateMutation.mutate({ videoId, update });
    },
    [updateMutation]
  );

  const handleDelete = useCallback(
    (videoId: string) => {
      deleteMutation.mutate(videoId);
    },
    [deleteMutation]
  );

  return (
    <div className="celestial-fade-in flex h-full flex-col gap-5 overflow-auto rounded-[1.5rem] border border-border/70 bg-background/42 p-4 backdrop-blur-sm sm:gap-6 sm:rounded-[1.75rem] sm:p-6">
      <CelestialCatalogHero
        eyebrow="Media Library"
        title="Upload, view, and manage videos."
        description="Drag and drop video files to upload. Supports MP4, MOV, AVI, MKV, and WebM formats up to 2 GB."
      />

      <div className="space-y-6">
        {/* Upload section */}
        <section aria-label="Upload video">
          <VideoUploader key={uploadKey} onUploadComplete={handleUploadComplete} />
        </section>

        {/* Video gallery */}
        <section aria-label="Video library">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
            </div>
          ) : (
            <VideoManager
              videos={data?.videos ?? []}
              onUpdate={handleUpdate}
              onDelete={handleDelete}
              isLoading={updateMutation.isPending || deleteMutation.isPending}
            />
          )}
        </section>
      </div>
    </div>
  );
}
