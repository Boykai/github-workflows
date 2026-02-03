/**
 * IssueRecommendationPreview Component
 *
 * Displays an AI-generated GitHub issue recommendation with all sections
 * (title, user story, UI/UX description, functional requirements) and
 * provides Confirm/Reject buttons for user action.
 */

import { useState } from 'react';
import type { IssueCreateActionData, WorkflowResult } from '../../types';
import './ChatInterface.css';

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
      setResult(workflowResult);
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
      <div className="issue-recommendation-preview success">
        <div className="result-header">
          <span className="success-icon">✓</span>
          <h4>Issue Created Successfully</h4>
        </div>
        <div className="result-details">
          <p>
            <strong>Issue #{result.issue_number}</strong>: {recommendation.proposed_title}
          </p>
          <p>Status: {result.current_status}</p>
          {result.issue_url && (
            <a
              href={result.issue_url}
              target="_blank"
              rel="noopener noreferrer"
              className="issue-link"
            >
              View on GitHub →
            </a>
          )}
        </div>
      </div>
    );
  }

  // Show rejected state
  if (recommendation.status === 'rejected') {
    return (
      <div className="issue-recommendation-preview rejected">
        <div className="result-header">
          <span className="rejected-icon">✗</span>
          <h4>Recommendation Rejected</h4>
        </div>
        <p className="rejected-title">{recommendation.proposed_title}</p>
      </div>
    );
  }

  return (
    <div className="issue-recommendation-preview">
      <div className="recommendation-header">
        <h4>📝 Issue Recommendation</h4>
        <span className="status-badge">{recommendation.status}</span>
      </div>

      <div className="recommendation-section">
        <h5>Title</h5>
        <p className="recommendation-title">{recommendation.proposed_title}</p>
      </div>

      <div className="recommendation-section">
        <h5>User Story</h5>
        <p className="user-story">{recommendation.user_story}</p>
      </div>

      <div className="recommendation-section">
        <h5>UI/UX Description</h5>
        <p className="ui-ux-description">
          {recommendation.ui_ux_description.length > 300
            ? `${recommendation.ui_ux_description.substring(0, 300)}...`
            : recommendation.ui_ux_description}
        </p>
      </div>

      <div className="recommendation-section">
        <h5>Functional Requirements</h5>
        <ul className="requirements-list">
          {recommendation.functional_requirements.slice(0, 5).map((req, index) => (
            <li key={index}>{req}</li>
          ))}
          {recommendation.functional_requirements.length > 5 && (
            <li className="more-items">
              ... and {recommendation.functional_requirements.length - 5} more
            </li>
          )}
        </ul>
      </div>

      {recommendation.metadata && (
        <div className="recommendation-section metadata-section">
          <h5>📊 Metadata</h5>
          <div className="metadata-grid">
            <div className="metadata-item">
              <span className="metadata-label">Priority</span>
              <span className={`metadata-value priority-${recommendation.metadata.priority?.toLowerCase()}`}>
                {recommendation.metadata.priority || 'P2'}
              </span>
            </div>
            <div className="metadata-item">
              <span className="metadata-label">Size</span>
              <span className="metadata-value size-badge">
                {recommendation.metadata.size || 'M'}
              </span>
            </div>
            <div className="metadata-item">
              <span className="metadata-label">Estimate</span>
              <span className="metadata-value">
                {recommendation.metadata.estimate_hours || 4}h
              </span>
            </div>
            <div className="metadata-item">
              <span className="metadata-label">Start</span>
              <span className="metadata-value">
                {recommendation.metadata.start_date || 'TBD'}
              </span>
            </div>
            <div className="metadata-item">
              <span className="metadata-label">Target</span>
              <span className="metadata-value">
                {recommendation.metadata.target_date || 'TBD'}
              </span>
            </div>
            {recommendation.metadata.labels && recommendation.metadata.labels.length > 0 && (
              <div className="metadata-item labels-item">
                <span className="metadata-label">Labels</span>
                <div className="labels-list">
                  {recommendation.metadata.labels.map((label, idx) => (
                    <span key={idx} className="label-badge">{label}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {error && <div className="error-message">{error}</div>}

      <div className="recommendation-actions">
        <button
          className="confirm-button"
          onClick={handleConfirm}
          disabled={isLoading || recommendation.status !== 'pending'}
        >
          {isLoading ? 'Creating...' : '✓ Confirm & Create Issue'}
        </button>
        <button
          className="reject-button"
          onClick={handleReject}
          disabled={isLoading || recommendation.status !== 'pending'}
        >
          {isLoading ? 'Rejecting...' : '✗ Reject'}
        </button>
      </div>
    </div>
  );
}

export default IssueRecommendationPreview;
