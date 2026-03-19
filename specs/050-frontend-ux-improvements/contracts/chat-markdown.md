# Contract: Chat Markdown & Code Blocks (Phase 2)

**Feature**: 050-frontend-ux-improvements  
**Requirements**: FR-006 through FR-010  
**Dependencies**: `react-markdown` ^10.1.0 (existing), `remark-gfm` ^4.0.1 (existing)

## Component Contracts

### `MessageBubble.tsx` Modification

**Location**: `solune/frontend/src/components/chat/MessageBubble.tsx`  
**Action**: Conditionally render AI messages through ReactMarkdown.

```tsx
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { CodeBlock } from './CodeBlock';
import { CopyMessageAction } from './CopyMessageAction';

// In the AI message rendering branch:
{message.role === 'assistant' ? (
  <div className="group relative">
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        code: CodeBlock,
        a: ({ href, children }) => (
          <a href={href} target="_blank" rel="noopener noreferrer"
             className="text-primary underline hover:text-primary/80">
            {children}
          </a>
        ),
      }}
    >
      {message.content}
    </ReactMarkdown>
    <CopyMessageAction content={message.content} />
  </div>
) : (
  // User messages: plain text (FR-009)
  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
)}
```

### `CodeBlock.tsx` (NEW)

**Location**: `solune/frontend/src/components/chat/CodeBlock.tsx`  
**Props**:

```tsx
interface CodeBlockProps {
  children?: React.ReactNode;
  className?: string;    // Contains "language-xxx" from markdown
  inline?: boolean;
}
```

**Behavior**:
- Inline code (`inline={true}`): Render as `<code>` with `bg-muted px-1 rounded text-sm font-mono` styling.
- Block code (`inline={false}`): Render in a container with:
  - Language label (extracted from `className`)
  - Copy button (top-right corner)
  - Scrollable `<pre><code>` with `bg-muted/50 rounded-lg p-4 font-mono text-sm`
  - Copy feedback: Button text changes to "Copied!" for 2 seconds after click

```tsx
// Copy handler:
const handleCopy = async () => {
  await navigator.clipboard.writeText(codeContent);
  setCopied(true);
  setTimeout(() => setCopied(false), 2000);
};
```

### `CopyMessageAction.tsx` (NEW)

**Location**: `solune/frontend/src/components/chat/CopyMessageAction.tsx`  
**Props**:

```tsx
interface CopyMessageActionProps {
  content: string;       // Raw markdown content to copy
}
```

**Behavior**:
- Renders a "Copy message" button that appears on hover (via `group-hover:opacity-100` from parent's `group` class).
- Positioned at top-right of the message bubble.
- Uses `navigator.clipboard.writeText(content)` to copy raw markdown.
- Shows "Copied!" feedback for 2 seconds.

## Security

- FR-010: `react-markdown` strips HTML by default. The `rehype-raw` plugin MUST NOT be added. This prevents XSS from AI-generated content containing malicious HTML.
- Links open in new tabs with `rel="noopener noreferrer"` to prevent tabnapping.

## Styling Notes

- Markdown prose styling uses the existing `@tailwindcss/typography` plugin (installed) with `prose prose-sm` classes.
- Code blocks inherit the celestial theme: `bg-muted/50` background, `border border-border` separator, `text-foreground` text color.
- GFM tables render with `border-collapse` and `border border-border` styling.
