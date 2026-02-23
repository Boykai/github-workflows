/**
 * Chat hook for managing messages and proposals.
 */

import { useCallback, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { STALE_TIME_SHORT, PROPOSAL_EXPIRY_MS } from '@/constants';
import { chatApi, tasksApi } from '@/services/api';
import type { AITaskProposal, ChatMessage, ProposalConfirmRequest, IssueCreateActionData, StatusChangeProposal } from '@/types';

interface UseChatReturn {
  messages: ChatMessage[];
  isLoading: boolean;
  isSending: boolean;
  error: Error | null;
  pendingProposals: Map<string, AITaskProposal>;
  pendingStatusChanges: Map<string, StatusChangeProposal>;
  pendingRecommendations: Map<string, IssueCreateActionData>;
  sendMessage: (content: string) => Promise<void>;
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

  // Fetch messages
  const {
    data: messagesData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['chat', 'messages'],
    queryFn: chatApi.getMessages,
    staleTime: STALE_TIME_SHORT,
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
    async (content: string) => {
      await sendMutation.mutateAsync({ content });
    },
    [sendMutation]
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
      // Refetch messages (will be empty)
      queryClient.invalidateQueries({ queryKey: ['chat', 'messages'] });
    },
  });

  const clearChat = useCallback(async () => {
    await clearChatMutation.mutateAsync();
  }, [clearChatMutation]);

  return {
    messages: messagesData?.messages ?? [],
    isLoading,
    isSending: sendMutation.isPending,
    error: error as Error | null,
    pendingProposals,
    pendingStatusChanges,
    pendingRecommendations,
    sendMessage,
    confirmProposal,
    confirmStatusChange,
    rejectProposal,
    removePendingRecommendation,
    clearChat,
  };
}
