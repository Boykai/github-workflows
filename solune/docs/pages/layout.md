# Layout and Navigation

Every page in Solune (except Login) shares a consistent layout with a sidebar, top bar, chat panel, and search palette. This guide explains the elements you see on every screen and how to use them.

## Sidebar

The sidebar is the main way to navigate between pages. It lives on the left side of the screen.

**What you can do:**

- **Navigate** — click any item to jump to that page (Projects, Pipeline, Agents, Tools, Chores, Settings, Apps, Activity, Help)
- **Switch projects** — click the project selector at the top of the sidebar to choose which GitHub project you are working with, or create a new one
- **View recent issues** — the bottom of the sidebar shows your most recent parent issues, color-coded by status, so you can quickly jump back to something you were working on
- **Toggle theme** — click the sun/moon icon to switch between light and dark mode
- **Collapse/expand** — click the toggle arrow to collapse the sidebar to icons only, giving you more screen space. On mobile, the sidebar appears as a full-screen overlay

## Top Bar

The top bar sits across the top of every page and provides context and quick actions.

| Element | What It Does |
|---------|--------------|
| **Breadcrumb** | Shows where you are (e.g., Home > Apps > MyApp). Click a parent segment to jump back |
| **Search (Ctrl+K)** | Opens the Command Palette for quick navigation. You can also click the search icon |
| **Help button** | Jumps directly to the Help page |
| **Notification bell** | Shows unread notifications with a badge count. Click to open the dropdown, then "Mark all read" to clear them |
| **Rate limit bar** | Displays your GitHub API usage. Green means plenty of quota remaining; yellow is moderate; red means you are near the limit |
| **Profile** | Shows your GitHub avatar and username |

## Chat Panel

A floating chat panel is available on every page, accessible from the bottom-right corner. It stays open as you navigate between pages — your conversation is never lost.

**What you can do:**

- **Talk to AI agents** — type a message or use `@agentname` to direct a question to a specific agent
- **Use slash commands** — type `/` to see available commands (e.g., `/help`, `/theme`, `/clear`)
- **Voice input** — click the microphone button to dictate messages
- **Attach files** — drag or paste files into the chat for context
- **Review proposals** — when an agent proposes an issue or status change, you can accept or reject it directly in the chat

## Command Palette

Press **Ctrl+K** (or **Cmd+K** on Mac) to open the Command Palette. This is the fastest way to get around Solune.

**What you can do:**

- **Search pages** — type a page name to jump there instantly
- **Run actions** — access common actions without navigating to a specific page
- **Keyboard navigation** — use arrow keys to move through results and Enter to select

## Onboarding Tour

The first time you use Solune, a guided tour highlights key parts of the interface step by step. Each step spotlights a UI element and explains what it does.

- **Navigate the tour** — use Next, Previous, or Skip at each step
- **Replay anytime** — go to the Help page and click "Replay Tour" to start the tour again

## Notifications

The notification bell in the top bar keeps you informed of important events.

- A **badge** shows the number of unread notifications
- Click the bell to open the **dropdown** with your notification list
- Each notification shows a dot indicator — filled for unread, empty for read
- Click **"Mark all read"** to clear the unread count
- Press **Escape** or click outside the dropdown to close it

## Project Selector

The project selector in the sidebar lets you switch between your GitHub projects.

**How to use it:**

1. Click the current project name in the sidebar
2. Choose a project from the dropdown list (a checkmark shows the active one)
3. To create a new project, fill in the title and owner fields and submit

Switching projects updates the board, pipelines, agents, chores, and all project-scoped data across every page.

## Theme

Solune supports light and dark mode. Toggle between them using the sun/moon icon in the sidebar. Your preference is saved and restored on your next visit.
