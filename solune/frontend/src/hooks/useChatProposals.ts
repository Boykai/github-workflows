/**
 * useChatProposals — manages pending task proposals, status changes,
 * and issue recommendations extracted from chat responses.
 */

import { useCallback, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { PROPOSAL_EXPIRY_MS } from '@/constants';
import { chatApi, tasksApi } from '@/services/api';
import type {
  AITaskProposal,
  ChatMessage,
  IssueCreateActionData,
  ProposalConfirmRequest,
  StatusChangeProposal,
  TaskCreateActionData,
  StatusUpdateActionData,
} from '@/types';

export function useChatProposals() {
  const queryClient = useQueryClient();
  const [pendingProposals, setPendingProposals] = useState<Map<string, AITaskProposal>>(new Map());
  const [pendingStatusChanges, setPendingStatusChanges] = useState<
    Map<string, StatusChangeProposal>
  >(new Map());
  const [pendingRecommendations, setPendingRecommendations] = useState<
    Map<string, IssueCreateActionData>
  >(new Map());

  const handleActionResponse = useCallback((response: ChatMessage) => {
    if (response.action_type === 'task_create' && response.action_data) {
      const data = response.action_data as TaskCreateActionData;
      if (data.proposal_id && data.status === 'pending') {
        const proposal: AITaskProposal = {
          proposal_id: data.proposal_id,
          session_id: response.session_id,
          original_input: '',
          proposed_title: data.proposed_title || '',
          proposed_description: data.proposed_description || '',
          status: 'pending',
          created_at: new Date().toISOString(),
          expires_at: new Date(Date.now() + PROPOSAL_EXPIRY_MS).toISOString(),
        };
        setPendingProposals((prev) => new Map(prev).set(proposal.proposal_id, proposal));
      }
    }

    if (response.action_type === 'status_update' && response.action_data) {
      const data = response.action_data as StatusUpdateActionData;
      if (data.proposal_id && data.task_id && data.status === 'pending') {
        const statusChange: StatusChangeProposal = {
          proposal_id: data.proposal_id,
          task_id: data.task_id,
          task_title: data.task_title || '',
          current_status: data.current_status || '',
          target_status: data.target_status || '',
          status_option_id: data.status_option_id || '',
          status_field_id: data.status_field_id || '',
          status: data.status || '',
        };
        setPendingStatusChanges((prev) =>
          new Map(prev).set(statusChange.proposal_id, statusChange),
        );
      }
    }

    if (response.action_type === 'issue_create' && response.action_data) {
      const data = response.action_data as IssueCreateActionData;
      if (data.recommendation_id && data.status === 'pending') {
        setPendingRecommendations((prev) =>
          new Map(prev).set(data.recommendation_id, { ...data, status: 'pending' }),
        );
      }
    }
  }, []);

  const confirmMutation = useMutation({
    mutationFn: ({ proposalId, data }: { proposalId: string; data?: ProposalConfirmRequest }) =>
      chatApi.confirmProposal(proposalId, data),
    onSuccess: (_, variables) => {
      setPendingProposals((prev) => {
        const next = new Map(prev);
        next.delete(variables.proposalId);
        return next;
      });
      queryClient.invalidateQueries({ queryKey: ['chat', 'messages'] });
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });

  const statusChangeMutation = useMutation({
    mutationFn: async (proposalId: string) => {
      const statusChange = pendingStatusChanges.get(proposalId);
      if (!statusChange) throw new Error('No pending status change found');
      return tasksApi.updateStatus(statusChange.task_id, statusChange.target_status);
    },
    onSuccess: (_, proposalId) => {
      setPendingStatusChanges((prev) => {
        const next = new Map(prev);
        next.delete(proposalId);
        return next;
      });
      queryClient.invalidateQueries({ queryKey: ['chat', 'messages'] });
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });

  const cancelMutation = useMutation({
    mutationFn: chatApi.cancelProposal,
    onSuccess: (_, proposalId) => {
      setPendingProposals((prev) => {
        const next = new Map(prev);
        next.delete(proposalId);
        return next;
      });
      setPendingStatusChanges((prev) => {
        const next = new Map(prev);
        next.delete(proposalId);
        return next;
      });
      queryClient.invalidateQueries({ queryKey: ['chat', 'messages'] });
    },
  });

  const confirmProposal = useCallback(
    async (proposalId: string, edits?: ProposalConfirmRequest) => {
      await confirmMutation.mutateAsync({ proposalId, data: edits });
    },
    [confirmMutation],
  );

  const confirmStatusChange = useCallback(
    async (proposalId: string) => {
      await statusChangeMutation.mutateAsync(proposalId);
    },
    [statusChangeMutation],
  );

  const rejectProposal = useCallback(
    async (proposalId: string) => {
      await cancelMutation.mutateAsync(proposalId);
    },
    [cancelMutation],
  );

  const removePendingRecommendation = useCallback((recommendationId: string) => {
    setPendingRecommendations((prev) => {
      const next = new Map(prev);
      next.delete(recommendationId);
      return next;
    });
  }, []);

  const clearProposals = useCallback(() => {
    setPendingProposals(new Map());
    setPendingStatusChanges(new Map());
    setPendingRecommendations(new Map());
  }, []);

  return {
    pendingProposals,
    pendingStatusChanges,
    pendingRecommendations,
    handleActionResponse,
    confirmProposal,
    confirmStatusChange,
    rejectProposal,
    removePendingRecommendation,
    clearProposals,
  };
}
