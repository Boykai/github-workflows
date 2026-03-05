# Quickstart & Verification: Cowboy Saloon UI

Since the modifications are purely frontend CSS and React UI component changes, validation can be performed immediately by running the Vite dev server.

## Verification Steps
1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Start the Vite React development server:
   ```bash
   npm run dev 
   ```
   *(or `yarn dev` / `pnpm dev` based on package manager in use).*
3. Open the localhost URL in your browser.
4. **Validating Theme**: The application background, foreground elements, borders, and general components will reflect rustic "Saloon" warm colors.
5. **Validating Dark Mode**: Find the Theme toggle in the UI (usually top right), and switch into Dark Mode. UI must reflect a high-contrast dark-mode equivalent of the Saloon aesthetics.
6. **Validating Agents**: Initiate an agent thread, or view agents. Distinct custom cowboy avatars must render next to agent names per their particular `slug`.
