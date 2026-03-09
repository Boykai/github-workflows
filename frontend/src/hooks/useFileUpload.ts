/**
 * useFileUpload — manages file selection, client-side validation,
 * upload state, and preview data.
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import type { FileAttachment } from '@/types';
import { FILE_VALIDATION, ALLOWED_TYPES } from '@/types';
import { chatApi } from '@/services/api';

interface UseFileUploadReturn {
  files: FileAttachment[];
  isUploading: boolean;
  errors: string[];
  addFiles: (fileList: FileList | File[]) => void;
  removeFile: (fileId: string) => void;
  uploadAll: () => Promise<string[]>;
  clearAll: () => void;
}

let fileIdCounter = 0;

function generateFileId(): string {
  return `file-${Date.now()}-${++fileIdCounter}`;
}

function getFileExtension(filename: string): string {
  const dotIndex = filename.lastIndexOf('.');
  if (dotIndex < 0) return '';
  return filename.slice(dotIndex).toLowerCase();
}

function createPreviewUrl(file: File): string | null {
  if (!file.type.startsWith('image/')) return null;
  return URL.createObjectURL(file);
}

function revokePreviewUrl(file: Pick<FileAttachment, 'previewUrl'>): void {
  if (file.previewUrl) {
    URL.revokeObjectURL(file.previewUrl);
  }
}

export function useFileUpload(): UseFileUploadReturn {
  const [files, setFiles] = useState<FileAttachment[]>([]);
  const [errors, setErrors] = useState<string[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const filesRef = useRef<FileAttachment[]>([]);

  useEffect(() => {
    filesRef.current = files;
  }, [files]);

  useEffect(
    () => () => {
      for (const file of filesRef.current) {
        revokePreviewUrl(file);
      }
    },
    []
  );

  const addFiles = useCallback(
    (fileList: FileList | File[]) => {
      const newErrors: string[] = [];
      const newFiles: FileAttachment[] = [];
      const incomingFiles = Array.from(fileList);

      for (const file of incomingFiles) {
        const ext = getFileExtension(file.name);

        // Check total file count
        if (files.length + newFiles.length >= FILE_VALIDATION.maxFilesPerMessage) {
          newErrors.push(`Maximum ${FILE_VALIDATION.maxFilesPerMessage} files allowed per message`);
          break;
        }

        // Check file size
        if (file.size > FILE_VALIDATION.maxFileSize) {
          newErrors.push(`${file.name}: File exceeds the 10 MB size limit`);
          continue;
        }

        // Check file type
        if (!ALLOWED_TYPES.includes(ext as (typeof ALLOWED_TYPES)[number])) {
          newErrors.push(`${file.name}: File type ${ext || 'unknown'} is not supported`);
          continue;
        }

        newFiles.push({
          id: generateFileId(),
          file,
          filename: file.name,
          fileSize: file.size,
          contentType: file.type || 'application/octet-stream',
          previewUrl: createPreviewUrl(file),
          status: 'pending',
          progress: 0,
          fileUrl: null,
          error: null,
        });
      }

      if (newFiles.length > 0) {
        setFiles((prev) => [...prev, ...newFiles]);
      }
      if (newErrors.length > 0) {
        setErrors(newErrors);
        // Clear errors after a few seconds
        setTimeout(() => setErrors([]), 5000);
      }
    },
    [files.length]
  );

  const removeFile = useCallback((fileId: string) => {
    setFiles((prev) => {
      const fileToRemove = prev.find((f) => f.id === fileId);
      if (fileToRemove) {
        revokePreviewUrl(fileToRemove);
      }
      return prev.filter((f) => f.id !== fileId);
    });
  }, []);

  const uploadAll = useCallback(async (): Promise<string[]> => {
    const pendingFiles = files.filter((f) => f.status === 'pending');
    if (pendingFiles.length === 0) {
      // Return already-uploaded URLs
      return files.filter((f) => f.status === 'uploaded' && f.fileUrl).map((f) => f.fileUrl!);
    }

    setIsUploading(true);
    const urls: string[] = [];

    // Include already uploaded URLs
    for (const f of files) {
      if (f.status === 'uploaded' && f.fileUrl) {
        urls.push(f.fileUrl);
      }
    }

    for (const file of pendingFiles) {
      // Mark as uploading
      setFiles((prev) =>
        prev.map((f) =>
          f.id === file.id ? { ...f, status: 'uploading' as const, progress: 50 } : f
        )
      );

      try {
        const response = await chatApi.uploadFile(file.file);
        urls.push(response.file_url);
        setFiles((prev) =>
          prev.map((f) =>
            f.id === file.id
              ? { ...f, status: 'uploaded' as const, progress: 100, fileUrl: response.file_url }
              : f
          )
        );
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Upload failed';
        setFiles((prev) =>
          prev.map((f) =>
            f.id === file.id ? { ...f, status: 'error' as const, error: errorMsg } : f
          )
        );
      }
    }

    setIsUploading(false);
    return urls;
  }, [files]);

  const clearAll = useCallback(() => {
    for (const file of filesRef.current) {
      revokePreviewUrl(file);
    }
    setFiles([]);
    setErrors([]);
  }, []);

  return {
    files,
    isUploading,
    errors,
    addFiles,
    removeFile,
    uploadAll,
    clearAll,
  };
}
