import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { expectNoA11yViolations } from '@/test/a11y-helpers';
import { PipelineWarningBanner } from './PipelineWarningBanner';

const mockUseSelectedPipeline = vi.fn();

vi.mock('@/hooks/useSelectedPipeline', () => ({
  useSelectedPipeline: (...args: unknown[]) => mockUseSelectedPipeline(...args),
}));

describe('PipelineWarningBanner', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders nothing while the pipeline state is loading', () => {
    mockUseSelectedPipeline.mockReturnValue({
      pipelineId: '',
      pipelineName: '',
      isLoading: true,
      hasAssignment: false,
    });

    const { container } = render(<PipelineWarningBanner projectId="PVT_123" />);

    expect(container).toBeEmptyDOMElement();
  });

  it('renders nothing when a pipeline assignment exists', () => {
    mockUseSelectedPipeline.mockReturnValue({
      pipelineId: 'pipe-1',
      pipelineName: 'Pipeline Alpha',
      isLoading: false,
      hasAssignment: true,
    });

    const { container } = render(<PipelineWarningBanner projectId="PVT_123" />);

    expect(container).toBeEmptyDOMElement();
  });

  it('renders the warning text when no assignment exists', () => {
    mockUseSelectedPipeline.mockReturnValue({
      pipelineId: '',
      pipelineName: '',
      isLoading: false,
      hasAssignment: false,
    });

    render(<PipelineWarningBanner projectId="PVT_123" />);

    expect(screen.getByText(/No Agent Pipeline selected/i)).toBeInTheDocument();
    expect(screen.getByText(/issues will use the default pipeline/i)).toBeInTheDocument();
  });

  it('uses an alert role for accessibility', () => {
    mockUseSelectedPipeline.mockReturnValue({
      pipelineId: '',
      pipelineName: '',
      isLoading: false,
      hasAssignment: false,
    });

    render(<PipelineWarningBanner projectId="PVT_123" />);

    expect(screen.getByRole('alert')).toBeInTheDocument();
  });

  it('has no accessibility violations', async () => {
    mockUseSelectedPipeline.mockReturnValue({
      pipelineId: '',
      pipelineName: '',
      isLoading: false,
      hasAssignment: false,
    });

    const { container } = render(<PipelineWarningBanner projectId="PVT_123" />);
    await expectNoA11yViolations(container);
  });
});
