/**
 * MentionInput component — contentEditable div replacing the textarea.
 * Supports inline @mention token spans alongside plain text.
 */

import { useState, useRef, useEffect, useCallback, useImperativeHandle, forwardRef } from 'react';
import { cn } from '@/lib/utils';
import { MENTION_TOKEN_VALID } from '@/hooks/useMentionAutocomplete';

export interface MentionInputHandle {
  focus: () => void;
  clear: () => void;
  getPlainText: () => string;
  getElement: () => HTMLDivElement | null;
  moveCursorToEnd: () => void;
  isCaretOnFirstLine: () => boolean;
  isCaretOnLastLine: () => boolean;
  insertTokenAtCursor: (
    pipelineId: string,
    pipelineName: string,
    triggerOffset: number,
    queryLength: number
  ) => void;
}

interface MentionInputProps {
  value: string;
  placeholder?: string;
  placeholderMobile?: string;
  cyclingPlaceholder?: string;
  ariaLabel?: string;
  onFocusChange?: (isFocused: boolean) => void;
  disabled?: boolean;
  isNavigating?: boolean;
  onTextChange: (text: string) => void;
  onTokenRemove?: (pipelineId: string) => void;
  onMentionTrigger: (query: string, offset: number) => void;
  onMentionDismiss: () => void;
  onSubmit: () => void;
  onKeyDown?: (e: React.KeyboardEvent) => void;
}

export const MentionInput = forwardRef<MentionInputHandle, MentionInputProps>(
  function MentionInput(
    {
      value,
      placeholder,
      placeholderMobile,
      cyclingPlaceholder,
      ariaLabel,
      onFocusChange,
      disabled,
      isNavigating,
      onTextChange,
      onTokenRemove,
      onMentionTrigger,
      onMentionDismiss,
      onSubmit,
      onKeyDown,
    },
    ref,
  ) {
    const divRef = useRef<HTMLDivElement>(null);
    const isComposingRef = useRef(false);
    const [isEmpty, setIsEmpty] = useState(true);

    // Expose imperative handle
    useImperativeHandle(ref, () => ({
      focus() {
        divRef.current?.focus();
      },
      clear() {
        if (divRef.current) {
          divRef.current.innerHTML = '';
          onTextChange('');
          setIsEmpty(true);
        }
      },
      getPlainText() {
        return extractPlainText(divRef.current);
      },
      getElement() {
        return divRef.current;
      },
      moveCursorToEnd() {
        moveCursorToEnd(divRef.current);
      },
      isCaretOnFirstLine() {
        return isCaretOnFirstLine(divRef.current);
      },
      isCaretOnLastLine() {
        return isCaretOnLastLine(divRef.current);
      },
      insertTokenAtCursor(pipelineId: string, pipelineName: string, triggerOffset: number, queryLength: number) {
        insertToken(divRef.current, pipelineId, pipelineName, triggerOffset, queryLength);
        onTextChange(extractPlainText(divRef.current));
        setIsEmpty(false);
      },
    }));

    // Focus on mount
    useEffect(() => {
      divRef.current?.focus();
  }, []);

    // Sync isEmpty when value prop changes (render-time adjustment)
    const [prevValue, setPrevValue] = useState(value);
    if (value !== prevValue) {
      setPrevValue(value);
      setIsEmpty(!value.trim());
    }

  useEffect(() => {
    const el = divRef.current;
    if (!el) return;

    const currentText = extractPlainText(el);
    if (currentText === value) return;

    setPlainTextContent(el, value);
  }, [value]);

  const handleInput = useCallback(() => {
    if (isComposingRef.current) return;
    const el = divRef.current;
    if (!el) return;

    const text = extractPlainText(el);
    onTextChange(text);
    setIsEmpty(!text.trim());

    // Check for @ trigger
    const sel = window.getSelection();
    if (!sel || sel.rangeCount === 0) return;

    const range = sel.getRangeAt(0);
    // Only detect in text nodes
    if (range.startContainer.nodeType !== Node.TEXT_NODE) return;

    const textNode = range.startContainer as Text;
    const textContent = textNode.textContent || '';
    const cursorPos = range.startOffset;

    // Walk backwards from cursor to find the @ trigger
    let atPos = -1;
    for (let i = cursorPos - 1; i >= 0; i--) {
      const ch = textContent[i];
      if (ch === '@') {
        // Check that @ is preceded by space, newline, or is at position 0
        if (i === 0) {
          atPos = i;
        } else {
          const prevChar = textContent[i - 1];
          if (prevChar === ' ' || prevChar === '\n' || prevChar === '\r') {
            atPos = i;
          }
        }
        break;
      }
      // Stop scanning if we hit a space or newline (no @ trigger)
      if (ch === ' ' || ch === '\n' || ch === '\r') break;
    }

    if (atPos >= 0) {
      const query = textContent.slice(atPos + 1, cursorPos);
      // Calculate absolute offset: walk sibling text nodes to find the absolute position
      const absoluteOffset = getAbsoluteOffset(el, textNode, atPos);
      onMentionTrigger(query, absoluteOffset);
    } else {
      onMentionDismiss();
    }
  }, [onTextChange, onMentionTrigger, onMentionDismiss]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLDivElement>) => {
      // Let the parent handle autocomplete keys first
      if (onKeyDown) {
        onKeyDown(e);
        if (e.defaultPrevented) return;
      }

      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        onSubmit();
      }

      // Handle backspace into token: when the cursor is right after a token span,
      // remove the entire token
      if (e.key === 'Backspace') {
        const sel = window.getSelection();
        if (sel && sel.rangeCount > 0 && sel.isCollapsed) {
          const range = sel.getRangeAt(0);
          const container = range.startContainer;

          // Case 1: Cursor is at position 0 in a text node, check previous sibling
          if (container.nodeType === Node.TEXT_NODE && range.startOffset === 0) {
            const prevSibling = container.previousSibling;
            if (
              prevSibling &&
              prevSibling instanceof HTMLElement &&
              prevSibling.hasAttribute('data-mention-token')
            ) {
              e.preventDefault();
              const removedPipelineId = prevSibling.getAttribute('data-pipeline-id');
              prevSibling.remove();
              onTextChange(extractPlainText(divRef.current));
              if (removedPipelineId) onTokenRemove?.(removedPipelineId);
              setIsEmpty(!extractPlainText(divRef.current).trim());
              return;
            }
          }

          // Case 2: Cursor is in the parent div between child nodes
          if (container === divRef.current && range.startOffset > 0) {
            const prevNode = container.childNodes[range.startOffset - 1];
            if (
              prevNode &&
              prevNode instanceof HTMLElement &&
              prevNode.hasAttribute('data-mention-token')
            ) {
              e.preventDefault();
              const removedPipelineId = prevNode.getAttribute('data-pipeline-id');
              prevNode.remove();
              onTextChange(extractPlainText(divRef.current));
              if (removedPipelineId) onTokenRemove?.(removedPipelineId);
              setIsEmpty(!extractPlainText(divRef.current).trim());
              return;
            }
          }
        }
      }
    },
    [onKeyDown, onSubmit, onTextChange, onTokenRemove],
  );

  const handlePaste = useCallback(
    (e: React.ClipboardEvent) => {
      e.preventDefault();
      const text = e.clipboardData.getData('text/plain');
      document.execCommand('insertText', false, text);
    },
    [],
  );

  // Show/hide placeholder — use local state rather than DOM queries

  return (
    <div className="relative">
      <div
        ref={divRef}
        contentEditable={!disabled}
        role="textbox"
        tabIndex={0}
        aria-multiline="true"
        aria-label={ariaLabel || "Chat input"}
        suppressContentEditableWarning
        onFocus={() => onFocusChange?.(true)}
        onBlur={() => onFocusChange?.(false)}
        onInput={handleInput}
        onKeyDown={handleKeyDown}
        onPaste={handlePaste}
        onCompositionStart={() => { isComposingRef.current = true; }}
        onCompositionEnd={() => {
          isComposingRef.current = false;
          handleInput();
        }}
        className={cn(
          'w-full min-h-[52px] max-h-[400px] overflow-y-auto rounded-xl border border-border bg-background/76 p-3 text-sm font-inherit leading-relaxed text-foreground outline-none transition-colors focus:border-primary disabled:bg-muted whitespace-pre-wrap break-words',
          isNavigating && 'border-l-4 border-l-primary bg-primary/5',
          disabled && 'bg-muted pointer-events-none opacity-60',
        )}
      />
      {isEmpty && !disabled && placeholder && (
        <div className="absolute top-0 left-0 p-3 text-sm text-muted-foreground pointer-events-none select-none">
          {placeholderMobile ? (
            <>
              <span className="max-sm:hidden">
                {cyclingPlaceholder ? (
                  <span key={cyclingPlaceholder} className="inline-block animate-[fadeIn_0.3s_ease-in] motion-reduce:animate-none">{cyclingPlaceholder}</span>
                ) : (
                  placeholder
                )}
              </span>
              <span className="hidden max-sm:inline">{placeholderMobile}</span>
            </>
          ) : (
            cyclingPlaceholder || placeholder
          )}
        </div>
      )}
    </div>
  );
  },
);

/**
 * Extract plain text from the contentEditable div.
 * Token spans are replaced by their display text.
 */
function extractPlainText(el: HTMLDivElement | null): string {
  if (!el) return '';
  let text = '';
  for (const node of el.childNodes) {
    if (node.nodeType === Node.TEXT_NODE) {
      text += node.textContent || '';
    } else if (node instanceof HTMLElement) {
      if (node.hasAttribute('data-mention-token')) {
        // Replace token with @name placeholder
        const name = node.getAttribute('data-pipeline-name') || '';
        text += `@${name}`;
      } else if (node.tagName === 'BR') {
        text += '\n';
      } else {
        text += node.textContent || '';
      }
    }
  }
  return text;
}

/**
 * Calculate the absolute character offset of a position within a text node
 * relative to the contentEditable container.
 */
function getAbsoluteOffset(
  container: HTMLDivElement,
  targetNode: Text,
  localOffset: number
): number {
  let offset = 0;
  for (const node of container.childNodes) {
    if (node === targetNode) {
      return offset + localOffset;
    }
    if (node.nodeType === Node.TEXT_NODE) {
      offset += (node.textContent || '').length;
    } else if (node instanceof HTMLElement) {
      if (node.hasAttribute('data-mention-token')) {
        const name = node.getAttribute('data-pipeline-name') || '';
        offset += name.length + 1; // +1 for the @
      } else {
        offset += (node.textContent || '').length;
      }
    }
  }
  return offset + localOffset;
}

/**
 * Insert a mention token span at the trigger position, replacing the @query text.
 */
function insertToken(
  container: HTMLDivElement | null,
  pipelineId: string,
  pipelineName: string,
  triggerOffset: number,
  queryLength: number
): void {
  if (!container) return;

  const sel = window.getSelection();
  if (!sel || sel.rangeCount === 0) return;

  // Create the token span
  const span = document.createElement('span');
  span.contentEditable = 'false';
  span.setAttribute('data-pipeline-id', pipelineId);
  span.setAttribute('data-pipeline-name', pipelineName);
  span.setAttribute('data-mention-token', '');
  span.className = MENTION_TOKEN_VALID;
  span.textContent = `@${pipelineName}`;

  if (!replaceQueryRangeWithToken(container, span, triggerOffset, queryLength + 1, sel)) {
    replaceSelectionWithToken(sel, span);
  }
}

function setPlainTextContent(el: HTMLDivElement, text: string): void {
  if (!text) {
    el.innerHTML = '';
    return;
  }
  el.textContent = text;
}

function moveCursorToEnd(container: HTMLDivElement | null): void {
  if (!container) return;
  const selection = window.getSelection();
  if (!selection) return;

  const range = document.createRange();
  range.selectNodeContents(container);
  range.collapse(false);
  selection.removeAllRanges();
  selection.addRange(range);
}

function isCaretOnFirstLine(container: HTMLDivElement | null): boolean {
  const offset = getCaretOffset(container);
  if (offset === null || !container) return true;
  return !extractPlainText(container).slice(0, offset).includes('\n');
}

function isCaretOnLastLine(container: HTMLDivElement | null): boolean {
  const offset = getCaretOffset(container);
  if (offset === null || !container) return true;
  return !extractPlainText(container).slice(offset).includes('\n');
}

function getCaretOffset(container: HTMLDivElement | null): number | null {
  if (!container) return null;

  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0) return null;

  const range = selection.getRangeAt(0);
  if (!container.contains(range.startContainer)) return null;

  const preCaretRange = range.cloneRange();
  preCaretRange.selectNodeContents(container);
  preCaretRange.setEnd(range.startContainer, range.startOffset);
  return preCaretRange.toString().length;
}

function replaceQueryRangeWithToken(
  container: HTMLDivElement,
  token: HTMLElement,
  startOffset: number,
  length: number,
  selection: Selection
): boolean {
  const start = locateTextPosition(container, startOffset);
  const end = locateTextPosition(container, startOffset + length);
  if (!start || !end || start.node !== end.node) {
    return false;
  }

  const textNode = start.node;
  const originalText = textNode.textContent || '';
  const beforeText = originalText.slice(0, start.offset);
  const afterText = originalText.slice(end.offset);
  textNode.textContent = beforeText;

  const parent = textNode.parentNode;
  if (!parent) return false;

  const nextSibling = textNode.nextSibling;
  parent.insertBefore(token, nextSibling);

  let caretNode: Text | null = null;
  if (afterText) {
    caretNode = document.createTextNode(afterText);
    parent.insertBefore(caretNode, token.nextSibling);
  }

  const newRange = document.createRange();
  if (caretNode) {
    newRange.setStart(caretNode, 0);
  } else {
    newRange.setStartAfter(token);
  }
  newRange.collapse(true);
  selection.removeAllRanges();
  selection.addRange(newRange);
  return true;
}

function replaceSelectionWithToken(selection: Selection, token: HTMLElement): void {
  const range = selection.getRangeAt(0);
  range.deleteContents();
  range.insertNode(token);

  const newRange = document.createRange();
  newRange.setStartAfter(token);
  newRange.collapse(true);
  selection.removeAllRanges();
  selection.addRange(newRange);
}

function locateTextPosition(
  container: HTMLDivElement,
  absoluteOffset: number
): { node: Text; offset: number } | null {
  let remaining = absoluteOffset;
  let lastTextNode: Text | null = null;

  for (const node of container.childNodes) {
    if (node.nodeType === Node.TEXT_NODE) {
      const textNode = node as Text;
      const length = textNode.textContent?.length ?? 0;
      lastTextNode = textNode;
      if (remaining <= length) {
        return { node: textNode, offset: remaining };
      }
      remaining -= length;
      continue;
    }

    if (node instanceof HTMLElement && node.hasAttribute('data-mention-token')) {
      const tokenLength = (node.getAttribute('data-pipeline-name') || '').length + 1;
      if (remaining <= tokenLength) {
        return null;
      }
      remaining -= tokenLength;
    }
  }

  if (lastTextNode) {
    return { node: lastTextNode, offset: lastTextNode.textContent?.length ?? 0 };
  }

  const textNode = document.createTextNode('');
  container.appendChild(textNode);
  return { node: textNode, offset: 0 };
}
