import { useCallback, useId, useMemo, useRef, useState, type ChangeEvent } from 'react';
import { useMutation } from '@tanstack/react-query';
import {
  CheckCircle2,
  ChevronDown,
  FileUp,
  LoaderCircle,
  Orbit,
  Sparkles,
  TriangleAlert,
} from '@/lib/icons';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { pipelinesApi } from '@/services/api';
import { toast } from 'sonner';
import type { PipelineConfigSummary, PipelineIssueLaunchRequest, WorkflowResult } from '@/types';

const STORAGE_KEY = 'parentIssueIntake_expanded';

function loadExpanded(): boolean {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === null) return false;
    return stored === 'true';
  } catch {
    return false;
  }
}

const MAX_ISSUE_DESCRIPTION_LENGTH = 65_536;
const MAX_PREVIEW_TITLE_LENGTH = 120;
const PREVIEW_TITLE_TRUNCATE_AT = MAX_PREVIEW_TITLE_LENGTH - 3;
const ACCEPTED_FILE_EXTENSIONS = ['.md', '.txt', '.vtt', '.srt'];
const MARKDOWN_TITLE_PREFIX_RE = /^[>\-*+\d.\s`_~]+/;

interface ProjectIssueLaunchPanelProps {
  projectId: string;
  projectName?: string;
  pipelines: PipelineConfigSummary[];
  isLoadingPipelines: boolean;
  pipelinesError?: string | null;
  onRetryPipelines: () => void;
  onLaunched?: (result: WorkflowResult) => void;
}

interface FormErrors {
  issueDescription?: string;
  pipelineId?: string;
  file?: string;
}

function deriveIssueTitlePreview(issueDescription: string): string {
  const headingMatch = issueDescription.match(/^\s{0,3}#{1,6}\s+(.+)$/m);
  const firstLine =
    headingMatch?.[1]?.trim() ??
    issueDescription
      .split('\n')
      .map((line) => line.trim())
      .find(Boolean) ??
    'Imported Parent Issue';

  const normalized = firstLine.replace(MARKDOWN_TITLE_PREFIX_RE, '').replace(/\s+/g, ' ').trim();
  if (!normalized) return 'Imported Parent Issue';
  return normalized.length > MAX_PREVIEW_TITLE_LENGTH
    ? `${normalized.slice(0, PREVIEW_TITLE_TRUNCATE_AT).trimEnd()}...`
    : normalized;
}

function isAcceptedIssueFile(file: File): boolean {
  const lowerName = file.name.toLowerCase();
  return ACCEPTED_FILE_EXTENSIONS.some((extension) => lowerName.endsWith(extension));
}

export function ProjectIssueLaunchPanel({
  projectId,
  projectName,
  pipelines,
  isLoadingPipelines,
  pipelinesError,
  onRetryPipelines,
  onLaunched,
}: ProjectIssueLaunchPanelProps) {
  const collapsibleBodyId = useId();
  const fileInputId = useId();
  const pipelineSelectId = useId();
  const issueDescriptionId = useId();
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [issueDescription, setIssueDescription] = useState('');
  const [pipelineId, setPipelineId] = useState('');
  const [uploadedFileName, setUploadedFileName] = useState('');
  const [formErrors, setFormErrors] = useState<FormErrors>({});
  const [submissionResult, setSubmissionResult] = useState<WorkflowResult | null>(null);
  const [submissionError, setSubmissionError] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState(loadExpanded);

  const toggleExpanded = useCallback(() => {
    setIsExpanded((prev) => {
      const next = !prev;
      try {
        localStorage.setItem(STORAGE_KEY, String(next));
      } catch {
        /* ignore */
      }
      return next;
    });
  }, []);

  const selectedPipeline = useMemo(
    () => pipelines.find((pipeline) => pipeline.id === pipelineId) ?? null,
    [pipelineId, pipelines]
  );
  const issueTitlePreview = useMemo(
    () => deriveIssueTitlePreview(issueDescription),
    [issueDescription]
  );

  const launchMutation = useMutation({
    mutationFn: (payload: PipelineIssueLaunchRequest) => pipelinesApi.launch(projectId, payload),
    onSuccess: (result) => {
      setSubmissionResult(result);
      if (result.success) {
        setSubmissionError(null);
        onLaunched?.(result);
        // Show toast for queued pipelines
        if (result.message?.includes('Pipeline queued')) {
          toast.info(result.message);
        }
        return;
      }

      setSubmissionError(result.message);
    },
    onError: (error) => {
      setSubmissionResult(null);
      setSubmissionError(
        error instanceof Error ? error.message : 'We could not launch the selected pipeline.'
      );
    },
  });

  const handleIssueDescriptionChange = (event: ChangeEvent<HTMLTextAreaElement>) => {
    const nextValue = event.target.value;
    setIssueDescription(nextValue);
    setUploadedFileName('');
    setSubmissionResult(null);
    setSubmissionError(null);
    setFormErrors((current) => ({
      ...current,
      issueDescription:
        nextValue.trim().length === 0
          ? undefined
          : nextValue.length > MAX_ISSUE_DESCRIPTION_LENGTH
            ? `Keep the issue description under ${MAX_ISSUE_DESCRIPTION_LENGTH.toLocaleString()} characters.`
            : undefined,
      file: undefined,
    }));
  };

  const handlePipelineChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const nextValue = event.target.value;
    setPipelineId(nextValue);
    setSubmissionResult(null);
    setSubmissionError(null);
    setFormErrors((current) => ({
      ...current,
      pipelineId: nextValue ? undefined : current.pipelineId,
    }));
  };

  const handleFileSelection = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setSubmissionResult(null);
    setSubmissionError(null);

    if (!isAcceptedIssueFile(file)) {
      setFormErrors((current) => ({
        ...current,
        file: 'Only Markdown (.md), plain-text (.txt), WebVTT (.vtt), and SubRip (.srt) files are supported.',
      }));
      event.target.value = '';
      return;
    }

    try {
      const text = await file.text();
      if (text.length > MAX_ISSUE_DESCRIPTION_LENGTH) {
        setFormErrors((current) => ({
          ...current,
          file: `Keep the imported issue under ${MAX_ISSUE_DESCRIPTION_LENGTH.toLocaleString()} characters.`,
        }));
        event.target.value = '';
        return;
      }

      setIssueDescription(text);
      setUploadedFileName(file.name);
      setFormErrors((current) => ({
        ...current,
        issueDescription: undefined,
        file: undefined,
      }));
    } catch {
      setFormErrors((current) => ({
        ...current,
        file: 'The selected file could not be read. Please try again.',
      }));
    } finally {
      event.target.value = '';
    }
  };

  const handleSubmit = async () => {
    const nextErrors: FormErrors = {};
    const normalizedDescription = issueDescription.trim();

    if (!normalizedDescription) {
      nextErrors.issueDescription = 'Paste or upload the parent issue description first.';
    } else if (normalizedDescription.length > MAX_ISSUE_DESCRIPTION_LENGTH) {
      nextErrors.issueDescription = `Keep the issue description under ${MAX_ISSUE_DESCRIPTION_LENGTH.toLocaleString()} characters.`;
    }

    if (!pipelineId) {
      nextErrors.pipelineId = 'Select an Agent Pipeline Config before launching.';
    }

    setFormErrors((current) => ({ ...current, ...nextErrors }));
    setSubmissionResult(null);
    setSubmissionError(null);

    if (Object.keys(nextErrors).length > 0) {
      return;
    }

    await launchMutation.mutateAsync({
      issue_description: normalizedDescription,
      pipeline_id: pipelineId,
    });
  };

  const hasPipelineOptions = pipelines.length > 0;

  return (
    <section className="celestial-panel relative overflow-hidden rounded-[1.45rem] border border-border/80 bg-background/34 shadow-sm">
      <div className="pointer-events-none absolute inset-x-6 top-0 h-px bg-gradient-to-r from-transparent via-primary/45 to-transparent" />

      {/* Collapsible header — always visible */}
      <button
        type="button"
        aria-expanded={isExpanded}
        aria-controls={collapsibleBodyId}
        onClick={toggleExpanded}
        className="flex w-full items-center gap-3 p-5 text-left transition-colors hover:bg-background/28 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary sm:p-6"
      >
        <ChevronDown
          className={cn(
            'h-4 w-4 shrink-0 text-muted-foreground transition-transform duration-200',
            !isExpanded && '-rotate-90'
          )}
        />
        <div className="flex flex-1 flex-wrap items-center gap-2">
          <span className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/8 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-primary">
            <Orbit className="h-3.5 w-3.5" />
            Parent issue intake
          </span>
          {projectName ? (
            <span className="rounded-full border border-border/70 px-3 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
              {projectName}
            </span>
          ) : null}
        </div>
      </button>

      {/* Collapsible body */}
      <div
        id={collapsibleBodyId}
        inert={!isExpanded || undefined}
        className={cn(
          'grid transition-[grid-template-rows] duration-200 ease-in-out',
          isExpanded ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'
        )}
      >
        <div className="overflow-hidden">
          <div className="px-5 pb-5 sm:px-6 sm:pb-6">
            <div className="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_20rem]">
              <div className="space-y-4">
                <div className="space-y-2">
                  <h3 className="text-lg font-semibold text-foreground">
                    Launch an agent pipeline from existing GitHub issue context
                  </h3>
                  <p className="max-w-3xl text-sm leading-6 text-muted-foreground">
                    Paste the parent issue body or import a Markdown/text file, then pair it with a
                    saved Agent Pipeline Config. This launch also keeps the project&apos;s active
                    pipeline in sync so downstream agents continue with the same configuration.
                  </p>
                </div>

                <div className="rounded-[1.25rem] border border-border/75 bg-background/58 p-4 backdrop-blur-sm">
                  <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <label
                        htmlFor={issueDescriptionId}
                        className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground"
                      >
                        GitHub Parent Issue Description
                      </label>
                      <p className="mt-1 text-xs text-muted-foreground">
                        Supports pasted Markdown or imported <code>.md</code>/<code>.txt</code>/<code>.vtt</code>/<code>.srt</code>{' '}
                        issue bodies and transcripts.
                      </p>
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      <input
                        ref={fileInputRef}
                        id={fileInputId}
                        type="file"
                        accept=".md,.txt,.vtt,.srt,text/plain,text/markdown"
                        className="sr-only"
                        onChange={(event) => {
                          void handleFileSelection(event);
                        }}
                      />
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => fileInputRef.current?.click()}
                      >
                        <FileUp className="mr-2 h-3.5 w-3.5" />
                        Upload file
                      </Button>
                      {uploadedFileName ? (
                        <span className="rounded-full border border-primary/20 bg-primary/8 px-3 py-1 text-[11px] font-medium text-primary">
                          Imported {uploadedFileName}
                        </span>
                      ) : null}
                    </div>
                  </div>

                  <textarea
                    id={issueDescriptionId}
                    value={issueDescription}
                    onChange={handleIssueDescriptionChange}
                    aria-invalid={!!formErrors.issueDescription}
                    aria-describedby={
                      formErrors.issueDescription ? `${issueDescriptionId}-error` : undefined
                    }
                    placeholder="# Improve the Projects launch flow&#10;&#10;## User Story&#10;As a user, I want to import parent issue context and launch the right pipeline without retyping the details."
                    className={cn(
                      'min-h-[18rem] w-full rounded-[1rem] border bg-background/72 px-4 py-3 text-sm leading-6 text-foreground shadow-inner outline-none transition-colors resize-y',
                      formErrors.issueDescription
                        ? 'border-destructive/60 focus:border-destructive/70'
                        : 'border-border/70 focus:border-primary/50'
                    )}
                  />

                  <div className="mt-3 flex flex-wrap items-center justify-between gap-3 text-xs text-muted-foreground">
                    <span>
                      The first heading or opening line becomes the parent issue title preview shown
                      on the right.
                    </span>
                    <span>
                      {issueDescription.length.toLocaleString()} /{' '}
                      {MAX_ISSUE_DESCRIPTION_LENGTH.toLocaleString()} chars
                    </span>
                  </div>

                  {formErrors.issueDescription ? (
                    <p id={`${issueDescriptionId}-error`} className="mt-3 text-sm text-destructive">
                      {formErrors.issueDescription}
                    </p>
                  ) : null}
                  {formErrors.file ? (
                    <p className="mt-3 text-sm text-destructive">{formErrors.file}</p>
                  ) : null}
                </div>
              </div>

              <div className="space-y-4">
                <div className="rounded-[1.25rem] border border-border/75 bg-background/58 p-4 backdrop-blur-sm">
                  <div className="mb-3 space-y-1">
                    <label
                      htmlFor={pipelineSelectId}
                      className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground"
                    >
                      Agent Pipeline Config
                    </label>
                    <p className="text-xs text-muted-foreground">
                      Choose the saved pipeline that should process this imported issue.
                    </p>
                  </div>

                  {pipelinesError ? (
                    <div className="space-y-3 rounded-[1rem] border border-destructive/25 bg-destructive/8 p-3 text-sm text-destructive">
                      <div className="flex items-start gap-2">
                        <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" />
                        <p>{pipelinesError}</p>
                      </div>
                      <Button type="button" variant="outline" size="sm" onClick={onRetryPipelines}>
                        Retry loading configs
                      </Button>
                    </div>
                  ) : !isLoadingPipelines && !hasPipelineOptions ? (
                    <div className="space-y-3 rounded-[1rem] border border-border/75 bg-background/65 p-3 text-sm text-muted-foreground">
                      <p>No Agent Pipeline Configs are available for this project yet.</p>
                      <Button type="button" variant="outline" size="sm" asChild>
                        <Link to="/pipeline">Create a pipeline</Link>
                      </Button>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <select
                        id={pipelineSelectId}
                        value={pipelineId}
                        onChange={handlePipelineChange}
                        disabled={isLoadingPipelines || launchMutation.isPending}
                        aria-invalid={!!formErrors.pipelineId}
                        aria-describedby={
                          formErrors.pipelineId ? `${pipelineSelectId}-error` : undefined
                        }
                        className={cn(
                          'moonwell h-11 w-full rounded-[0.95rem] border px-3 text-sm text-foreground outline-none transition-colors',
                          formErrors.pipelineId
                            ? 'border-destructive/60 focus:border-destructive/70'
                            : 'border-border/70 focus:border-primary/40'
                        )}
                      >
                        <option value="">
                          {isLoadingPipelines
                            ? 'Loading pipeline configs…'
                            : 'Select a pipeline config'}
                        </option>
                        {pipelines.map((pipeline) => (
                          <option key={pipeline.id} value={pipeline.id}>
                            {pipeline.name}
                          </option>
                        ))}
                      </select>
                      {formErrors.pipelineId ? (
                        <p id={`${pipelineSelectId}-error`} className="text-sm text-destructive">
                          {formErrors.pipelineId}
                        </p>
                      ) : null}
                    </div>
                  )}
                </div>

                <div className="rounded-[1.25rem] border border-primary/15 bg-primary/6 p-4">
                  <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-primary">
                    <Sparkles className="h-3.5 w-3.5" />
                    Launch preview
                  </div>
                  <dl className="space-y-4">
                    <div>
                      <dt className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                        Derived issue title
                      </dt>
                      <dd className="mt-1 text-sm font-medium text-foreground">
                        {issueTitlePreview}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                        Selected pipeline
                      </dt>
                      <dd className="mt-1 text-sm text-foreground">
                        {selectedPipeline?.name ?? 'Choose a saved pipeline config'}
                      </dd>
                      {selectedPipeline ? (
                        <p className="mt-1 text-xs leading-5 text-muted-foreground">
                          {selectedPipeline.stage_count} stages • {selectedPipeline.agent_count}{' '}
                          agents
                        </p>
                      ) : null}
                    </div>
                    <div>
                      <dt className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                        What happens next
                      </dt>
                      <dd className="mt-1 text-sm leading-6 text-muted-foreground">
                        We create a new parent issue from this description, attach it to the
                        project, and start the selected pipeline on the first stage automatically.
                      </dd>
                    </div>
                  </dl>
                </div>
              </div>
            </div>

            <div className="mt-5 space-y-3">
              {submissionError ? (
                <div className="flex flex-wrap items-start gap-3 rounded-[1.15rem] border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
                  <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" />
                  <div className="min-w-0 flex-1 space-y-1">
                    <p className="font-medium">Launch failed</p>
                    <p>{submissionError}</p>
                    {submissionResult?.issue_url ? (
                      <a
                        href={submissionResult.issue_url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex font-medium text-destructive underline underline-offset-4"
                      >
                        Open the created issue
                      </a>
                    ) : null}
                  </div>
                </div>
              ) : null}

              {submissionResult?.success ? (
                <div className="flex flex-wrap items-start gap-3 rounded-[1.15rem] border border-emerald-500/30 bg-emerald-500/10 p-4 text-sm text-emerald-700 dark:text-emerald-300">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
                  <div className="min-w-0 flex-1 space-y-1">
                    <p className="font-medium">Pipeline launched successfully</p>
                    <p>{submissionResult.message}</p>
                  </div>
                  {submissionResult.issue_url ? (
                    <Button type="button" variant="outline" size="sm" asChild>
                      <a href={submissionResult.issue_url} target="_blank" rel="noreferrer">
                        Open issue #{submissionResult.issue_number}
                      </a>
                    </Button>
                  ) : null}
                </div>
              ) : null}

              <div className="flex flex-col gap-3 border-t border-border/65 pt-4 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-sm leading-6 text-muted-foreground">
                  Validation happens inline and your imported text stays in place if the launch
                  needs to be corrected or retried.
                </p>
                <Button
                  type="button"
                  size="lg"
                  disabled={launchMutation.isPending || isLoadingPipelines || !hasPipelineOptions}
                  onClick={() => {
                    void handleSubmit();
                  }}
                >
                  {launchMutation.isPending ? (
                    <>
                      <LoaderCircle className="mr-2 h-4 w-4 animate-spin" />
                      Launching pipeline…
                    </>
                  ) : (
                    'Launch pipeline'
                  )}
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
