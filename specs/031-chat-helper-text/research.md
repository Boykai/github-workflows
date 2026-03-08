# Research: Update User Chat Helper Text for Comprehensive UX Guidance

**Feature**: 031-chat-helper-text | **Date**: 2026-03-08

## R1: Placeholder Text Content Strategy — Desktop vs. Mobile Variants

### Context

The spec requires descriptive placeholder copy on desktop (≥1024px) and a shortened variant on mobile (<768px). The current main chat placeholder is "Describe a task, type / for commands, or @ for pipelines..." — already somewhat descriptive but not comprehensive enough per the spec, and not responsive.

### Research Findings

**Current placeholders across the app:**

| Component | Current Placeholder | Context |
|-----------|-------------------|---------|
| ChatInterface (via MentionInput) | "Describe a task, type / for commands, or @ for pipelines..." | Main agent chat — primary interaction point |
| AgentChatFlow | "Type your response…" | Multi-turn agent creation flow — contextual conversation |
| ChoreChatFlow | "Type your response…" | Multi-turn chore template building — contextual conversation |

**Analysis:**
- The main ChatInterface placeholder should be the most descriptive since it's the primary entry point for all user interactions.
- AgentChatFlow and ChoreChatFlow are contextual mini-chats within modals — their placeholder should acknowledge the conversational context ("response") but still be more helpful.
- The main chat supports: task description, slash commands (`/`), @mention pipelines, file uploads, voice input, AI enhance toggle, and natural language queries.

### Decision: Placeholder Copy

**Desktop (main chat, ≥768px):**
> "Ask a question, describe a task, use / for commands, or @ to select a pipeline…"

**Mobile (main chat, <768px):**
> "Ask anything or use / and @ for more…"

**AgentChatFlow (all viewports — small modal input):**
> "Describe what you'd like your agent to do…"

**ChoreChatFlow (all viewports — small modal input):**
> "Add details or refine your request…"

### Rationale
- Desktop copy communicates 4 interaction types (questions, tasks, commands, pipelines) in a single line that fits typical chat input widths (~500px+).
- Mobile copy is concise but still hints at advanced features (`/` and `@`) for discoverability.
- Agent/Chore flow placeholders are context-specific rather than generic "Type your response" — they guide the user on what the system expects.
- Tone is approachable and action-oriented, aligned with Solune's established voice (direct, helpful, not robotic).

### Alternatives Considered
1. **Single placeholder for all viewports**: Rejected — desktop text would truncate on mobile; mobile text would be underwhelming on desktop.
2. **Enumerated list of all features**: Rejected — "Ask questions, create issues, summarize content, run pipelines, upload files, use voice..." is too long and overwhelming.
3. **Question-format placeholder** ("What can I help you with?"): Rejected — doesn't communicate specific capabilities; too similar to generic chatbot patterns.

---

## R2: Responsive Placeholder Implementation — CSS vs. JavaScript Approach

### Context

The MentionInput component renders the placeholder as a custom overlay `<div>` (not a native `<input placeholder>`), which means CSS `::placeholder` pseudo-element cannot be used. The responsive behavior must switch between desktop and mobile copy variants.

### Research Findings

**Current MentionInput placeholder implementation** (`MentionInput.tsx:247-250`):
```tsx
{isEmpty && !disabled && placeholder && (
  <div className="absolute top-0 left-0 p-3 text-sm text-muted-foreground pointer-events-none select-none">
    {placeholder}
  </div>
)}
```

**Approaches evaluated:**

1. **Dual-div with Tailwind responsive classes**: Render two `<div>` elements — one for desktop (hidden on `max-sm:`) and one for mobile (hidden on `sm:`). Pure CSS, no JavaScript, no hydration issues.

2. **JavaScript `useMediaQuery` hook**: Detect viewport width in React state and conditionally render the appropriate string. Adds React state/effect overhead and hydration mismatch risk on SSR.

3. **Single prop with CSS `content` property**: Use CSS `::after` pseudo-element with different `content` values at breakpoints. Rejected — the placeholder is rendered as React children, not CSS content.

### Decision: Dual-div with Tailwind responsive classes

Render both variants in the DOM; use `hidden max-sm:block` for mobile and `max-sm:hidden` for desktop. This follows existing patterns in the codebase (ChatPopup uses `max-sm:` and `max-md:` extensively).

**Implementation approach:**
```tsx
{isEmpty && !disabled && (
  <div className="absolute top-0 left-0 p-3 text-sm text-muted-foreground pointer-events-none select-none">
    {placeholderDesktop && (
      <span className="max-sm:hidden">{placeholderDesktop}</span>
    )}
    {placeholderMobile && (
      <span className="hidden max-sm:inline">{placeholderMobile}</span>
    )}
  </div>
)}
```

### Rationale
- Zero JavaScript overhead — pure CSS solution.
- Follows existing responsive patterns in the codebase (Tailwind `max-sm:` / `max-md:`).
- No hydration mismatch risk.
- Both variants are in the DOM for accessibility — screen readers get the desktop version by default (which is more descriptive).

### Alternatives Considered
1. **`useMediaQuery` hook**: Rejected — adds unnecessary JS state/effect for a static text display; creates hydration mismatch risk; over-engineering.
2. **CSS `content` property**: Rejected — placeholder is a React-rendered `<div>`, not a pseudo-element; would require refactoring MentionInput's placeholder architecture.

---

## R3: WCAG AA Contrast Compliance — Current State and Verification

### Context

The spec requires placeholder text to meet WCAG AA minimum 4.5:1 contrast ratio. The placeholder uses `text-muted-foreground` against the input's `bg-background/76` (with 76% opacity).

### Research Findings

**Current CSS custom property values from `frontend/src/index.css`:**

| Token | Light Mode (HSL) | Dark Mode (HSL) |
|-------|-----------------|-----------------|
| `--muted-foreground` | 228 10% 40% | 35 24% 72% |
| `--background` | 41 82% 95% | 236 28% 7% |

**Contrast ratio calculations:**

- **Light mode**: `hsl(228, 10%, 40%)` on `hsl(41, 82%, 95%)` → ~5.3:1 ✅ (exceeds 4.5:1)
- **Dark mode**: `hsl(35, 24%, 72%)` on `hsl(236, 28%, 7%)` → ~8.7:1 ✅ (exceeds 4.5:1)

**Note on `bg-background/76` opacity**: The MentionInput's parent has `bg-background/76` (76% opacity), which means the effective background blends with whatever is behind it. In practice, the chat popup background (`bg-background border border-border`) is the same `--background` color, so the 76% opacity reduces to a slightly different effective background. The contrast margin is sufficient (5.3:1 and 8.7:1 well exceed 4.5:1) to absorb this opacity variation.

### Decision: No CSS changes needed for contrast compliance

The existing `text-muted-foreground` color meets WCAG AA 4.5:1 in both light and dark modes with sufficient margin. No color token changes are required.

### Rationale
- Measured contrast ratios exceed the 4.5:1 minimum by comfortable margins.
- The `text-muted-foreground` token is used consistently across the codebase for secondary/placeholder text — changing it would have cascading effects.
- The opacity variation from `bg-background/76` does not bring the contrast below 4.5:1.

### Alternatives Considered
1. **Custom `text-placeholder` color token**: Rejected — unnecessary given existing compliance; would add a design token that deviates from the established system.
2. **Higher contrast `text-foreground` color**: Rejected — would make placeholder text too prominent, competing visually with user-entered text.

---

## R4: Cycling Placeholder Animation — Feasibility and Accessibility

### Context

User Story 5 (P3) requests cycling contextual placeholder examples that animate through different prompts. The MentionInput uses a custom contentEditable div with an absolutely positioned overlay for the placeholder — not a native input.

### Research Findings

**Technical feasibility:**
- The placeholder is a React-rendered `<div>` with text content. Cycling requires JavaScript to change the text at intervals.
- A custom `useCyclingPlaceholder` hook can manage a timer that rotates through an array of example prompts.
- CSS transitions (`opacity` or `transform`) can provide smooth fade/slide effects on text change.
- `prefers-reduced-motion` media query must be respected — users who prefer reduced motion should see the static placeholder instead.

**Accessibility concerns:**
- **Screen readers**: Cycling text must NOT trigger repeated `aria-live` announcements. The placeholder overlay has `pointer-events-none` and no ARIA role — screen readers should not announce visual-only placeholder cycling. The actual `aria-label` on the contentEditable div remains stable.
- **Cognitive load**: Rapid cycling can be distracting. A 5-second interval with a slow fade (300ms) is standard practice.
- **Focus behavior**: Cycling must stop immediately when the input receives focus and resume only when the input is empty and unfocused.

**Implementation sketch:**
```tsx
function useCyclingPlaceholder(prompts: string[], intervalMs = 5000): string {
  const [index, setIndex] = useState(0);
  const prefersReducedMotion = useRef(
    window.matchMedia('(prefers-reduced-motion: reduce)').matches
  );

  useEffect(() => {
    if (prefersReducedMotion.current || prompts.length <= 1) return;
    const timer = setInterval(() => {
      setIndex((prev) => (prev + 1) % prompts.length);
    }, intervalMs);
    return () => clearInterval(timer);
  }, [prompts.length, intervalMs]);

  return prompts[prefersReducedMotion.current ? 0 : index];
}
```

### Decision: Implement as P3 optional enhancement with `prefers-reduced-motion` fallback

The cycling placeholder is technically feasible and can be implemented as a standalone hook without new dependencies. It should:
- Cycle through 4–5 example prompts at 5-second intervals.
- Use a CSS `opacity` transition for smooth fade between prompts.
- Stop cycling when the input is focused or non-empty.
- Fall back to the static desktop placeholder when `prefers-reduced-motion: reduce` is active.
- NOT affect the `aria-label` or any other accessibility attribute — only the visual placeholder overlay cycles.

### Rationale
- Self-contained implementation in a single hook + CSS transition — no new dependencies.
- `prefers-reduced-motion` check ensures accessibility compliance.
- 5-second interval balances discoverability with cognitive load.
- P3 priority means it can be deferred without blocking the core P1/P2 deliverables.

### Alternatives Considered
1. **CSS-only `@keyframes` animation**: Rejected — the placeholder is React-rendered text content, not a CSS pseudo-element; `@keyframes` cannot change DOM text content.
2. **Third-party animation library (framer-motion)**: Rejected — over-engineering for a single text fade; adds bundle weight for one feature.
3. **No cycling — always static**: Acceptable fallback if P3 is deprioritized. The static placeholder from R1 already communicates key capabilities.
