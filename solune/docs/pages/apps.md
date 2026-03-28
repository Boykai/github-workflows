# Apps

The Apps page lets you create, manage, and monitor Solune applications. You can browse all your apps in a grid, create new ones from scratch or from existing repositories, and control their lifecycle (start, stop, delete).

## What You See

### List View

- **App grid** — cards for each of your apps showing name, status, and quick-action buttons
- **Create button** — opens a dialog to create a new app
- **Status badges** — each card shows whether the app is running, stopped, or in another state

### Detail View

When you click an app card, you are taken to a detail view with:

- **Configuration** — the app's settings and setup
- **Logs** — recent output and activity for the app
- **Status** — current health and state information

## How to Use It

### Creating an App

1. Click the **Create** button
2. Choose whether to create a new repository or use an existing one
3. Fill in the required fields (name, owner)
4. Submit to create the app

### Starting and Stopping Apps

Each app card has **Start** and **Stop** buttons. Click Start to launch the app, or Stop to shut it down. The status badge updates to reflect the change.

### Deleting an App

1. Click the **Delete** button on an app card
2. Solune shows you an **asset inventory** — a summary of all branches, issues, and pull requests associated with the app
3. Review the inventory and confirm deletion

This safety step ensures you know exactly what will be affected before anything is removed.

### Viewing App Details

Click an app card to open its detail page. The breadcrumb at the top updates to show the app name, and you can navigate back to the list by clicking "Apps" in the breadcrumb.

## Tips

- Scroll down to load more apps — the list loads incrementally as you scroll.
- If you see a rate limit warning when creating or managing apps, wait a few minutes for your GitHub API quota to reset.
- The asset inventory during deletion is a safety net — always review it before confirming.
