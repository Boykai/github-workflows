/**
 * CleanUpConfirmModal — displays categorized lists of branches/PRs
 * scheduled for deletion and preservation, with confirm/cancel actions.
 * Items link out to GitHub and can be toggled between delete/preserve.
 */

import { useEffect, useCallback, useState } from 'react';
import { createPortal } from 'react-dom';
import {
  ExternalLink,
  GitBranch,
  GitPullRequest,
  Shield,
  ShieldOff,
  Trash2,
  X,
} from '@/lib/icons';
import type {
  CleanupPreflightResponse,
  CleanupConfirmPayload,
  BranchInfo,
  PullRequestInfo,
  OrphanedIssueInfo,
  IssueInfo,
} from '@/types';
import { useScrollLock } from '@/hooks/useScrollLock';

interface CleanUpConfirmModalProps {
  data: CleanupPreflightResponse;
  owner: string;
  repo: string;
  onConfirm: (payload: CleanupConfirmPayload) => void;
  onCancel: () => void;
}

export function CleanUpConfirmModal({
  data,
  owner,
  repo,
  onConfirm,
  onCancel,
}: CleanUpConfirmModalProps) {
  // Track which items the user has toggled away from their default category.
  // Sets hold identifiers: branch name, `pr:${number}`, or `issue:${number}`.
  const [preserved, setPreserved] = useState<Set<string>>(new Set());
  const [markedForDeletion, setMarkedForDeletion] = useState<Set<string>>(new Set());

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') onCancel();
    },
    [onCancel]
  );

  useScrollLock(true);

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleKeyDown]);

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) onCancel();
  };

  // Toggle helpers
  const togglePreserve = (key: string) => {
    setPreserved((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const toggleMarkForDeletion = (key: string) => {
    setMarkedForDeletion((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  // Batch toggle helpers
  const toggleAllInDeleteSection = (keys: string[]) => {
    setPreserved((prev) => {
      const next = new Set(prev);
      const allPreserved = keys.length > 0 && keys.every((k) => next.has(k));
      if (allPreserved) {
        keys.forEach((k) => next.delete(k));
      } else {
        keys.forEach((k) => next.add(k));
      }
      return next;
    });
  };

  const toggleAllInPreserveSection = (keys: string[], excludeKeys: string[] = []) => {
    const excluded = new Set(excludeKeys);
    const eligible = keys.filter((k) => !excluded.has(k));
    setMarkedForDeletion((prev) => {
      const next = new Set(prev);
      const allMarked = eligible.length > 0 && eligible.every((k) => next.has(k));
      if (allMarked) {
        eligible.forEach((k) => next.delete(k));
      } else {
        eligible.forEach((k) => next.add(k));
      }
      return next;
    });
  };

  // Compute final lists
  const finalBranchesToDelete = data.branches_to_delete.filter((b) => !preserved.has(b.name));
  const finalPrsToClose = data.prs_to_close.filter((p) => !preserved.has(`pr:${p.number}`));
  const finalIssuesToClose = (data.orphaned_issues ?? []).filter(
    (i) => !preserved.has(`issue:${i.number}`)
  );
  const finalBranchesToDeleteFromPreserve = data.branches_to_preserve.filter(
    (b) => markedForDeletion.has(b.name) && b.name !== 'main'
  );
  const finalPrsToCloseFromPreserve = data.prs_to_preserve.filter((p) =>
    markedForDeletion.has(`pr:${p.number}`)
  );
  const finalIssuesToDeleteFromPreserve = (data.issues_to_preserve ?? []).filter(
    (i) => markedForDeletion.has(`issue:${i.number}`)
  );

  const hasItemsToDelete =
    finalBranchesToDelete.length > 0 ||
    finalPrsToClose.length > 0 ||
    finalIssuesToClose.length > 0 ||
    finalBranchesToDeleteFromPreserve.length > 0 ||
    finalPrsToCloseFromPreserve.length > 0 ||
    finalIssuesToDeleteFromPreserve.length > 0;

  const handleConfirm = () => {
    onConfirm({
      branches_to_delete: [
        ...finalBranchesToDelete.map((b) => b.name),
        ...finalBranchesToDeleteFromPreserve.map((b) => b.name),
      ],
      prs_to_close: [
        ...finalPrsToClose.map((p) => p.number),
        ...finalPrsToCloseFromPreserve.map((p) => p.number),
      ],
      issues_to_delete: [
        ...finalIssuesToClose
          .filter((i) => i.node_id != null)
          .map((i) => ({ number: i.number, node_id: i.node_id! })),
        ...finalIssuesToDeleteFromPreserve
          .filter((i) => i.node_id != null)
          .map((i) => ({ number: i.number, node_id: i.node_id! })),
      ],
    });
  };

  // URL builders
  const ghBase = `https://github.com/${owner}/${repo}`;
  const branchUrl = (name: string) => `${ghBase}/tree/${encodeURIComponent(name)}`;
  const prUrl = (num: number) => `${ghBase}/pull/${num}`;
  const issueUrl = (issue: OrphanedIssueInfo | IssueInfo) => issue.html_url || `${ghBase}/issues/${issue.number}`;

  // Section key arrays and derived toggle states
  const issueKeys = (data.orphaned_issues ?? []).map((i) => `issue:${i.number}`);
  const branchDeleteKeys = data.branches_to_delete.map((b) => b.name);
  const prCloseKeys = data.prs_to_close.map((p) => `pr:${p.number}`);
  const branchPreserveKeys = data.branches_to_preserve.map((b) => b.name);
  const prPreserveKeys = data.prs_to_preserve.map((p) => `pr:${p.number}`);
  const issuePreserveKeys = (data.issues_to_preserve ?? []).map((i) => `issue:${i.number}`);

  const allIssuesPreserved = issueKeys.length > 0 && issueKeys.every((k) => preserved.has(k));
  const allBranchesDeletePreserved =
    branchDeleteKeys.length > 0 && branchDeleteKeys.every((k) => preserved.has(k));
  const allPrsClosePreserved =
    prCloseKeys.length > 0 && prCloseKeys.every((k) => preserved.has(k));
  const branchPreserveEligible = data.branches_to_preserve.filter((b) => b.name !== 'main');
  const allBranchesPreserveMarked =
    branchPreserveEligible.length > 0 &&
    branchPreserveEligible.every((b) => markedForDeletion.has(b.name));
  const allPrsPreserveMarked =
    prPreserveKeys.length > 0 && prPreserveKeys.every((k) => markedForDeletion.has(k));
  const allIssuesPreserveMarked =
    issuePreserveKeys.length > 0 && issuePreserveKeys.every((k) => markedForDeletion.has(k));

  return createPortal(
    <div
      className="fixed inset-0 z-[2000] flex items-center justify-center bg-background/80 backdrop-blur-sm"
      role="none"
      onClick={handleBackdropClick}
    >
      <div
        className="celestial-fade-in celestial-panel relative m-4 w-full max-w-2xl max-h-[85vh] overflow-y-auto rounded-[1.4rem] border border-border p-6 text-card-foreground shadow-lg"
        role="dialog"
        aria-modal="true"
        aria-label="Confirm Repository Cleanup"
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Confirm Repository Cleanup</h2>
          <button
            onClick={onCancel}
            className="rounded-md p-1 text-muted-foreground transition-colors hover:bg-primary/10 hover:text-foreground"
            aria-label="Close"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <p className="text-sm text-muted-foreground mb-4">
          Review the Solune-generated items below before confirming. Assets created outside the app
          will be preserved. This operation cannot be undone.
        </p>

        {/* ─── Orphaned Issues to Delete ─── */}
        {(data.orphaned_issues ?? []).length > 0 && (
          <section className="mb-4">
            <h3 className="text-sm font-medium text-destructive mb-2">
              <button
                type="button"
                className="inline-flex items-center gap-2 cursor-pointer select-none hover:opacity-80 transition-opacity"
                onClick={() => toggleAllInDeleteSection(issueKeys)}
                aria-label="Toggle all orphaned issues"
              >
                <Trash2 className="h-4 w-4" />
                Orphaned Issues to Delete ({data.orphaned_issues.length})
                {allIssuesPreserved ? (
                  <Shield className="h-3.5 w-3.5 text-green-600 dark:text-green-400" />
                ) : (
                  <ShieldOff className="h-3.5 w-3.5 text-destructive" />
                )}
              </button>
            </h3>
            <p className="text-xs text-muted-foreground mb-2">
              App-created issues no longer attached to the project board. These will be permanently
              deleted from GitHub.
            </p>
            <ul className="space-y-1 text-sm">
              {data.orphaned_issues.map((issue) => {
                const key = `issue:${issue.number}`;
                const isPreserved = preserved.has(key);
                return (
                  <li
                    key={issue.number}
                    className={`flex items-center gap-2 px-2 py-1.5 rounded transition-colors ${isPreserved ? 'bg-green-100/80 dark:bg-green-900/30' : 'bg-destructive/10'}`}
                  >
                    <ToggleButton
                      willDelete={!isPreserved}
                      onClick={() => togglePreserve(key)}
                    />
                    <a
                      href={issueUrl(issue)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 min-w-0 flex-1 hover:underline"
                    >
                      <span className="font-medium shrink-0">#{issue.number}</span>
                      <span className="text-muted-foreground truncate">{issue.title}</span>
                      {issue.labels.length > 0 && (
                        <span className="text-xs text-muted-foreground shrink-0">
                          [{issue.labels.join(', ')}]
                        </span>
                      )}
                      <ExternalLink className="h-3 w-3 shrink-0 text-muted-foreground" />
                    </a>
                  </li>
                );
              })}
            </ul>
          </section>
        )}

        {/* ─── Branches to Delete ─── */}
        {data.branches_to_delete.length > 0 && (
          <section className="mb-4">
            <h3 className="text-sm font-medium text-destructive mb-2">
              <button
                type="button"
                className="inline-flex items-center gap-2 cursor-pointer select-none hover:opacity-80 transition-opacity"
                onClick={() => toggleAllInDeleteSection(branchDeleteKeys)}
                aria-label="Toggle all branches to delete"
              >
                <Trash2 className="h-4 w-4" />
                Branches to Delete ({data.branches_to_delete.length})
                {allBranchesDeletePreserved ? (
                  <Shield className="h-3.5 w-3.5 text-green-600 dark:text-green-400" />
                ) : (
                  <ShieldOff className="h-3.5 w-3.5 text-destructive" />
                )}
              </button>
            </h3>
            <ul className="space-y-1 text-sm">
              {data.branches_to_delete.map((branch) => {
                const isPreserved = preserved.has(branch.name);
                return (
                  <BranchRow
                    key={branch.name}
                    branch={branch}
                    url={branchUrl(branch.name)}
                    willDelete={!isPreserved}
                    onToggle={() => togglePreserve(branch.name)}
                  />
                );
              })}
            </ul>
          </section>
        )}

        {/* ─── PRs to Close ─── */}
        {data.prs_to_close.length > 0 && (
          <section className="mb-4">
            <h3 className="text-sm font-medium text-destructive mb-2">
              <button
                type="button"
                className="inline-flex items-center gap-2 cursor-pointer select-none hover:opacity-80 transition-opacity"
                onClick={() => toggleAllInDeleteSection(prCloseKeys)}
                aria-label="Toggle all pull requests to close"
              >
                <Trash2 className="h-4 w-4" />
                Pull Requests to Close ({data.prs_to_close.length})
                {allPrsClosePreserved ? (
                  <Shield className="h-3.5 w-3.5 text-green-600 dark:text-green-400" />
                ) : (
                  <ShieldOff className="h-3.5 w-3.5 text-destructive" />
                )}
              </button>
            </h3>
            <ul className="space-y-1 text-sm">
              {data.prs_to_close.map((pr) => {
                const key = `pr:${pr.number}`;
                const isPreserved = preserved.has(key);
                return (
                  <PrRow
                    key={pr.number}
                    pr={pr}
                    url={prUrl(pr.number)}
                    willDelete={!isPreserved}
                    onToggle={() => togglePreserve(key)}
                  />
                );
              })}
            </ul>
          </section>
        )}

        {/* ─── Branches to Preserve ─── */}
        {data.branches_to_preserve.length > 0 && (
          <section className="mb-4">
            <h3 className="text-sm font-medium text-green-800 dark:text-green-400 mb-2">
              <button
                type="button"
                className="inline-flex items-center gap-2 cursor-pointer select-none hover:opacity-80 transition-opacity"
                onClick={() => toggleAllInPreserveSection(branchPreserveKeys, ['main'])}
                aria-label="Toggle all branches to preserve"
              >
                {allBranchesPreserveMarked ? (
                  <ShieldOff className="h-4 w-4 text-destructive" />
                ) : (
                  <Shield className="h-4 w-4" />
                )}
                Branches to Preserve ({data.branches_to_preserve.length})
              </button>
            </h3>
            <ul className="space-y-1 text-sm">
              {data.branches_to_preserve.map((branch) => {
                const isMain = branch.name === 'main';
                const willDelete = !isMain && markedForDeletion.has(branch.name);
                return (
                  <BranchRow
                    key={branch.name}
                    branch={branch}
                    url={branchUrl(branch.name)}
                    willDelete={willDelete}
                    onToggle={isMain ? () => {} : () => toggleMarkForDeletion(branch.name)}
                    reason={isMain ? 'Default branch cannot be deleted' : branch.preservation_reason}
                    disabled={isMain}
                  />
                );
              })}
            </ul>
          </section>
        )}

        {/* ─── PRs to Preserve ─── */}
        {data.prs_to_preserve.length > 0 && (
          <section className="mb-4">
            <h3 className="text-sm font-medium text-green-800 dark:text-green-400 mb-2">
              <button
                type="button"
                className="inline-flex items-center gap-2 cursor-pointer select-none hover:opacity-80 transition-opacity"
                onClick={() => toggleAllInPreserveSection(prPreserveKeys)}
                aria-label="Toggle all pull requests to preserve"
              >
                {allPrsPreserveMarked ? (
                  <ShieldOff className="h-4 w-4 text-destructive" />
                ) : (
                  <Shield className="h-4 w-4" />
                )}
                Pull Requests to Preserve ({data.prs_to_preserve.length})
              </button>
            </h3>
            <ul className="space-y-1 text-sm">
              {data.prs_to_preserve.map((pr) => {
                const key = `pr:${pr.number}`;
                const willDelete = markedForDeletion.has(key);
                return (
                  <PrRow
                    key={pr.number}
                    pr={pr}
                    url={prUrl(pr.number)}
                    willDelete={willDelete}
                    onToggle={() => toggleMarkForDeletion(key)}
                    reason={pr.preservation_reason}
                  />
                );
              })}
            </ul>
          </section>
        )}

        {/* ─── Issues to Preserve ─── */}
        {(data.issues_to_preserve ?? []).length > 0 && (
          <section className="mb-4">
            <h3 className="text-sm font-medium text-green-800 dark:text-green-400 mb-2">
              <button
                type="button"
                className="inline-flex items-center gap-2 cursor-pointer select-none hover:opacity-80 transition-opacity"
                onClick={() => toggleAllInPreserveSection(issuePreserveKeys)}
                aria-label="Toggle all issues to preserve"
              >
                {allIssuesPreserveMarked ? (
                  <ShieldOff className="h-4 w-4 text-destructive" />
                ) : (
                  <Shield className="h-4 w-4" />
                )}
                Issues to Preserve ({data.issues_to_preserve.length})
              </button>
            </h3>
            <ul className="space-y-1 text-sm">
              {data.issues_to_preserve.map((issue) => {
                const key = `issue:${issue.number}`;
                const willDelete = markedForDeletion.has(key);
                return (
                  <li
                    key={issue.number}
                    className={`flex flex-col gap-0.5 px-2 py-1.5 rounded transition-colors ${willDelete ? 'bg-destructive/10' : 'bg-green-100/80 dark:bg-green-900/30'}`}
                  >
                    <div className="flex items-center gap-2">
                      <ToggleButton
                        willDelete={willDelete}
                        onClick={() => toggleMarkForDeletion(key)}
                      />
                      <a
                        href={issueUrl(issue)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2 min-w-0 flex-1 hover:underline"
                      >
                        <span className="font-medium shrink-0">#{issue.number}</span>
                        <span className="text-muted-foreground truncate">{issue.title}</span>
                        {issue.labels.length > 0 && (
                          <span className="text-xs text-muted-foreground shrink-0">
                            [{issue.labels.join(', ')}]
                          </span>
                        )}
                        <ExternalLink className="h-3 w-3 shrink-0 text-muted-foreground" />
                      </a>
                    </div>
                    {issue.preservation_reason && (
                      <span className="ml-[3.25rem] text-[11px] text-muted-foreground">
                        {issue.preservation_reason}
                      </span>
                    )}
                  </li>
                );
              })}
            </ul>
          </section>
        )}

        {!hasItemsToDelete && (
          <div className="mb-4 rounded-[1rem] border border-border bg-background/48 p-4 text-center text-sm text-muted-foreground">
            No stale Solune-generated branches, pull requests, or orphaned issues found. Nothing to
            clean up.
          </div>
        )}

        {/* Summary line */}
        <p className="text-xs text-muted-foreground mb-4">
          {data.open_issues_on_board} open issue{data.open_issues_on_board !== 1 ? 's' : ''} on the
          project board used for cross-referencing.
        </p>

        {/* Actions */}
        <div className="flex justify-end gap-3">
          <button
            onClick={onCancel}
            className="rounded-full border border-input bg-background/72 px-4 py-2 text-sm font-medium transition-colors hover:bg-primary/10"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={!hasItemsToDelete}
            className="px-4 py-2 text-sm font-medium rounded-md bg-destructive text-destructive-foreground hover:bg-destructive/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Confirm Cleanup
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}

/* ─── Sub-components ─── */

function ToggleButton({
  willDelete,
  onClick,
  disabled,
}: {
  willDelete: boolean;
  onClick: () => void;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={disabled ? undefined : onClick}
      disabled={disabled}
      className={`shrink-0 rounded p-1 transition-colors ${
        disabled ? 'opacity-50 cursor-not-allowed' : 'hover:bg-primary/10'
      }`}
      aria-label={willDelete ? 'Preserve this item' : 'Mark for deletion'}
      aria-disabled={disabled || undefined}
    >
      {willDelete ? (
        <ShieldOff className="h-3.5 w-3.5 text-destructive" />
      ) : (
        <Shield className="h-3.5 w-3.5 text-green-600 dark:text-green-400" />
      )}
    </button>
  );
}

function BranchRow({
  branch,
  url,
  willDelete,
  onToggle,
  reason,
  disabled,
}: {
  branch: BranchInfo;
  url: string;
  willDelete: boolean;
  onToggle: () => void;
  reason?: string | null;
  disabled?: boolean;
}) {
  return (
    <li
      className={`flex flex-col gap-0.5 px-2 py-1.5 rounded transition-colors ${willDelete ? 'bg-destructive/10' : 'bg-green-100/80 dark:bg-green-900/30'}`}
    >
      <div className="flex items-center gap-2">
        <ToggleButton willDelete={willDelete} onClick={onToggle} disabled={disabled} />
        <GitBranch className="h-3 w-3 shrink-0 text-muted-foreground" />
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1.5 min-w-0 hover:underline"
        >
          <span className="font-mono text-xs truncate">{branch.name}</span>
          <ExternalLink className="h-3 w-3 shrink-0 text-muted-foreground" />
        </a>
      </div>
      {(branch.deletion_reason || reason) && (
        <span className="ml-[3.25rem] text-[11px] text-muted-foreground">
          {disabled ? reason : willDelete ? branch.deletion_reason ?? reason : reason}
        </span>
      )}
    </li>
  );
}

function PrRow({
  pr,
  url,
  willDelete,
  onToggle,
  reason,
}: {
  pr: PullRequestInfo;
  url: string;
  willDelete: boolean;
  onToggle: () => void;
  reason?: string | null;
}) {
  return (
    <li
      className={`flex flex-col gap-0.5 px-2 py-1.5 rounded transition-colors ${willDelete ? 'bg-destructive/10' : 'bg-green-100/80 dark:bg-green-900/30'}`}
    >
      <div className="flex items-center gap-2">
        <ToggleButton willDelete={willDelete} onClick={onToggle} />
        <GitPullRequest className="h-3 w-3 shrink-0 text-muted-foreground" />
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 min-w-0 flex-1 hover:underline"
        >
          <span className="font-medium shrink-0">#{pr.number}</span>
          <span className="text-muted-foreground truncate">{pr.title}</span>
          <ExternalLink className="h-3 w-3 shrink-0 text-muted-foreground" />
        </a>
      </div>
      {(pr.deletion_reason || reason) && (
        <span className="ml-[3.25rem] text-[11px] text-muted-foreground">
          {willDelete ? pr.deletion_reason : reason}
        </span>
      )}
    </li>
  );
}
