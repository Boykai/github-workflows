/**
 * useMentionAutocomplete hook — manages the @mention autocomplete lifecycle.
 * Handles trigger detection, pipeline filtering, keyboard navigation,
 * token management, and active pipeline tracking.
 */

import { useState, useCallback, useEffect, useMemo, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { pipelinesApi } from '@/services/api';
import type { MentionFilterResult, MentionToken, PipelineConfigSummary } from '@/types';
import type { MentionInputHandle } from '@/components/chat/MentionInput';

interface UseMentionAutocompleteProps {
  projectId: string;
  inputRef: React.RefObject<MentionInputHandle | null>;
}

interface UseMentionAutocompleteReturn {
  // Autocomplete state
  isAutocompleteOpen: boolean;
  filteredPipelines: MentionFilterResult[];
  highlightedIndex: number;
  isLoadingPipelines: boolean;
  pipelineError: string | null;

  // Token state
  mentionTokens: MentionToken[];
  activePipelineId: string | null;
  activePipelineName: string | null;
  hasMultipleMentions: boolean;
  hasInvalidMentions: boolean;

  // Event handlers
  handleMentionTrigger: (query: string, offset: number) => void;
  handleMentionDismiss: () => void;
  handleSelect: (pipeline: PipelineConfigSummary) => void;
  handleTokenRemove: (pipelineId: string) => void;
  handleHighlightChange: (index: number) => void;
  handleKeyDown: (e: React.KeyboardEvent) => void;

  // Actions
  validateTokens: () => boolean;
  getSubmissionPipelineId: () => string | null;
  getPlainTextContent: () => string;
  clearTokens: () => void;
  reset: () => void;
}

export const MENTION_TOKEN_BASE =
  'inline-flex items-center gap-0.5 rounded px-1 py-0.5 text-xs font-medium align-baseline select-none';
export const MENTION_TOKEN_VALID = `${MENTION_TOKEN_BASE} bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200`;
export const MENTION_TOKEN_INVALID = `${MENTION_TOKEN_BASE} bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200`;

export function useMentionAutocomplete({
  projectId,
  inputRef,
}: UseMentionAutocompleteProps): UseMentionAutocompleteReturn {
  const [isAutocompleteOpen, setIsAutocompleteOpen] = useState(false);
  const [filterQuery, setFilterQuery] = useState('');
  const [highlightedIndex, setHighlightedIndex] = useState(0);
  const [triggerOffset, setTriggerOffset] = useState<number | null>(null);
  const [tokens, setTokens] = useState<MentionToken[]>([]);
  const [hasTriggered, setHasTriggered] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  // Clean up debounce timer on unmount
  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, []);

  // Fetch pipelines lazily (only after first @ trigger)
  const {
    data: pipelineData,
    isLoading,
    error: queryError,
  } = useQuery({
    queryKey: ['pipelines', projectId],
    queryFn: () => pipelinesApi.list(projectId),
    enabled: !!projectId && hasTriggered,
    staleTime: 30_000,
  });

  const pipelineError = queryError ? 'Unable to load pipelines' : null;

  // Client-side filtering with debounced query
  const filteredPipelines: MentionFilterResult[] = useMemo(() => {
    if (!pipelineData?.pipelines) return [];
    const query = filterQuery.toLowerCase();
    return pipelineData.pipelines
      .filter((p) => p.name.toLowerCase().includes(query))
      .slice(0, 10)
      .map((pipeline) => {
        const matchIndices: [number, number][] = [];
        if (query) {
          const idx = pipeline.name.toLowerCase().indexOf(query);
          if (idx >= 0) {
            matchIndices.push([idx, idx + query.length]);
          }
        }
        return { pipeline, matchIndices };
      });
  }, [pipelineData, filterQuery]);

  // Compute active pipeline from tokens
  const validTokens = useMemo(() => tokens.filter((t) => t.isValid), [tokens]);
  const invalidTokens = useMemo(() => tokens.filter((t) => !t.isValid), [tokens]);

  const activePipelineId =
    validTokens.length > 0 ? validTokens[validTokens.length - 1].pipelineId : null;
  const activePipelineName =
    validTokens.length > 0 ? validTokens[validTokens.length - 1].pipelineName : null;
  const hasMultipleMentions = validTokens.length > 1;
  const hasInvalidMentions = invalidTokens.length > 0;

  const handleMentionTrigger = useCallback(
    (query: string, offset: number) => {
      if (!hasTriggered) setHasTriggered(true);
      setTriggerOffset(offset);

      // Debounce filter updates
      if (debounceRef.current) clearTimeout(debounceRef.current);
      debounceRef.current = setTimeout(() => {
        setFilterQuery(query);
        setIsAutocompleteOpen(true);
        setHighlightedIndex(0);
      }, 150);
    },
    [hasTriggered]
  );

  const handleMentionDismiss = useCallback(() => {
    setIsAutocompleteOpen(false);
    setFilterQuery('');
    setTriggerOffset(null);
    if (debounceRef.current) clearTimeout(debounceRef.current);
  }, []);

  const handleSelect = useCallback(
    (pipeline: PipelineConfigSummary) => {
      const queryLength = filterQuery.length;
      const offset = triggerOffset ?? 0;

      // Insert the token into the contentEditable div
      inputRef.current?.insertTokenAtCursor(pipeline.id, pipeline.name, offset, queryLength);

      // Track the token
      setTokens((prev) => [
        ...prev,
        {
          pipelineId: pipeline.id,
          pipelineName: pipeline.name,
          isValid: true,
          position: offset,
        },
      ]);

      // Close autocomplete
      handleMentionDismiss();
      inputRef.current?.focus();
    },
    [filterQuery, triggerOffset, inputRef, handleMentionDismiss]
  );

  const handleTokenRemove = useCallback((pipelineId: string) => {
    setTokens((prev) => prev.filter((t) => t.pipelineId !== pipelineId));
  }, []);

  const handleHighlightChange = useCallback((index: number) => {
    setHighlightedIndex(index);
  }, []);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (!isAutocompleteOpen) return;

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setHighlightedIndex((prev) =>
          filteredPipelines.length > 0 ? (prev + 1) % filteredPipelines.length : 0
        );
        return;
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        setHighlightedIndex((prev) =>
          filteredPipelines.length > 0
            ? (prev - 1 + filteredPipelines.length) % filteredPipelines.length
            : 0
        );
        return;
      }
      if (e.key === 'Enter' || e.key === 'Tab') {
        if (filteredPipelines.length > 0 && highlightedIndex >= 0) {
          e.preventDefault();
          handleSelect(filteredPipelines[highlightedIndex].pipeline);
          return;
        }
      }
      if (e.key === 'Escape') {
        e.preventDefault();
        handleMentionDismiss();
        return;
      }
    },
    [isAutocompleteOpen, filteredPipelines, highlightedIndex, handleSelect, handleMentionDismiss]
  );

  // Re-validate tokens against pipeline list
  const validateTokens = useCallback((): boolean => {
    if (tokens.length === 0) return true;

    // If pipeline data hasn't loaded yet, trust the isValid state set at insertion time
    // rather than re-validating against an empty set (which would incorrectly block submission).
    if (!pipelineData) {
      return validTokens.length > 0;
    }

    const pipelineIds = new Set(pipelineData.pipelines.map((p) => p.id));
    const updatedTokens = tokens.map((t) => ({
      ...t,
      isValid: pipelineIds.has(t.pipelineId),
    }));
    setTokens(updatedTokens);

    // Also update token styling in the DOM
    const el = inputRef.current?.getElement();
    if (el) {
      const tokenSpans = el.querySelectorAll('[data-mention-token]');
      tokenSpans.forEach((span) => {
        const id = span.getAttribute('data-pipeline-id');
        const isValid = id ? pipelineIds.has(id) : false;
        if (isValid) {
          span.className = MENTION_TOKEN_VALID;
        } else {
          span.className = MENTION_TOKEN_INVALID;
        }
      });
    }

    return updatedTokens.some((t) => t.isValid);
  }, [tokens, pipelineData, validTokens, inputRef]);

  const getSubmissionPipelineId = useCallback((): string | null => {
    // Scan the DOM for token spans to get the last valid one
    const el = inputRef.current?.getElement();
    if (!el) return activePipelineId;

    const tokenSpans = el.querySelectorAll('[data-mention-token]');

    // If pipeline data is available, restrict to IDs the server knows about
    if (pipelineData?.pipelines) {
      const pipelineIds = new Set(pipelineData.pipelines.map((p) => p.id));
      let lastValidId: string | null = null;
      tokenSpans.forEach((span) => {
        const id = span.getAttribute('data-pipeline-id');
        if (id && pipelineIds.has(id)) {
          lastValidId = id;
        }
      });
      return lastValidId ?? activePipelineId;
    }

    // Pipeline data not yet loaded — use the id stored in the DOM span (set at insertion time)
    // and fall back to the last known valid token. The backend validates the final id anyway.
    let lastId: string | null = null;
    tokenSpans.forEach((span) => {
      const id = span.getAttribute('data-pipeline-id');
      if (id) lastId = id;
    });
    return lastId ?? activePipelineId;
  }, [inputRef, pipelineData, activePipelineId]);

  const getPlainTextContent = useCallback((): string => {
    return inputRef.current?.getPlainText() ?? '';
  }, [inputRef]);

  const clearTokens = useCallback(() => {
    setTokens([]);
    handleMentionDismiss();
  }, [handleMentionDismiss]);

  const reset = useCallback(() => {
    clearTokens();
    setHighlightedIndex(0);
    inputRef.current?.clear();
  }, [clearTokens, inputRef]);

  return {
    isAutocompleteOpen,
    filteredPipelines,
    highlightedIndex,
    isLoadingPipelines: isLoading,
    pipelineError,
    mentionTokens: tokens,
    activePipelineId,
    activePipelineName,
    hasMultipleMentions,
    hasInvalidMentions,
    handleMentionTrigger,
    handleMentionDismiss,
    handleSelect,
    handleTokenRemove,
    handleHighlightChange,
    handleKeyDown,
    validateTokens,
    getSubmissionPipelineId,
    getPlainTextContent,
    clearTokens,
    reset,
  };
}
