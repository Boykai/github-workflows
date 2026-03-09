import { describe, expect, it, vi } from 'vitest';
import { render, screen, userEvent } from '@/test/test-utils';
import { FilePreviewChips } from './FilePreviewChips';
import type { FileAttachment } from '@/types';

function createAttachment(overrides: Partial<FileAttachment> = {}): FileAttachment {
  const file = new File(['content'], overrides.filename ?? 'design-spec.pdf', {
    type: overrides.contentType ?? 'application/pdf',
  });

  return {
    id: 'file-1',
    file,
    filename: 'design-spec.pdf',
    fileSize: 2048,
    contentType: 'application/pdf',
    previewUrl: null,
    status: 'pending',
    progress: 0,
    fileUrl: null,
    error: null,
    ...overrides,
  };
}

describe('FilePreviewChips', () => {
  it('renders image thumbnails and file cards for pending attachments', () => {
    render(
      <FilePreviewChips
        files={[
          createAttachment({
            id: 'image-1',
            filename: 'screenshot.png',
            contentType: 'image/png',
            previewUrl: 'blob:screenshot-preview',
          }),
          createAttachment(),
        ]}
        onRemove={vi.fn()}
      />
    );

    expect(screen.getByText('Attachments')).toBeInTheDocument();
    expect(screen.getByAltText('screenshot.png')).toHaveAttribute('src', 'blob:screenshot-preview');
    expect(screen.getByText('design-spec.pdf')).toBeInTheDocument();
  });

  it('calls onRemove for individual attachments', async () => {
    const onRemove = vi.fn();
    const user = userEvent.setup();

    render(<FilePreviewChips files={[createAttachment()]} onRemove={onRemove} />);

    await user.click(screen.getByRole('button', { name: /remove design-spec\.pdf/i }));

    expect(onRemove).toHaveBeenCalledWith('file-1');
  });
});
