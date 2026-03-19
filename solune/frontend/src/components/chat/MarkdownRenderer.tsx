/**
 * MarkdownRenderer — renders markdown content with GFM support and celestial styling.
 * Used for AI assistant messages in chat.
 */

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { CopyButton } from '@/components/ui/copy-button';
import { cn } from '@/lib/utils';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export function MarkdownRenderer({ content, className }: MarkdownRendererProps) {
  return (
    <div className={cn('prose prose-sm dark:prose-invert max-w-none break-words', className)}>
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        code: ({ children, className: codeClassName, node: _node, ...rest }) => {
          const match = /language-(\w+)/.exec(codeClassName || '');
          // Block code has a language class or contains newlines; inline code has neither.
          const isInline = !match && !String(children).includes('\n');
          
          if (!isInline && match) {
            const codeContent = String(children).replace(/\n$/, '');
            return (
              <div className="group/code relative my-2 rounded-lg border border-border bg-muted/50">
                <div className="flex items-center justify-between border-b border-border px-3 py-1.5">
                  <span className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                    {match[1]}
                  </span>
                  <CopyButton value={codeContent} label="Copy code" />
                </div>
                <pre className="overflow-x-auto p-3">
                  <code className="text-sm font-mono">{codeContent}</code>
                </pre>
              </div>
            );
          }

          if (!isInline) {
            const codeContent = String(children).replace(/\n$/, '');
            return (
              <div className="group/code relative my-2 rounded-lg border border-border bg-muted/50">
                <div className="flex justify-end px-3 py-1">
                  <CopyButton value={codeContent} label="Copy code" />
                </div>
                <pre className="overflow-x-auto px-3 pb-3">
                  <code className="text-sm font-mono">{codeContent}</code>
                </pre>
              </div>
            );
          }

          return (
            <code className="rounded bg-muted px-1 py-0.5 text-sm font-mono" {...rest}>
              {children}
            </code>
          );
        },
        a: ({ href, children }) => (
          <a
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary underline hover:text-primary/80"
          >
            {children}
          </a>
        ),
        table: ({ children }) => (
          <div className="my-2 overflow-x-auto">
            <table className="min-w-full border-collapse border border-border text-sm">
              {children}
            </table>
          </div>
        ),
        th: ({ children }) => (
          <th className="border border-border bg-muted/30 px-3 py-1.5 text-left font-semibold">
            {children}
          </th>
        ),
        td: ({ children }) => (
          <td className="border border-border px-3 py-1.5">{children}</td>
        ),
      }}
    >
      {content}
    </ReactMarkdown>
    </div>
  );
}
