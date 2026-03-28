# Activity

The Activity page shows a timeline of everything that has happened across your project — pipeline runs, chore triggers, agent actions, app events, tool changes, webhooks, cleanups, and status transitions. Use it to understand what happened, when, and why.

## What You See

- **Filter chips** — a row of category buttons across the top. Each chip toggles a category on or off:
  - **Pipeline** — pipeline runs and stage transitions
  - **Chore** — chore triggers and chore create/edit/delete events
  - **Agent** — agent activations and executions
  - **App** — app create, start, stop, and delete events
  - **Tool** — tool uploads and removals
  - **Webhook** — incoming webhook events
  - **Cleanup** — repository cleanup operations
  - **Status** — issue status changes on the board
- **Timeline** — a chronological list of events, each showing an icon, summary, and relative timestamp (e.g., "5m ago")
- **Clear all filters** — a button to reset and show all event types

## How to Use It

### Filtering Events

Click any filter chip to toggle that category. Active chips are highlighted. You can enable multiple categories at once, or turn them all off and click "Clear all filters" to see everything.

### Viewing Event Details

Click any event in the timeline to expand it and see the full details — including the event payload, affected resources, and context.

### Scrolling Through History

The timeline loads more events automatically as you scroll down. There is no need to click "Load more" — just keep scrolling to see older activity.

## Tips

- Use filters to focus on what matters. For example, toggle on only "Pipeline" and "Agent" to see how your automation is performing.
- Timestamps are relative (e.g., "2h ago") so you can quickly gauge recency without checking dates.
- If the timeline is empty with filters active, try clicking "Clear all filters" to confirm there is activity to display.
