# Component Contracts: Homepage Hero & Navigation Changes

**Feature**: 011-chat-popup-homepage  
**Date**: 2026-02-26

## Homepage Hero Section (inline in App.tsx)

### Purpose
Replace the former chat view with a minimal homepage displaying only a centered "Create Your App Here" CTA heading.

### Render Contract

```tsx
{activeView === 'home' && (
  <section className="homepage-hero">
    <h2 className="homepage-hero-title">Create Your App Here</h2>
    <p className="homepage-hero-subtitle">
      Get started by heading to your project board
    </p>
    <button
      className="homepage-hero-cta"
      onClick={() => setActiveView('board')}
    >
      Go to Project Board →
    </button>
  </section>
)}
```

### CSS Contract

```css
.homepage-hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  gap: 16px;
}

.homepage-hero-title {
  font-size: 48px;
  font-weight: 700;
  color: var(--color-text);
}

.homepage-hero-cta {
  background: var(--color-primary);
  color: white;
  padding: 12px 32px;
  font-size: 16px;
  border-radius: var(--radius);
}

/* Mobile */
@media (max-width: 767px) {
  .homepage-hero-title {
    font-size: 32px;
  }
}
```

## Navigation Changes (App.tsx header)

### Before
```
[Chat] [Project Board] [Settings]
```

### After
```
[Home] [Project Board] [Settings]
```

### Changes
- Rename "Chat" button to "Home"
- Change `onClick` from `setActiveView('chat')` to `setActiveView('home')`
- Update `className` active check from `=== 'chat'` to `=== 'home'`
- Default `activeView` initial state changes from `'chat'` to `'home'`

## App.tsx Import Changes

### Removed imports
```typescript
// REMOVE these from App.tsx:
import { useChat } from '@/hooks/useChat';
import { useWorkflow } from '@/hooks/useWorkflow';
import { ProjectSidebar } from '@/components/sidebar/ProjectSidebar';
import { ChatInterface } from '@/components/chat/ChatInterface';
```

### Removed state/logic
```typescript
// REMOVE: useChat() call and all related destructuring
// REMOVE: useWorkflow() call and related destructuring  
// REMOVE: handleConfirmProposal function
// REMOVE: All chat-related JSX in the 'chat' view branch
```

## ProjectBoardPage Changes

### Added imports
```typescript
import { ChatPopup } from '@/components/chat/ChatPopup';
```

### Added render
```tsx
// At the end of the ProjectBoardPage return, before closing </div>:
<ChatPopup
  selectedProjectId={selectedProjectId}
  onTasksRefresh={() => selectProject(selectedProjectId!)}
/>
```
