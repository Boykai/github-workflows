/**
 * useVideoUpload — manages video upload state, validation, and API interaction.
 *
 * Provides a clean interface for video upload workflows including
 * file validation, progress tracking, and error management.
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { FILE_VALIDATION } from '@/types';
import type { VideoUploadResponse } from '@/types';
import { videoApi } from '@/services/api';

export interface VideoUploadFile {
  id: string;
  file: File;
  filename: string;
  fileSize: number;
  progress: number;
  status: 'pending' | 'validating' | 'uploading' | 'complete' | 'error';
  error: string | null;
  response: VideoUploadResponse | null;
}

interface UseVideoUploadReturn {
  files: VideoUploadFile[];
  isUploading: boolean;
  errors: string[];
  addVideo: (file: File) => void;
  removeVideo: (fileId: string) => void;
  uploadAll: () => Promise<VideoUploadResponse[]>;
  clearAll: () => void;
}

const ALLOWED_EXTENSIONS = FILE_VALIDATION.allowedVideoTypes;

let videoIdCounter = 0;
function generateVideoId(): string {
  return `video-${Date.now()}-${++videoIdCounter}`;
}

function getFileExtension(filename: string): string {
  const dotIndex = filename.lastIndexOf('.');
  if (dotIndex < 0) return '';
  return filename.slice(dotIndex).toLowerCase();
}

export function useVideoUpload(): UseVideoUploadReturn {
  const [files, setFiles] = useState<VideoUploadFile[]>([]);
  const [errors, setErrors] = useState<string[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const errorTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (errorTimerRef.current) clearTimeout(errorTimerRef.current);
    };
  }, []);

  const addVideo = useCallback(
    (file: File) => {
      const newErrors: string[] = [];
      const ext = getFileExtension(file.name);

      // Validate extension
      if (!ALLOWED_EXTENSIONS.includes(ext as (typeof ALLOWED_EXTENSIONS)[number])) {
        newErrors.push(
          `${file.name}: Unsupported format "${ext}". Accepted: ${ALLOWED_EXTENSIONS.join(', ')}`
        );
      }

      // Validate size (2 GB)
      if (file.size > FILE_VALIDATION.maxVideoFileSize) {
        newErrors.push(`${file.name}: File exceeds the 2 GB size limit`);
      }

      // Validate not empty
      if (file.size === 0) {
        newErrors.push(`${file.name}: File is empty`);
      }

      if (newErrors.length > 0) {
        setErrors(newErrors);
        if (errorTimerRef.current) clearTimeout(errorTimerRef.current);
        errorTimerRef.current = setTimeout(() => setErrors([]), 5000);
        return;
      }

      const newFile: VideoUploadFile = {
        id: generateVideoId(),
        file,
        filename: file.name,
        fileSize: file.size,
        progress: 0,
        status: 'pending',
        error: null,
        response: null,
      };

      setFiles((prev) => [...prev, newFile]);
    },
    [setErrors, setFiles]
  );

  const removeVideo = useCallback((fileId: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== fileId));
  }, []);

  const uploadAll = useCallback(async (): Promise<VideoUploadResponse[]> => {
    const results: VideoUploadResponse[] = [];
    const pendingFiles = files.filter((f) => f.status === 'pending');

    if (pendingFiles.length === 0) {
      // Return already-completed uploads
      return files.filter((f) => f.response).map((f) => f.response!);
    }

    setIsUploading(true);

    for (const videoFile of pendingFiles) {
      setFiles((prev) =>
        prev.map((f) => (f.id === videoFile.id ? { ...f, status: 'uploading' as const } : f))
      );

      try {
        const response = await videoApi.uploadVideo(videoFile.file, (progress) => {
          setFiles((prev) =>
            prev.map((f) => (f.id === videoFile.id ? { ...f, progress } : f))
          );
        });

        results.push(response);
        setFiles((prev) =>
          prev.map((f) =>
            f.id === videoFile.id
              ? { ...f, status: 'complete' as const, progress: 100, response }
              : f
          )
        );
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Upload failed';
        setFiles((prev) =>
          prev.map((f) =>
            f.id === videoFile.id ? { ...f, status: 'error' as const, error: errorMsg } : f
          )
        );
      }
    }

    setIsUploading(false);
    return results;
  }, [files]);

  const clearAll = useCallback(() => {
    setFiles([]);
    setErrors([]);
  }, []);

  return {
    files,
    isUploading,
    errors,
    addVideo,
    removeVideo,
    uploadAll,
    clearAll,
  };
}
