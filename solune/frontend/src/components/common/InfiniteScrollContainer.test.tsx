import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { InfiniteScrollContainer } from './InfiniteScrollContainer';

describe('InfiniteScrollContainer', () => {
  let mockObserve: ReturnType<typeof vi.fn>;
  let mockDisconnect: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    mockObserve = vi.fn();
    mockDisconnect = vi.fn();
    // Use a class-style mock to satisfy `new IntersectionObserver(…)`
    vi.stubGlobal(
      'IntersectionObserver',
      class {
        observe = mockObserve;
        disconnect = mockDisconnect;
        unobserve = vi.fn();
        constructor(_cb: IntersectionObserverCallback, _opts?: IntersectionObserverInit) {}
      },
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders children', () => {
    render(
      <InfiniteScrollContainer
        hasNextPage={false}
        isFetchingNextPage={false}
        fetchNextPage={vi.fn()}
      >
        <div data-testid="child">Hello</div>
      </InfiniteScrollContainer>,
    );
    expect(screen.getByTestId('child')).toBeInTheDocument();
  });

  it('shows loading indicator when fetching next page', () => {
    render(
      <InfiniteScrollContainer
        hasNextPage={true}
        isFetchingNextPage={true}
        fetchNextPage={vi.fn()}
      >
        <div>Content</div>
      </InfiniteScrollContainer>,
    );
    expect(screen.getByText('Loading more…')).toBeInTheDocument();
  });

  it('shows error state with retry button on error', () => {
    const onRetry = vi.fn();
    render(
      <InfiniteScrollContainer
        hasNextPage={true}
        isFetchingNextPage={false}
        fetchNextPage={vi.fn()}
        isError={true}
        onRetry={onRetry}
      >
        <div>Content</div>
      </InfiniteScrollContainer>,
    );
    expect(screen.getByText('Failed to load more items.')).toBeInTheDocument();
    expect(screen.getByText('Retry')).toBeInTheDocument();
  });

  it('hides sentinel when there is no next page', () => {
    const { container } = render(
      <InfiniteScrollContainer
        hasNextPage={false}
        isFetchingNextPage={false}
        fetchNextPage={vi.fn()}
      >
        <div>Content</div>
      </InfiniteScrollContainer>,
    );
    const sentinel = container.querySelector('[aria-hidden="true"]');
    expect(sentinel).toBeNull();
  });

  it('shows sentinel when hasNextPage is true and no error', () => {
    const { container } = render(
      <InfiniteScrollContainer
        hasNextPage={true}
        isFetchingNextPage={false}
        fetchNextPage={vi.fn()}
      >
        <div>Content</div>
      </InfiniteScrollContainer>,
    );
    const sentinel = container.querySelector('[aria-hidden="true"]');
    expect(sentinel).not.toBeNull();
  });

  it('sets up IntersectionObserver when hasNextPage is true', () => {
    render(
      <InfiniteScrollContainer
        hasNextPage={true}
        isFetchingNextPage={false}
        fetchNextPage={vi.fn()}
      >
        <div>Content</div>
      </InfiniteScrollContainer>,
    );
    expect(mockObserve).toHaveBeenCalled();
  });

  it('does not show loading indicator when not fetching', () => {
    render(
      <InfiniteScrollContainer
        hasNextPage={true}
        isFetchingNextPage={false}
        fetchNextPage={vi.fn()}
      >
        <div>Content</div>
      </InfiniteScrollContainer>,
    );
    expect(screen.queryByText('Loading more…')).toBeNull();
  });
});
