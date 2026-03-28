# Pipeline

The Pipeline page is where you build automation workflows. Each pipeline defines a series of stages that map to your board columns, with an AI agent and model assigned to each stage. When issues move through the board, the assigned agents process them automatically.

## What You See

- **Stats bar** — shows the number of saved pipelines, active stages, the currently assigned pipeline, and your project name
- **Pipeline board** — a visual editor where each board column has a corresponding stage. You assign an agent and an AI model to each stage
- **Toolbar** — buttons to Save, Save as Copy, Delete, and Discard changes
- **Saved workflows list** — a panel listing all your saved pipelines. Click one to load it into the editor
- **Analytics** — usage statistics and performance metrics for your pipelines
- **Run history** — a log of past pipeline executions with status and timing
- **Stages overview** — a summary view of all stages and their configurations

## How to Use It

### Creating a Pipeline

1. Select a project from the sidebar (if not already selected)
2. The pipeline editor loads with stages matching your board columns
3. For each stage, choose an **agent** from the dropdown (the AI agent that will handle issues in that column)
4. For each stage, choose a **model** (the LLM that the agent will use)
5. Click **Save** in the toolbar to store your pipeline

The first time you visit this page for a project, Solune automatically creates starter pipeline templates to help you get going.

### Editing a Pipeline

1. Click a pipeline name in the Saved Workflows list to load it
2. Make changes to agent or model assignments
3. Click **Save** to update, or **Save as Copy** to keep the original and create a new version

### Deleting a Pipeline

Click **Delete** in the toolbar. You will be asked to confirm before the pipeline is removed.

### Assigning a Pipeline to the Board

After saving a pipeline, assign it to your project board from the [Projects](projects.md) page. Once assigned, agents will automatically process issues as they move through columns.

### Discarding Changes

If you have unsaved edits and want to start over, click **Discard**. Solune also warns you if you try to navigate away with unsaved changes — you can choose to save, discard, or stay on the page.

## Validation

The editor checks your pipeline before saving. If a stage is missing an agent or has a configuration issue, an error message appears inline on the affected stage card. Fix the issues before saving.

## Tips

- Use **Save as Copy** to experiment with different agent/model combinations without losing your current setup.
- Check the **Run History** section to see how your pipelines have performed and identify stages that could use a different agent or model.
- The **Analytics** section helps you understand which pipelines are used most and how they perform over time.
