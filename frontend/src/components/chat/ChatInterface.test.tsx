import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { ChatInterface } from './ChatInterface';

const uploadAllMock = vi.fn();
const clearAllMock = vi.fn();

vi.mock('@/hooks/useCommands', () => ({
  useCommands: () => ({
    isCommand: () => false,
    getFilteredCommands: () => [],
  }),
}));

vi.mock('@/hooks/useChatHistory', () => ({
  useChatHistory: () => ({
    addToHistory: vi.fn(),
    navigateUp: vi.fn(),
    navigateDown: vi.fn(),
    isNavigating: false,
    resetNavigation: vi.fn(),
    history: [],
    selectFromHistory: vi.fn(),
  }),
}));

vi.mock('@/hooks/useVoiceInput', () => ({
  useVoiceInput: () => ({
    isSupported: false,
    isRecording: false,
    interimTranscript: '',
    error: null,
    startRecording: vi.fn(),
    stopRecording: vi.fn(),
    cancelRecording: vi.fn(),
  }),
}));

vi.mock('@/hooks/useFileUpload', () => ({
  useFileUpload: () => ({
    files: [
      {
        id: 'file-1',
        file: new File(['hello'], 'notes.txt', { type: 'text/plain' }),
        filename: 'notes.txt',
        fileSize: 5,
        contentType: 'text/plain',
        status: 'pending',
        progress: 0,
        fileUrl: null,
        error: null,
      },
    ],
    errors: [],
    isUploading: false,
    addFiles: vi.fn(),
    removeFile: vi.fn(),
    uploadAll: uploadAllMock,
    clearAll: clearAllMock,
  }),
}));

describe('ChatInterface', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('does not send or clear files when uploads fail', async () => {
    uploadAllMock.mockResolvedValue({ urls: [], hasErrors: true });
    const onSendMessage = vi.fn();

    render(
      <ChatInterface
        messages={[]}
        pendingProposals={new Map()}
        pendingStatusChanges={new Map()}
        pendingRecommendations={new Map()}
        isSending={false}
        onSendMessage={onSendMessage}
        onRetryMessage={vi.fn()}
        onConfirmProposal={vi.fn()}
        onConfirmStatusChange={vi.fn()}
        onConfirmRecommendation={vi.fn()}
        onRejectProposal={vi.fn()}
        onRejectRecommendation={vi.fn()}
        onNewChat={vi.fn()}
      />
    );

    const textarea = screen.getByPlaceholderText('Describe a task or type / for commands...');
    fireEvent.change(textarea, {
      target: { value: 'Create an issue from this file' },
    });
    fireEvent.submit(textarea.closest('form')!);

    await waitFor(() => {
      expect(uploadAllMock).toHaveBeenCalledTimes(1);
    });

    expect(onSendMessage).not.toHaveBeenCalled();
    expect(clearAllMock).not.toHaveBeenCalled();
    expect(screen.getByText('notes.txt')).toBeInTheDocument();
  });
});