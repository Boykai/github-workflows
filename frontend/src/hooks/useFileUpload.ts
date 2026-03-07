/**
 * useFileUpload — manages file selection, client-side validation,
 * upload state, and preview data.
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import type { FileAttachment } from '@/types';
import { FILE_VALIDATION, ALLOWED_TYPES } from '@/types';
import { chatApi } from '@/services/api';

interface UploadAllResult {
  urls: string[];
  hasErrors: boolean;
}

interface UseFileUploadReturn {
  files: FileAttachment[];
  isUploading: boolean;
  errors: string[];
  addFiles: (fileList: FileList) => void;
  removeFile: (fileId: string) => void;
  uploadAll: () => Promise<UploadAllResult>;
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

export function useFileUpload(): UseFileUploadReturn {
  const [files, setFiles] = useState<FileAttachment[]>([]);
  const [errors, setErrors] = useState<string[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const errorTimeoutRef = useRef<number | null>(null);

  const scheduleErrorClear = useCallback(() => {
    if (errorTimeoutRef.current !== null) {
      window.clearTimeout(errorTimeoutRef.current);
    }

    errorTimeoutRef.current = window.setTimeout(() => {
      setErrors([]);
      errorTimeoutRef.current = null;
    }, 5000);
  }, []);

  useEffect(() => {
    return () => {
      if (errorTimeoutRef.current !== null) {
        window.clearTimeout(errorTimeoutRef.current);
      }
    };
  }, []);

  const addFiles = useCallback((fileList: FileList) => {
    const newErrors: string[] = [];
    const newFiles: FileAttachment[] = [];

    for (let i = 0; i < fileList.length; i++) {
      const file = fileList[i];
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
      if (!ALLOWED_TYPES.includes(ext as typeof ALLOWED_TYPES[number])) {
        newErrors.push(`${file.name}: File type ${ext || 'unknown'} is not supported`);
        continue;
      }

      newFiles.push({
        id: generateFileId(),
        file,
        filename: file.name,
        fileSize: file.size,
        contentType: file.type || 'application/octet-stream',
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
      scheduleErrorClear();
    }
  }, [files.length, scheduleErrorClear]);

  const removeFile = useCallback((fileId: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== fileId));
  }, []);

  const uploadAll = useCallback(async (): Promise<UploadAllResult> => {
    const pendingFiles = files.filter((f) => f.status === 'pending');
    if (pendingFiles.length === 0) {
      return {
        urls: files.filter((f) => f.status === 'uploaded' && f.fileUrl).map((f) => f.fileUrl!),
        hasErrors: files.some((f) => f.status === 'error'),
      };
    }

    setIsUploading(true);
    const urls: string[] = [];
    let hasErrors = files.some((f) => f.status === 'error');

    // Include already uploaded URLs
    for (const f of files) {
      if (f.status === 'uploaded' && f.fileUrl) {
        urls.push(f.fileUrl);
      }
    }

    for (const file of pendingFiles) {
      // Mark as uploading
      setFiles((prev) =>
        prev.map((f) => (f.id === file.id ? { ...f, status: 'uploading' as const, progress: 50 } : f))
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
        hasErrors = true;
        const errorMsg = err instanceof Error ? err.message : 'Upload failed';
        setFiles((prev) =>
          prev.map((f) =>
            f.id === file.id ? { ...f, status: 'error' as const, error: errorMsg } : f
          )
        );
      }
    }

    setIsUploading(false);
    if (hasErrors) {
      setErrors(['One or more files failed to upload. Remove the failed file and try again.']);
      scheduleErrorClear();
    }

    return { urls, hasErrors };
  }, [files, scheduleErrorClear]);

  const clearAll = useCallback(() => {
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
