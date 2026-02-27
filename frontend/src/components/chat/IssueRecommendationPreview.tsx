/**
 * IssueRecommendationPreview Component
 *
 * Displays an AI-generated GitHub issue recommendation with all sections
 * (title, user story, UI/UX description, functional requirements) and
 * provides Confirm/Reject buttons for user action.
 */

import { useState } from 'react';
import type { IssueCreateActionData, WorkflowResult } from '@/types';

interface IssueRecommendationPreviewProps {
  recommendation: IssueCreateActionData;
  onConfirm: (recommendationId: string) => Promise<WorkflowResult>;
  onReject: (recommendationId: string) => Promise<void>;
}

export function IssueRecommendationPreview({
  recommendation,
  onConfirm,
  onReject,
}: IssueRecommendationPreviewProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<WorkflowResult | null>(null);

  const handleConfirm = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const workflowResult = await onConfirm(recommendation.recommendation_id);
      if (!workflowResult.success) {
        // Backend returned a structured error (HTTP 200 with success: false)
        setError(workflowResult.message || 'Failed to create issue');
        // Still store result so we can show partial success (issue created but agent failed)
        if (workflowResult.issue_number) {
          setResult(workflowResult);
        }
      } else {
        setResult(workflowResult);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create issue');
    } finally {
      setIsLoading(false);
    }
  };

  const handleReject = async () => {
    setIsLoading(true);
    setError(null);
    try {
      await onReject(recommendation.recommendation_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reject');
    } finally {
      setIsLoading(false);
    }
  };

  // Show success result
  if (result?.success) {
    return (
      <div className="bg-green-500/10 border border-green-500 rounded-lg p-4 mt-3 max-w-[600px]">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xl text-green-500">✓</span>
          <h4 className="m-0 font-semibold">Issue Created Successfully</h4>
        </div>
        <div className="text-sm">
          <p className="my-1">
            <strong>Issue #{result.issue_number}</strong>: {recommendation.proposed_title}
          </p>
          <p className="my-1">Status: {result.current_status}</p>
          {result.issue_url && (
            <a
              href={result.issue_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block mt-2 text-primary font-medium hover:underline"
            >
              View on GitHub →
            </a>
          )}
        </div>
      </div>
    );
  }

  // Show partial success: issue created but workflow had errors (e.g., agent assignment failed)
  if (result && !result.success && result.issue_number) {
    return (
      <div className="bg-amber-500/10 border border-amber-500 rounded-lg p-4 mt-3 max-w-[600px]">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xl text-amber-500">⚠</span>
          <h4 className="m-0 font-semibold">Issue Created with Warnings</h4>
        </div>
        <div className="text-sm">
          <p className="my-1">
            <strong>Issue #{result.issue_number}</strong>: {recommendation.proposed_title}
          </p>
          {result.issue_url && (
            <a
              href={result.issue_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block mt-2 text-primary font-medium hover:underline"
            >
              View on GitHub →
            </a>
          )}
          {error && <div className="bg-red-500/10 text-red-500 p-2 rounded-md text-sm mt-3">{error}</div>}
          <p className="mt-2 text-sm text-muted-foreground italic">
            The issue was created but the agent pipeline encountered an error.
            The system will automatically retry, or you can check the pipeline status.
          </p>
        </div>
      </div>
    );
  }

  // Show rejected state
  if (recommendation.status === 'rejected') {
    return (
      <div className="bg-red-500/10 border border-red-500 rounded-lg p-4 mt-3 max-w-[600px] opacity-70">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xl text-red-500">✗</span>
          <h4 className="m-0 font-semibold">Recommendation Rejected</h4>
        </div>
        <p className="text-muted-foreground line-through m-0">{recommendation.proposed_title}</p>
      </div>
    );
  }

  return (
    <div className="bg-muted/50 border border-border rounded-lg p-4 mt-3 max-w-[600px]">
      <div className="flex justify-between items-center mb-4 pb-2 border-b border-border">
        <h4 className="m-0 text-base font-semibold text-foreground">📝 Issue Recommendation</h4>
        <span className="text-xs px-2 py-0.5 rounded-full bg-primary text-primary-foreground capitalize">{recommendation.status}</span>
      </div>

      <div className="mb-3">
        <h5 className="text-sm text-muted-foreground m-0 mb-1 font-semibold">Title</h5>
        <p className="text-sm font-semibold text-foreground m-0">{recommendation.proposed_title}</p>
      </div>

      <div className="mb-3">
        <h5 className="text-sm text-muted-foreground m-0 mb-1 font-semibold">User Story</h5>
        <p className="text-sm text-foreground m-0 leading-relaxed">{recommendation.user_story}</p>
      </div>

      <div className="mb-3">
        <h5 className="text-sm text-muted-foreground m-0 mb-1 font-semibold">UI/UX Description</h5>
        <p className="text-sm text-foreground m-0 leading-relaxed">
          {recommendation.ui_ux_description.length > 300
            ? `${recommendation.ui_ux_description.substring(0, 300)}...`
            : recommendation.ui_ux_description}
        </p>
      </div>

      <div className="mb-3">
        <h5 className="text-sm text-muted-foreground m-0 mb-1 font-semibold">Functional Requirements</h5>
        <ul className="m-0 pl-5 text-sm text-foreground">
          {recommendation.functional_requirements.slice(0, 5).map((req, index) => (
            <li key={index} className="mb-1">{req}</li>
          ))}
          {recommendation.functional_requirements.length > 5 && (
            <li className="text-muted-foreground italic">
              ... and {recommendation.functional_requirements.length - 5} more
            </li>
          )}
        </ul>
      </div>

      {recommendation.metadata && (
        <div className="bg-background rounded-lg p-3 mb-3">
          <h5 className="text-sm text-muted-foreground m-0 mb-1 font-semibold">📊 Metadata</h5>
          <div className="grid grid-cols-[repeat(auto-fit,minmax(100px,1fr))] gap-3">
            <div className="flex flex-col gap-1">
              <span className="text-[11px] uppercase text-muted-foreground font-medium">Priority</span>
              <span className={`text-sm font-medium ${recommendation.metadata.priority === 'P0' ? 'text-red-500 font-bold' : recommendation.metadata.priority === 'P1' ? 'text-orange-500 font-semibold' : recommendation.metadata.priority === 'P2' ? 'text-blue-500' : 'text-muted-foreground'}`}>
                {recommendation.metadata.priority || 'P2'}
              </span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-[11px] uppercase text-muted-foreground font-medium">Size</span>
              <span className="inline-block px-2 py-0.5 bg-muted rounded text-xs font-medium w-fit">
                {recommendation.metadata.size || 'M'}
              </span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-[11px] uppercase text-muted-foreground font-medium">Estimate</span>
              <span className="text-sm font-medium text-foreground">
                {recommendation.metadata.estimate_hours || 4}h
              </span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-[11px] uppercase text-muted-foreground font-medium">Start</span>
              <span className="text-sm font-medium text-foreground">
                {recommendation.metadata.start_date || 'TBD'}
              </span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-[11px] uppercase text-muted-foreground font-medium">Target</span>
              <span className="text-sm font-medium text-foreground">
                {recommendation.metadata.target_date || 'TBD'}
              </span>
            </div>
            {recommendation.metadata.labels && recommendation.metadata.labels.length > 0 && (
              <div className="col-span-2 flex flex-col gap-1">
                <span className="text-[11px] uppercase text-muted-foreground font-medium">Labels</span>
                <div className="flex flex-wrap gap-1.5">
                  {recommendation.metadata.labels.map((label, idx) => (
                    <span key={idx} className="inline-block px-2 py-0.5 bg-blue-500/10 text-blue-500 rounded-full text-[11px] font-medium">{label}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {error && <div className="bg-red-500/10 text-red-500 p-2 rounded-md text-sm mt-3">{error}</div>}

      <div className="flex gap-3 mt-4 pt-3 border-t border-border">
        <button
          className="flex-1 py-2.5 px-4 rounded-lg text-sm font-medium cursor-pointer transition-colors bg-green-500 text-white border-none hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed"
          onClick={handleConfirm}
          disabled={isLoading || recommendation.status !== 'pending'}
        >
          {isLoading ? 'Creating...' : '✓ Confirm & Create Issue'}
        </button>
        <button
          className="flex-1 py-2.5 px-4 rounded-lg text-sm font-medium cursor-pointer transition-colors bg-transparent text-red-500 border border-red-500 hover:bg-red-500/10 disabled:opacity-50 disabled:cursor-not-allowed"
          onClick={handleReject}
          disabled={isLoading || recommendation.status !== 'pending'}
        >
          {isLoading ? 'Rejecting...' : '✗ Reject'}
        </button>
      </div>
    </div>
  );
}
