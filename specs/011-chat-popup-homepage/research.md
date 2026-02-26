# Research: Move Chat Experience to Project-Board Page as Pop-Up Module & Simplify Homepage

**Date**: 2026-02-26 | **Branch**: `011-chat-popup-homepage` | **Plan**: [plan.md](plan.md)

## R1: Chat Component Extraction Strategy (FR-001, FR-003, FR-005)

**Decision**: Wrap the existing `ChatInterface` component inside a new `ChatPopup` container component, rather than modifying `ChatInterface` itself.

**Rationale**: `ChatInterface` is a fully functional, self-contained chat UI (message history, input field, send button, task previews, status change previews, issue recommendation previews). It accepts all data and callbacks via props. Wrapping it in a `ChatPopup` preserves 100% of existing functionality without touching any chat logic. The `ChatPopup` manages only the open/closed toggle state and floating overlay positioning.

**Alternatives considered**:
- Modify `ChatInterface` to add built-in toggle: Would couple toggle UI concerns into the chat component, violating single-responsibility. Other future consumers of ChatInterface would inherit unwanted toggle behavior.
- Create a generic `FloatingPanel` component: Premature abstraction — only one use case exists. YAGNI per constitution principle V.
- Use a dialog/modal library (e.g., Radix, Headless UI): Adds a dependency for a simple show/hide panel. CSS transitions are sufficient.

**Implementation approach**:
- New file: `frontend/src/components/chat/ChatPopup.tsx`
- Component accepts all `ChatInterface` props plus manages its own `isOpen` state via `useState`.
- Renders a floating toggle button (chat bubble icon) in fixed position (bottom-right, 24px offset).
- When open, renders a panel containing `<ChatInterface {...chatProps} />`.
- Panel uses CSS transitions for open/close animation.

---

## R2: State Management for Chat Pop-Up Toggle (FR-006)

**Decision**: Use local `useState<boolean>` within the `ChatPopup` component for open/closed state. No global state store needed.

**Rationale**: The spec requires state persistence "for the duration of the user's session on the project-board page." Since `ChatPopup` is rendered inside `ProjectBoardPage`, and `ProjectBoardPage` persists as long as the user is on the board view (controlled by `activeView` state in `App.tsx`), local component state naturally persists across re-renders. React preserves state for components that remain mounted in the same position in the tree.

**Alternatives considered**:
- Global state (Context, Zustand, or Jotai): Overkill — the toggle is needed only within the project-board page. Adding global state for a single boolean violates YAGNI.
- sessionStorage: Would persist across page refreshes, which exceeds the spec requirement ("duration of the user's session on the project-board page"). Also adds serialization overhead.
- Lift state to `App.tsx`: Unnecessary coupling — `App.tsx` doesn't need to know about chat pop-up visibility.

**Implementation approach**:
- `const [isOpen, setIsOpen] = useState(false)` inside `ChatPopup`.
- Toggle via `setIsOpen(prev => !prev)` on button click.
- State survives re-renders of parent `ProjectBoardPage` since `ChatPopup` stays mounted.

---

## R3: Animation Approach for Open/Close Transition (FR-008)

**Decision**: Use CSS transitions on `transform` and `opacity` properties for the chat pop-up panel, triggered by a CSS class toggle.

**Rationale**: CSS transitions are hardware-accelerated, require zero JavaScript runtime overhead, and no additional dependencies. The project does not currently use Framer Motion or any animation library, and adding one for a single open/close animation violates the constitution's simplicity principle. All existing transitions in the codebase use CSS (e.g., `transition: background 0.15s ease` in `index.css` buttons, `transition: all 0.15s ease` in nav buttons).

**Alternatives considered**:
- Framer Motion: Powerful but adds ~30KB to bundle for one animation. Not justified.
- CSS `@keyframes` animation: Slightly more complex to manage in conjunction with React state — transitions are simpler for binary state changes (open/closed).
- JavaScript-driven animation (requestAnimationFrame): Unnecessary complexity, worse performance than CSS transitions.

**Implementation approach**:
- Panel has base CSS: `transform: scale(0.95) translateY(10px); opacity: 0; transition: transform 0.2s ease, opacity 0.2s ease;`
- When open class applied: `transform: scale(1) translateY(0); opacity: 1;`
- Use `pointer-events: none` when closed to prevent interaction with invisible panel.
- Toggle button itself uses a subtle scale animation on hover.

---

## R4: Chat Prop Drilling vs. Hook Relocation (FR-005, FR-011)

**Decision**: Move `useChat()` and `useWorkflow()` hook invocations from `App.tsx` into `ProjectBoardPage`, so chat API calls only execute when the board page is active.

**Rationale**: Currently, `useChat()` is called in `App.tsx` unconditionally — the `useQuery` for messages fires regardless of which view (chat, board, settings) is active. Moving the hooks into `ProjectBoardPage` ensures no chat-related API calls occur on the homepage (FR-011) and keeps chat data co-located with its only consumer.

**Alternatives considered**:
- Keep hooks in `App.tsx` and conditionally skip them: React hooks cannot be called conditionally. Would need `enabled: activeView === 'board'` on the query, but this still initializes the hook and its state on every render.
- Pass all chat props from `App.tsx` through `ProjectBoardPage`: Requires `ProjectBoardPage` to accept ~15+ props for chat functionality. Ugly prop explosion.
- Create a ChatProvider context: Adds architectural complexity for a single consumer. Premature.

**Implementation approach**:
- Remove `useChat()`, `useWorkflow()`, and all chat-related state/callbacks from `App.tsx`.
- Add `useChat()` and `useWorkflow()` inside `ProjectBoardPage`.
- `ProjectBoardPage` passes chat props to `ChatPopup`, which passes them to `ChatInterface`.
- `App.tsx` homepage view becomes a simple static JSX block with no hooks or dynamic state.

---

## R5: Homepage CTA Navigation (FR-002, FR-009)

**Decision**: The "Create Your App Here" CTA on the simplified homepage calls `setActiveView('board')` to switch to the project-board view, using the existing in-app view switching mechanism.

**Rationale**: The app uses a single-page architecture with `activeView` state (not a router). Navigation between views is done via `setActiveView()`. Using this existing pattern is consistent and requires zero new infrastructure.

**Alternatives considered**:
- Add React Router: Major architectural change for a simple view switch. Completely out of scope.
- Use an anchor link: No route to link to — the app is a single-page with state-driven views.

**Implementation approach**:
- Homepage view: `<button onClick={() => setActiveView('board')}>Create Your App Here</button>` or a clickable heading.
- Styled as a prominent hero CTA with centered layout.

---

## R6: Responsive Design for Chat Pop-Up (FR-010)

**Decision**: Use CSS media queries to adjust the chat pop-up dimensions on mobile viewports. On screens ≤768px, the pop-up expands to near-full-width; on screens ≤480px, it fills the viewport.

**Rationale**: The existing codebase uses standard CSS media queries for responsive behavior (observed in `App.css`). No CSS-in-JS or responsive utility framework is in use. The chat pop-up fixed positioning must adapt to prevent overflow on small screens.

**Alternatives considered**:
- Container queries: Not yet universally supported and not used elsewhere in the codebase.
- JavaScript-based resize detection: Unnecessary when CSS media queries achieve the same result with zero runtime cost.

**Implementation approach**:
- Desktop (>768px): Pop-up is 400px wide × 500px tall, positioned bottom-right with 24px offset.
- Tablet (≤768px): Pop-up is calc(100vw - 48px) wide, positioned bottom-center.
- Mobile (≤480px): Pop-up fills viewport width and 70% of height, positioned at bottom.
- Toggle button remains fixed bottom-right on all viewports.
