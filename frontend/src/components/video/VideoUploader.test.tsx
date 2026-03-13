/**
 * Tests for VideoUploader component.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@/test/test-utils';
import { VideoUploader } from './VideoUploader';

// Mock the video API
vi.mock('@/services/api', () => ({
  videoApi: {
    uploadVideo: vi.fn(),
  },
  ApiError: class extends Error {
    constructor(
      public status: number,
      public error: { error: string }
    ) {
      super(error.error);
    }
  },
}));

describe('VideoUploader', () => {
  it('renders drop zone in idle state', () => {
    render(<VideoUploader />);
    expect(screen.getByText(/Drag & drop a video file/)).toBeInTheDocument();
    expect(screen.getByText(/MP4, MOV, AVI, MKV, WebM/)).toBeInTheDocument();
  });

  it('renders the browse link in the drop zone', () => {
    render(<VideoUploader />);
    expect(screen.getByText('browse')).toBeInTheDocument();
  });

  it('has proper aria-label on drop zone', () => {
    render(<VideoUploader />);
    const dropZone = screen.getByRole('button', {
      name: 'Upload video — drag and drop or click to browse',
    });
    expect(dropZone).toBeInTheDocument();
  });

  it('renders hidden file input with video accept types', () => {
    render(<VideoUploader />);
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    expect(input).toBeInTheDocument();
    expect(input.accept).toContain('.mp4');
    expect(input.accept).toContain('.webm');
    expect(input.accept).toContain('.mov');
  });

  it('accepts keyboard interaction on drop zone', () => {
    render(<VideoUploader />);
    const dropZone = screen.getByRole('button', {
      name: 'Upload video — drag and drop or click to browse',
    });
    expect(dropZone.getAttribute('tabindex')).toBe('0');
  });

  it('shows error for unsupported file format', async () => {
    const onError = vi.fn();
    render(<VideoUploader onUploadError={onError} />);

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const invalidFile = new File(['test'], 'document.pdf', { type: 'application/pdf' });

    Object.defineProperty(input, 'files', { value: [invalidFile] });
    fireEvent.change(input);

    // Wait for validation
    await vi.waitFor(() => {
      expect(screen.getByText(/Unsupported format/)).toBeInTheDocument();
    });
  });

  it('applies custom className', () => {
    const { container } = render(<VideoUploader className="my-custom-class" />);
    expect(container.firstChild).toHaveClass('my-custom-class');
  });

  it('shows drag-over visual feedback', () => {
    render(<VideoUploader />);
    const dropZone = screen.getByRole('button', {
      name: 'Upload video — drag and drop or click to browse',
    });

    fireEvent.dragOver(dropZone);
    expect(dropZone.className).toContain('border-primary');
  });
});
