# Quickstart: Modern UI Refresh

## Setup Instructions

1. **Install Dependencies**:
   Navigate to the `frontend` directory and install the required packages for Tailwind CSS and Shadcn UI.
   ```bash
   cd frontend
   npm install -D tailwindcss postcss autoprefixer
   npx tailwindcss init -p
   npm install class-variance-authority clsx tailwind-merge lucide-react
   ```

2. **Configure Tailwind**:
   Update `tailwind.config.js` to include the paths to all template files and define the custom color palette using CSS variables.

3. **Setup Global Styles**:
   Update `src/index.css` to include Tailwind directives and define the root CSS variables for the light and dark themes.

4. **Initialize Shadcn UI (Optional/Manual)**:
   You can use the Shadcn CLI to add components, or manually copy the required primitives (like Button, Input, Card) into `src/components/ui/`.
   ```bash
   npx shadcn-ui@latest init
   npx shadcn-ui@latest add button card input
   ```

## Development Guidelines

- **Component Usage**: Always prefer using the new components from `src/components/ui/` over standard HTML elements or old custom components.
- **Styling**: Use Tailwind utility classes for layout and spacing. Avoid writing custom CSS unless absolutely necessary.
- **Theming**: Use the semantic color variables (e.g., `bg-background`, `text-foreground`, `bg-primary`) instead of hardcoded colors to ensure dark mode compatibility.
