/**
 * Hook for managing file uploads in chat.
 * Handles file selection, client-side validation, upload state, and queue management.
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { chatApi } from '@/services/api';
import type { FileAttachmentResponse } from '@/types';

const MAX_FILE_SIZE = 25 * 1024 * 1024; // 25 MiB
const MAX_ATTACHMENTS = 10;
const ALLOWED_MIME_TYPES = new Set([
  'image/jpeg',
  'image/png',
  'image/gif',
  'image/webp',
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'text/plain',
]);

const ACCEPTED_FORMATS_LABEL = 'JPG, PNG, GIF, WEBP, PDF, DOCX, TXT';

export interface QueuedFile {
  id: string;
  file: File;
  previewUrl: string | null;
  status: 'queued' | 'uploading' | 'uploaded' | 'error';
  error?: string;
  uploadResponse?: FileAttachmentResponse;
}

interface UseFileUploadReturn {
  queuedFiles: QueuedFile[];
  validationError: string | null;
  isUploading: boolean;
  addFiles: (files: FileList | File[]) => void;
  removeFile: (id: string) => void;
  uploadAll: () => Promise<string[]>;
  clearAll: () => void;
  clearError: () => void;
}

let fileIdCounter = 0;
function generateFileId(): string {
  return `file-${Date.now()}-${++fileIdCounter}`;
}

function isImageType(mimeType: string): boolean {
  return mimeType.startsWith('image/');
}

export function useFileUpload(): UseFileUploadReturn {
  const [queuedFiles, setQueuedFiles] = useState<QueuedFile[]>([]);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const objectUrlsRef = useRef<Set<string>>(new Set());

  // Revoke object URLs on unmount to prevent memory leaks
  useEffect(() => {
    const urls = objectUrlsRef.current;
    return () => {
      urls.forEach((url) => URL.revokeObjectURL(url));
      urls.clear();
    };
  }, []);

  const addFiles = useCallback((files: FileList | File[]) => {
    setValidationError(null);
    const fileArray = Array.from(files);

    setQueuedFiles((prev) => {
      const currentCount = prev.length;
      if (currentCount + fileArray.length > MAX_ATTACHMENTS) {
        setValidationError(`Maximum of ${MAX_ATTACHMENTS} files per message`);
        return prev;
      }

      const newQueued: QueuedFile[] = [];

      for (const file of fileArray) {
        // Validate size
        if (file.size > MAX_FILE_SIZE) {
          setValidationError('File exceeds the maximum size of 25 MB');
          continue;
        }

        // Validate type
        if (!ALLOWED_MIME_TYPES.has(file.type)) {
          setValidationError(
            `File type not supported. Accepted formats: ${ACCEPTED_FORMATS_LABEL}`
          );
          continue;
        }

        // Create preview URL for images
        let previewUrl: string | null = null;
        if (isImageType(file.type)) {
          previewUrl = URL.createObjectURL(file);
          objectUrlsRef.current.add(previewUrl);
        }

        newQueued.push({
          id: generateFileId(),
          file,
          previewUrl,
          status: 'queued',
        });
      }

      return [...prev, ...newQueued];
    });
  }, []);

  const removeFile = useCallback((id: string) => {
    setQueuedFiles((prev) => {
      const file = prev.find((f) => f.id === id);
      if (file?.previewUrl) {
        URL.revokeObjectURL(file.previewUrl);
        objectUrlsRef.current.delete(file.previewUrl);
      }
      return prev.filter((f) => f.id !== id);
    });
    setValidationError(null);
  }, []);

  const uploadAll = useCallback(async (): Promise<string[]> => {
    const toUpload = queuedFiles.filter((f) => f.status === 'queued');
    if (toUpload.length === 0) {
      // Return IDs of already-uploaded files
      return queuedFiles
        .filter((f) => f.status === 'uploaded' && f.uploadResponse)
        .map((f) => f.uploadResponse!.id);
    }

    setIsUploading(true);
    const attachmentIds: string[] = [];

    try {
      for (const queued of toUpload) {
        // Mark as uploading
        setQueuedFiles((prev) =>
          prev.map((f) => (f.id === queued.id ? { ...f, status: 'uploading' as const } : f))
        );

        try {
          const response = await chatApi.uploadFile(queued.file);
          attachmentIds.push(response.id);

          setQueuedFiles((prev) =>
            prev.map((f) =>
              f.id === queued.id
                ? { ...f, status: 'uploaded' as const, uploadResponse: response }
                : f
            )
          );
        } catch (err) {
          const errorMsg = err instanceof Error ? err.message : 'Upload failed';
          setQueuedFiles((prev) =>
            prev.map((f) =>
              f.id === queued.id ? { ...f, status: 'error' as const, error: errorMsg } : f
            )
          );
        }
      }

      // Also include previously uploaded IDs
      const prevUploaded = queuedFiles
        .filter((f) => f.status === 'uploaded' && f.uploadResponse)
        .map((f) => f.uploadResponse!.id);

      return [...prevUploaded, ...attachmentIds];
    } finally {
      setIsUploading(false);
    }
  }, [queuedFiles]);

  const clearAll = useCallback(() => {
    queuedFiles.forEach((f) => {
      if (f.previewUrl) {
        URL.revokeObjectURL(f.previewUrl);
        objectUrlsRef.current.delete(f.previewUrl);
      }
    });
    setQueuedFiles([]);
    setValidationError(null);
  }, [queuedFiles]);

  const clearError = useCallback(() => {
    setValidationError(null);
  }, []);

  return {
    queuedFiles,
    validationError,
    isUploading,
    addFiles,
    removeFile,
    uploadAll,
    clearAll,
    clearError,
  };
}
