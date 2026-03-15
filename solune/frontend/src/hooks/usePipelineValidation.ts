/**
 * usePipelineValidation — validation state for pipeline configs.
 */

import { useState, useCallback } from 'react';
import type { PipelineConfig, PipelineValidationErrors } from '@/types';

export interface UsePipelineValidationReturn {
  validationErrors: PipelineValidationErrors;
  validatePipeline: () => boolean;
  clearValidationError: (field: string) => void;
}

export function usePipelineValidation(
  pipeline: PipelineConfig | null,
): UsePipelineValidationReturn {
  const [validationErrors, setValidationErrors] = useState<PipelineValidationErrors>({});

  const validatePipeline = useCallback((): boolean => {
    const errors: PipelineValidationErrors = {};
    if (!pipeline?.name?.trim()) {
      errors.name = 'Pipeline name is required';
    }
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  }, [pipeline]);

  const clearValidationError = useCallback((field: string) => {
    setValidationErrors((prev) => {
      if (!prev[field]) return prev;
      const next = { ...prev };
      delete next[field];
      return next;
    });
  }, []);

  return { validationErrors, validatePipeline, clearValidationError };
}
