/**
 * CleanUpConfirmModal — displays categorized lists of branches/PRs
 * scheduled for deletion and preservation, with confirm/cancel actions.
 * Items link out to GitHub and can be toggled between delete/preserve.
 * Type group headers support select-all toggling with indeterminate state.
 * The 'main' branch is permanently protected from deletion.
 */

import { useEffect, useCallback, useState } from 'react';
import { createPortal } from 'react-dom';
import {
  ExternalLink,
  GitBranch,
  GitPullRequest,
  Lock,
  Minus,
  Shield,
  ShieldOff,
  Square,
  SquareCheck,
  Trash2,
  X,
} from '@/lib/icons';
import { Tooltip } from '@/components/ui/tooltip';
import type {
  CleanupPreflightResponse,
  CleanupConfirmPayload,
  BranchInfo,
  PullRequestInfo,
  OrphanedIssueInfo,
} from '@/types';
import { useScrollLock } from '@/hooks/useScrollLock';

/** Branch names that can never be deleted. */
const PROTECTED_BRANCHES = new Set(['main']);

function isProtectedBranch(name: string): boolean {
  return PROTECTED_BRANCHES.has(name);
}

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

  // ── Bulk-toggle helpers (type header select-all) ──

  /** Toggle all eligible (non-protected) branches in the "to delete" section. */
  const toggleAllDeleteBranches = () => {
    const eligible = data.branches_to_delete.filter((b) => !isProtectedBranch(b.name));
    const allSelected = eligible.every((b) => !preserved.has(b.name));
    setPreserved((prev) => {
      const next = new Set(prev);
      for (const b of eligible) {
        if (allSelected) next.add(b.name);
        else next.delete(b.name);
      }
      return next;
    });
  };

  /** Toggle all PRs in the "to close" section. */
  const toggleAllDeletePrs = () => {
    const allSelected = data.prs_to_close.every((p) => !preserved.has(`pr:${p.number}`));
    setPreserved((prev) => {
      const next = new Set(prev);
      for (const p of data.prs_to_close) {
        const key = `pr:${p.number}`;
        if (allSelected) next.add(key);
        else next.delete(key);
      }
      return next;
    });
  };

  /** Toggle all orphaned issues in the "to delete" section. */
  const toggleAllDeleteIssues = () => {
    const issues = data.orphaned_issues ?? [];
    const allSelected = issues.every((i) => !preserved.has(`issue:${i.number}`));
    setPreserved((prev) => {
      const next = new Set(prev);
      for (const i of issues) {
        const key = `issue:${i.number}`;
        if (allSelected) next.add(key);
        else next.delete(key);
      }
      return next;
    });
  };

  /** Toggle all eligible (non-protected) branches in the "to preserve" section. */
  const toggleAllPreserveBranches = () => {
    const eligible = data.branches_to_preserve.filter((b) => !isProtectedBranch(b.name));
    const allSelected = eligible.every((b) => markedForDeletion.has(b.name));
    setMarkedForDeletion((prev) => {
      const next = new Set(prev);
      for (const b of eligible) {
        if (allSelected) next.delete(b.name);
        else next.add(b.name);
      }
      return next;
    });
  };

  /** Toggle all PRs in the "to preserve" section. */
  const toggleAllPreservePrs = () => {
    const allSelected = data.prs_to_preserve.every((p) =>
      markedForDeletion.has(`pr:${p.number}`)
    );
    setMarkedForDeletion((prev) => {
      const next = new Set(prev);
      for (const p of data.prs_to_preserve) {
        const key = `pr:${p.number}`;
        if (allSelected) next.delete(key);
        else next.add(key);
      }
      return next;
    });
  };

  // ── Header checkbox state derivation ──

  const deleteBranchesEligible = data.branches_to_delete.filter(
    (b) => !isProtectedBranch(b.name)
  );
  const deleteBranchesSelected = deleteBranchesEligible.filter(
    (b) => !preserved.has(b.name)
  ).length;
  const deleteBranchesHeaderState = headerState(
    deleteBranchesSelected,
    deleteBranchesEligible.length
  );

  const deletePrsSelected = data.prs_to_close.filter(
    (p) => !preserved.has(`pr:${p.number}`)
  ).length;
  const deletePrsHeaderState = headerState(deletePrsSelected, data.prs_to_close.length);

  const orphanedIssues = data.orphaned_issues ?? [];
  const deleteIssuesSelected = orphanedIssues.filter(
    (i) => !preserved.has(`issue:${i.number}`)
  ).length;
  const deleteIssuesHeaderState = headerState(deleteIssuesSelected, orphanedIssues.length);

  const preserveBranchesEligible = data.branches_to_preserve.filter(
    (b) => !isProtectedBranch(b.name)
  );
  const preserveBranchesSelected = preserveBranchesEligible.filter((b) =>
    markedForDeletion.has(b.name)
  ).length;
  const preserveBranchesHeaderState = headerState(
    preserveBranchesSelected,
    preserveBranchesEligible.length
  );

  const preservePrsSelected = data.prs_to_preserve.filter((p) =>
    markedForDeletion.has(`pr:${p.number}`)
  ).length;
  const preservePrsHeaderState = headerState(preservePrsSelected, data.prs_to_preserve.length);

  // Compute final lists (protected branches are always excluded from deletion)
  const finalBranchesToDelete = data.branches_to_delete.filter(
    (b) => !preserved.has(b.name) && !isProtectedBranch(b.name)
  );
  const finalPrsToClose = data.prs_to_close.filter((p) => !preserved.has(`pr:${p.number}`));
  const finalIssuesToClose = orphanedIssues.filter(
    (i) => !preserved.has(`issue:${i.number}`)
  );
  const finalBranchesToDeleteFromPreserve = data.branches_to_preserve.filter(
    (b) => markedForDeletion.has(b.name) && !isProtectedBranch(b.name)
  );
  const finalPrsToCloseFromPreserve = data.prs_to_preserve.filter((p) =>
    markedForDeletion.has(`pr:${p.number}`)
  );

  const hasItemsToDelete =
    finalBranchesToDelete.length > 0 ||
    finalPrsToClose.length > 0 ||
    finalIssuesToClose.length > 0 ||
    finalBranchesToDeleteFromPreserve.length > 0 ||
    finalPrsToCloseFromPreserve.length > 0;

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
      issues_to_delete: finalIssuesToClose
        .filter((i) => i.node_id != null)
        .map((i) => ({ number: i.number, node_id: i.node_id! })),
    });
  };

  // URL builders
  const ghBase = `https://github.com/${owner}/${repo}`;
  const branchUrl = (name: string) => `${ghBase}/tree/${encodeURIComponent(name)}`;
  const prUrl = (num: number) => `${ghBase}/pull/${num}`;
  const issueUrl = (issue: OrphanedIssueInfo) => issue.html_url || `${ghBase}/issues/${issue.number}`;

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
        {orphanedIssues.length > 0 && (
          <section className="mb-4">
            <TypeGroupHeader
              icon={<Trash2 className="h-4 w-4" />}
              label={`Orphaned Issues to Delete (${orphanedIssues.length})`}
              state={deleteIssuesHeaderState}
              onToggle={toggleAllDeleteIssues}
              variant="destructive"
            />
            <p className="text-xs text-muted-foreground mb-2">
              App-created issues no longer attached to the project board. These will be permanently
              deleted from GitHub.
            </p>
            <ul className="space-y-1 text-sm">
              {orphanedIssues.map((issue) => {
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
            <TypeGroupHeader
              icon={<Trash2 className="h-4 w-4" />}
              label={`Branches to Delete (${data.branches_to_delete.length})`}
              state={deleteBranchesHeaderState}
              onToggle={toggleAllDeleteBranches}
              disabled={deleteBranchesEligible.length === 0}
              variant="destructive"
            />
            <ul className="space-y-1 text-sm">
              {data.branches_to_delete.map((branch) => {
                const branchProtected = isProtectedBranch(branch.name);
                const isPreserved = preserved.has(branch.name);
                return (
                  <BranchRow
                    key={branch.name}
                    branch={branch}
                    url={branchUrl(branch.name)}
                    willDelete={branchProtected ? false : !isPreserved}
                    onToggle={() => togglePreserve(branch.name)}
                    isProtected={branchProtected}
                  />
                );
              })}
            </ul>
          </section>
        )}

        {/* ─── PRs to Close ─── */}
        {data.prs_to_close.length > 0 && (
          <section className="mb-4">
            <TypeGroupHeader
              icon={<Trash2 className="h-4 w-4" />}
              label={`Pull Requests to Close (${data.prs_to_close.length})`}
              state={deletePrsHeaderState}
              onToggle={toggleAllDeletePrs}
              variant="destructive"
            />
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
            <TypeGroupHeader
              icon={<Shield className="h-4 w-4" />}
              label={`Branches to Preserve (${data.branches_to_preserve.length})`}
              state={preserveBranchesHeaderState}
              onToggle={toggleAllPreserveBranches}
              disabled={preserveBranchesEligible.length === 0}
              variant="preserve"
            />
            <ul className="space-y-1 text-sm">
              {data.branches_to_preserve.map((branch) => {
                const branchProtected = isProtectedBranch(branch.name);
                const willDelete = branchProtected
                  ? false
                  : markedForDeletion.has(branch.name);
                return (
                  <BranchRow
                    key={branch.name}
                    branch={branch}
                    url={branchUrl(branch.name)}
                    willDelete={willDelete}
                    onToggle={() => toggleMarkForDeletion(branch.name)}
                    reason={branch.preservation_reason}
                    isProtected={branchProtected}
                  />
                );
              })}
            </ul>
          </section>
        )}

        {/* ─── PRs to Preserve ─── */}
        {data.prs_to_preserve.length > 0 && (
          <section className="mb-4">
            <TypeGroupHeader
              icon={<Shield className="h-4 w-4" />}
              label={`Pull Requests to Preserve (${data.prs_to_preserve.length})`}
              state={preservePrsHeaderState}
              onToggle={toggleAllPreservePrs}
              variant="preserve"
            />
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

type CheckboxState = 'checked' | 'unchecked' | 'indeterminate';

/** Derive header checkbox state from selection counts. */
function headerState(selectedCount: number, totalEligible: number): CheckboxState {
  if (totalEligible === 0 || selectedCount === 0) return 'unchecked';
  if (selectedCount === totalEligible) return 'checked';
  return 'indeterminate';
}

/** Clickable type-group header with a select-all checkbox. */
function TypeGroupHeader({
  icon,
  label,
  state,
  onToggle,
  disabled = false,
  variant = 'destructive',
}: {
  icon: React.ReactNode;
  label: string;
  state: CheckboxState;
  onToggle: () => void;
  disabled?: boolean;
  variant?: 'destructive' | 'preserve';
}) {
  const ariaChecked = state === 'indeterminate' ? 'mixed' : state === 'checked';
  const colorClass =
    variant === 'destructive'
      ? 'text-destructive'
      : 'text-green-800 dark:text-green-400';

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (disabled) return;
    if (e.key === ' ' || e.key === 'Enter') {
      e.preventDefault();
      onToggle();
    }
  };

  return (
    <div
      className={`text-sm font-medium ${colorClass} mb-2 flex items-center gap-2 cursor-pointer select-none rounded px-1 py-0.5 transition-colors hover:bg-primary/5 ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
      role="checkbox"
      aria-checked={ariaChecked}
      aria-disabled={disabled}
      aria-label={`Toggle all: ${label}`}
      tabIndex={disabled ? -1 : 0}
      onClick={disabled ? undefined : onToggle}
      onKeyDown={handleKeyDown}
    >
      <span className="shrink-0" aria-hidden="true">
        {state === 'checked' && <SquareCheck className="h-4 w-4" />}
        {state === 'unchecked' && <Square className="h-4 w-4" />}
        {state === 'indeterminate' && <Minus className="h-4 w-4" />}
      </span>
      <span className="inline-flex items-center gap-2">
        {icon}
        {label}
      </span>
    </div>
  );
}

function ToggleButton({ willDelete, onClick }: { willDelete: boolean; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="shrink-0 rounded p-1 transition-colors hover:bg-primary/10"
      aria-label={willDelete ? 'Preserve this item' : 'Mark for deletion'}
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
  isProtected = false,
}: {
  branch: BranchInfo;
  url: string;
  willDelete: boolean;
  onToggle: () => void;
  reason?: string | null;
  isProtected?: boolean;
}) {
  return (
    <li
      className={`flex flex-col gap-0.5 px-2 py-1.5 rounded transition-colors ${isProtected ? 'bg-muted/40 opacity-60' : willDelete ? 'bg-destructive/10' : 'bg-green-100/80 dark:bg-green-900/30'}`}
    >
      <div className="flex items-center gap-2">
        {isProtected ? (
          <Tooltip content="Protected branch — cannot be deleted">
            <span className="shrink-0 rounded p-1 cursor-not-allowed" aria-label="Protected branch — cannot be deleted">
              <Lock className="h-3.5 w-3.5 text-muted-foreground" aria-hidden="true" />
            </span>
          </Tooltip>
        ) : (
          <ToggleButton willDelete={willDelete} onClick={onToggle} />
        )}
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
        {isProtected && (
          <span className="text-[10px] text-muted-foreground italic shrink-0">protected</span>
        )}
      </div>
      {(branch.deletion_reason || reason) && (
        <span className="ml-[3.25rem] text-[11px] text-muted-foreground">
          {willDelete ? branch.deletion_reason : reason}
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
