/**
 * Handlers for monitoring and export commands (/diff, /usage, /share, /feedback).
 */

import type { CommandResult, CommandContext } from '../types';

// ── /diff ───────────────────────────────────────────────────────────────────

export function diffHandler(): CommandResult {
  return { success: true, message: '', clearInput: true, passthrough: true };
}

// ── /usage ──────────────────────────────────────────────────────────────────

export function usageHandler(): CommandResult {
  return { success: true, message: '', clearInput: true, passthrough: true };
}

// ── /share ──────────────────────────────────────────────────────────────────

export function shareHandler(_args: string, context: CommandContext): CommandResult {
  const { messages } = context;

  if (messages.length === 0) {
    return {
      success: true,
      message: 'No messages to export.',
      clearInput: true,
    };
  }

  const exportDate = new Date().toISOString();
  const lines: string[] = [
    '# Solune Chat Export',
    `**Exported**: ${exportDate}`,
    `**Messages**: ${messages.length}`,
    '',
    '---',
    '',
    '## Conversation',
    '',
  ];

  for (const msg of messages) {
    const sender = msg.sender_type === 'user' ? 'User' : msg.sender_type === 'assistant' ? 'Assistant' : 'System';
    lines.push(`**${sender}** (${msg.timestamp}):`);
    lines.push(msg.content);
    lines.push('');
  }

  const markdown = lines.join('\n');
  const blob = new Blob([markdown], { type: 'text/markdown' });
  const url = URL.createObjectURL(blob);

  const a = document.createElement('a');
  a.href = url;
  a.download = `solune-chat-export-${exportDate.replace(/[:.]/g, '-')}.md`;
  a.click();
  URL.revokeObjectURL(url);

  return {
    success: true,
    message: `📥 Chat exported (${messages.length} messages).`,
    clearInput: true,
  };
}

// ── /feedback ───────────────────────────────────────────────────────────────

export function feedbackHandler(): CommandResult {
  return {
    success: true,
    message:
      '💬 We\'d love to hear from you! Share feedback at: https://github.com/Boykai/github-workflows/discussions',
    clearInput: true,
  };
}
