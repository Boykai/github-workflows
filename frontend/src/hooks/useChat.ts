/**
 * Chat hook for managing messages and proposals.
 */

import { useCallback, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { STALE_TIME_MEDIUM, PROPOSAL_EXPIRY_MS } from '@/constants';
import { chatApi, tasksApi } from '@/services/api';
import type { AITaskProposal, ChatMessage, ProposalConfirmRequest, IssueCreateActionData, StatusChangeProposal } from '@/types';
import { useCommands } from '@/hooks/useCommands';
import { generateId } from '@/utils/generateId';

interface UseChatReturn {
  messages: ChatMessage[];
  isLoading: boolean;
  isSending: boolean;
  error: Error | null;
  pendingProposals: Map<string, AITaskProposal>;
  pendingStatusChanges: Map<string, StatusChangeProposal>;
  pendingRecommendations: Map<string, IssueCreateActionData>;
  sendMessage: (content: string, options?: { isCommand?: boolean }) => Promise<void>;
  retryMessage: (messageId: string) => Promise<void>;
  confirmProposal: (proposalId: string, edits?: ProposalConfirmRequest) => Promise<void>;
  confirmStatusChange: (proposalId: string) => Promise<void>;
  rejectProposal: (proposalId: string) => Promise<void>;
  removePendingRecommendation: (recommendationId: string) => void;
  clearChat: () => Promise<void>;
}

export function useChat(): UseChatReturn {
  const queryClient = useQueryClient();
  const [pendingProposals, setPendingProposals] = useState<Map<string, AITaskProposal>>(new Map());
  const [pendingStatusChanges, setPendingStatusChanges] = useState<Map<string, StatusChangeProposal>>(new Map());
  const [pendingRecommendations, setPendingRecommendations] = useState<Map<string, IssueCreateActionData>>(new Map());
  const [localMessages, setLocalMessages] = useState<ChatMessage[]>([]);
  const { isCommand, executeCommand } = useCommands();

  // Fetch messages
  const {
    data: messagesData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['chat', 'messages'],
    queryFn: chatApi.getMessages,
    staleTime: STALE_TIME_MEDIUM,
  });

  // Send message mutation
  const sendMutation = useMutation({
    mutationFn: chatApi.sendMessage,
    onSuccess: (response) => {
      // Check if response contains a task creation proposal
      if (response.action_type === 'task_create' && response.action_data) {
        const data = response.action_data as unknown as Record<string, unknown>;
        if ('proposal_id' in data && data.status === 'pending') {
          const proposal: AITaskProposal = {
            proposal_id: data.proposal_id as string,
            session_id: response.session_id,
            original_input: '',
            proposed_title: data.proposed_title as string || '',
            proposed_description: data.proposed_description as string || '',
            status: 'pending',
            created_at: new Date().toISOString(),
            expires_at: new Date(Date.now() + PROPOSAL_EXPIRY_MS).toISOString(),
          };
          setPendingProposals(prev => new Map(prev).set(proposal.proposal_id, proposal));
        }
      }
      
      // Check if response contains a status change proposal (T052)
      if (response.action_type === 'status_update' && response.action_data) {
        const data = response.action_data as unknown as Record<string, unknown>;
        if ('task_id' in data && data.status === 'pending') {
          const statusChange: StatusChangeProposal = {
            proposal_id: data.proposal_id as string,
            task_id: data.task_id as string,
            task_title: data.task_title as string,
            current_status: data.current_status as string,
            target_status: data.target_status as string,
            status_option_id: data.status_option_id as string,
            status_field_id: data.status_field_id as string,
            status: data.status as string,
          };
          setPendingStatusChanges(prev => new Map(prev).set(statusChange.proposal_id, statusChange));
        }
      }

      // Check if response contains an issue recommendation (issue_create)
      if (response.action_type === 'issue_create' && response.action_data) {
        const data = response.action_data as unknown as Record<string, unknown>;
        if ('recommendation_id' in data && data.status === 'pending') {
          const recommendation: IssueCreateActionData = {
            recommendation_id: data.recommendation_id as string,
            proposed_title: data.proposed_title as string,
            user_story: data.user_story as string,
            ui_ux_description: data.ui_ux_description as string,
            functional_requirements: data.functional_requirements as string[],
            status: 'pending',
          };
          setPendingRecommendations(prev => new Map(prev).set(recommendation.recommendation_id, recommendation));
        }
      }
      
      // Refetch messages
      queryClient.invalidateQueries({ queryKey: ['chat', 'messages'] });
    },
  });

  // Confirm task creation proposal mutation
  const confirmMutation = useMutation({
    mutationFn: ({ proposalId, data }: { proposalId: string; data?: ProposalConfirmRequest }) =>
      chatApi.confirmProposal(proposalId, data),
    onSuccess: (_, variables) => {
      setPendingProposals(prev => {
        const next = new Map(prev);
        next.delete(variables.proposalId);
        return next;
      });
      queryClient.invalidateQueries({ queryKey: ['chat', 'messages'] });
      // Also refresh tasks
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });

  // Confirm status change mutation (T052)
  const statusChangeMutation = useMutation({
    mutationFn: async (proposalId: string) => {
      const statusChange = pendingStatusChanges.get(proposalId);
      if (!statusChange) throw new Error('No pending status change found');
      
      return tasksApi.updateStatus(
        statusChange.task_id,
        statusChange.target_status
      );
    },
    onSuccess: (_, proposalId) => {
      setPendingStatusChanges(prev => {
        const next = new Map(prev);
        next.delete(proposalId);
        return next;
      });
      queryClient.invalidateQueries({ queryKey: ['chat', 'messages'] });
      // Refresh tasks to show updated status
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });

  // Cancel proposal mutation
  const cancelMutation = useMutation({
    mutationFn: chatApi.cancelProposal,
    onSuccess: (_, proposalId) => {
      setPendingProposals(prev => {
        const next = new Map(prev);
        next.delete(proposalId);
        return next;
      });
      setPendingStatusChanges(prev => {
        const next = new Map(prev);
        next.delete(proposalId);
        return next;
      });
      queryClient.invalidateQueries({ queryKey: ['chat', 'messages'] });
    },
  });

  const sendMessage = useCallback(
    async (content: string, options?: { isCommand?: boolean }) => {
      // Evaluate command status fresh from the content parameter only —
      // no stored state or previous options are referenced.
      const isCmd = options?.isCommand || isCommand(content);

      // ── Command path (early return) ──────────────────────────────────
      if (isCmd) {
        try {
          const result = await executeCommand(content);

          if (result.passthrough) {
            // Forward to backend API — the backend handles the full flow
            await sendMutation.mutateAsync({ content });
            return;
          }

          // Local command — add user message and system response
          const userMsg: ChatMessage = {
            message_id: generateId(),
            session_id: 'local',
            sender_type: 'user',
            content,
            timestamp: new Date().toISOString(),
          };
          const systemMsg: ChatMessage = {
            message_id: generateId(),
            session_id: 'local',
            sender_type: 'system',
            content: result.message,
            timestamp: new Date().toISOString(),
          };
          setLocalMessages((prev) => [...prev, userMsg, systemMsg]);
        } catch (error) {
          // Surface the failure as a system message so the user sees it
          const errorMessage =
            error instanceof Error && error.message
              ? `Command failed: ${error.message}`
              : 'Command failed due to an unexpected error.';

          const userMsg: ChatMessage = {
            message_id: generateId(),
            session_id: 'local',
            sender_type: 'user',
            content,
            timestamp: new Date().toISOString(),
          };
          const systemErrorMsg: ChatMessage = {
            message_id: generateId(),
            session_id: 'local',
            sender_type: 'system',
            content: errorMessage,
            timestamp: new Date().toISOString(),
          };
          setLocalMessages((prev) => [...prev, userMsg, systemErrorMsg]);
        }
        // Command fully consumed — early return prevents any state leakage
        return;
      }

      // ── Regular message path (optimistic rendering) ──────────────────
      const tempId = generateId();
      const optimisticMsg: ChatMessage = {
        message_id: tempId,
        session_id: 'local',
        sender_type: 'user',
        content,
        timestamp: new Date().toISOString(),
        status: 'pending',
      };
      setLocalMessages((prev) => [...prev, optimisticMsg]);

      try {
        await sendMutation.mutateAsync({ content });
        // On success, remove the optimistic message — server data will
        // replace it after invalidateQueries fires in the mutation's onSuccess.
        setLocalMessages((prev) => prev.filter((m) => m.message_id !== tempId));
      } catch {
        // Mark the optimistic message as failed so the UI can show retry
        setLocalMessages((prev) =>
          prev.map((m) => (m.message_id === tempId ? { ...m, status: 'failed' as const } : m))
        );
      }
    },
    [sendMutation, isCommand, executeCommand]
  );

  const retryMessage = useCallback(
    async (messageId: string) => {
      const failedMsg = localMessages.find((m) => m.message_id === messageId && m.status === 'failed');
      if (!failedMsg) return;

      // Reset to pending
      setLocalMessages((prev) =>
        prev.map((m) => (m.message_id === messageId ? { ...m, status: 'pending' as const } : m))
      );

      try {
        await sendMutation.mutateAsync({ content: failedMsg.content });
        setLocalMessages((prev) => prev.filter((m) => m.message_id !== messageId));
      } catch {
        setLocalMessages((prev) =>
          prev.map((m) => (m.message_id === messageId ? { ...m, status: 'failed' as const } : m))
        );
      }
    },
    [localMessages, sendMutation]
  );

  const confirmProposal = useCallback(
    async (proposalId: string, edits?: ProposalConfirmRequest) => {
      await confirmMutation.mutateAsync({ proposalId, data: edits });
    },
    [confirmMutation]
  );

  const confirmStatusChange = useCallback(async (proposalId: string) => {
    await statusChangeMutation.mutateAsync(proposalId);
  }, [statusChangeMutation]);

  const rejectProposal = useCallback(
    async (proposalId: string) => {
      await cancelMutation.mutateAsync(proposalId);
    },
    [cancelMutation]
  );

  const removePendingRecommendation = useCallback((recommendationId: string) => {
    setPendingRecommendations(prev => {
      const next = new Map(prev);
      next.delete(recommendationId);
      return next;
    });
  }, []);

  // Clear chat mutation
  const clearChatMutation = useMutation({
    mutationFn: chatApi.clearMessages,
    onSuccess: () => {
      // Clear all local state
      setPendingProposals(new Map());
      setPendingStatusChanges(new Map());
      setPendingRecommendations(new Map());
      setLocalMessages([]);
      // Refetch messages (will be empty)
      queryClient.invalidateQueries({ queryKey: ['chat', 'messages'] });
    },
  });

  const clearChat = useCallback(async () => {
    await clearChatMutation.mutateAsync();
  }, [clearChatMutation]);

  return {
    messages: [...(messagesData?.messages ?? []), ...localMessages],
    isLoading,
    isSending: sendMutation.isPending,
    error: error as Error | null,
    pendingProposals,
    pendingStatusChanges,
    pendingRecommendations,
    sendMessage,
    retryMessage,
    confirmProposal,
    confirmStatusChange,
    rejectProposal,
    removePendingRecommendation,
    clearChat,
  };
}
