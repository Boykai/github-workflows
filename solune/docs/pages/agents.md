# Agents

The Agents page is a catalog of all available AI agents and a map showing which agents are assigned to which board columns. Use this page to explore what each agent does and see the current automation setup for your project.

## What You See

- **Stats bar** — total agent count, number of assigned agents, and pipeline configuration count
- **Agent catalog** (left side) — a searchable grid of agent cards, each showing:
  - Agent icon and name
  - Description of what the agent does
  - Usage count (how many times it has been activated)
  - Pipeline count (how many pipelines reference it)
  - Pending sub-issues (work the agent has queued)
- **Column assignment map** (right side) — your board columns listed with the agents currently assigned to each, color-coded by status

## How to Use It

### Browsing Agents

Scroll through the agent catalog to see all available agents. Use the search bar to filter by name or description. Each card gives you a quick summary of the agent's purpose and activity.

### Understanding the Assignment Map

The right panel shows your board columns (e.g., Backlog, In Progress, Review, Done). Under each column, you can see which agents are assigned to handle issues in that stage.

This view is read-only — to change agent assignments, go to the [Pipeline](pipeline.md) page where you can build and edit workflows.

### Checking Agent Activity

The usage count and pending sub-issue count on each card help you understand how active each agent is. A high usage count means the agent has been heavily involved in processing issues.

## Tips

- Think of this page as a reference catalog. When deciding which agents to use in your pipelines, come here to compare what each one does.
- On smaller screens, the catalog and assignment map stack vertically instead of side-by-side.
