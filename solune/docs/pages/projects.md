# Projects

The Projects page is the main workspace in Solune. It displays your GitHub project issues on a Kanban board where you can drag cards between columns, view issue details, assign pipelines, and track real-time updates.

## What You See

- **Kanban board** — issues are organized into columns by status (e.g., Backlog, In Progress, Done)
- **Issue cards** — each card shows an issue title, labels, and assignees. Click a card to open full details
- **Toolbar** — controls at the top of the board for filtering, sorting, and grouping issues
- **Pipeline stages** — when a pipeline is assigned, its stages are shown above the columns so you can see which agent handles each status
- **Sync indicator** — a real-time connection status showing whether the board is receiving live updates
- **Rate limit indicator** — shows how much of your GitHub API quota remains

## How to Use It

### Selecting a Project

If no project is selected, you will see a prompt to pick one. Use the project selector in the sidebar to choose which GitHub project to view.

### Moving Issues

Drag and drop issue cards between columns to change their status. The change takes effect immediately and syncs with GitHub.

### Viewing Issue Details

Click any issue card to open a detail modal where you can see the full description, comments, labels, and assignee information.

### Filtering and Sorting

Use the toolbar to:

- **Filter** — narrow down issues by label, assignee, or other criteria
- **Sort** — reorder issues within columns (e.g., by date, priority)
- **Group by** — change how issues are grouped across the board

Your filter and sort preferences are saved per project and persist across page reloads.

### Assigning a Pipeline

Use the pipeline dropdown in the toolbar to assign a saved pipeline to the board. Once assigned, the pipeline's stage labels appear above each column, and AI agents will process issues as they move through stages.

### Toggling Queue Mode and Auto-Merge

- **Queue mode** — when enabled, issues move through the board sequentially instead of in parallel
- **Auto-merge** — when enabled, pull requests for completed issues are merged automatically when they reach the Done column

### Creating Issues

Use the issue launch panel to create new issues or ask the chat agent to propose one. Draft issues are started in the chat and can be refined before submission.

### Cleanup

Click the cleanup button to audit and clean up stale branches, old issues, or other project artifacts. You can also view past cleanup operations in the audit history.

### Refreshing the Board

Click the refresh button to pull the latest data from GitHub. The button also shows your remaining API quota — if the quota is low, automatic refreshes slow down to conserve it.

## Tips

- The board updates in real time via a live connection. You usually do not need to refresh manually.
- If you see a yellow or red rate limit bar, avoid excessive refreshing — the quota resets automatically.
- Your board view (filters, sort order) is remembered per project, so switching projects restores your previous view.
