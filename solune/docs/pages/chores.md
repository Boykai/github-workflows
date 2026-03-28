# Chores

The Chores page lets you set up recurring automated tasks (called "rituals") for your repository. Chores can trigger on a schedule or when certain thresholds are reached, helping you keep your project healthy without manual effort.

## What You See

- **Featured Rituals** — a highlighted section at the top showing your most important chores
- **Chores list** — the full catalog of all configured chores, each showing its name, description, trigger conditions, and current status
- **Cleanup controls** — tools for running repository cleanup operations

## How to Use It

### Viewing Your Chores

The chores list shows every recurring task configured for your project. Each entry displays:

- **Name and description** — what the chore does
- **Trigger configuration** — when it runs (time-based interval or count-based threshold)
- **Status** — whether the chore is active, pending, or has recently fired

The first time you visit this page for a project, Solune creates a set of default chores to get you started.

### Adding a Chore

1. Use the add form at the top of the chores panel
2. Give the chore a name and description
3. Configure the trigger — either a time interval (e.g., "every 7 days") or a count threshold (e.g., "when there are more than 20 open issues")
4. Save the chore

### Editing and Deleting Chores

Click the edit or delete action on any chore in the list. If you have unsaved changes and try to navigate away, Solune will warn you so you do not lose your edits.

### Understanding Triggers

Chores support two types of triggers:

| Trigger Type | How It Works |
|--------------|--------------|
| **Time-based** | Fires at regular intervals (e.g., daily, weekly) |
| **Count-based** | Fires when a metric crosses a threshold (e.g., number of open parent issues exceeds a limit) |

While you are on this page, Solune automatically checks whether any count-based chores have reached their threshold and updates their status in real time.

### Running Cleanup

Use the cleanup controls to trigger a one-time repository cleanup. This can remove stale branches, close old issues, or perform other housekeeping tasks.

## Tips

- The Featured Rituals section highlights your most important chores — check it first for a quick overview.
- Count-based thresholds are evaluated while the page is open. If you want to see whether a chore is about to fire, just stay on the page and watch the status update.
- Preset chores are created automatically the first time you visit — these are good starting points that you can customize to your workflow.
