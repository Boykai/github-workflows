# Data Model: Cowboy Saloon UI

No backend database schema or data model modifications are required for this purely visual UI update feature.

## UI-Layer Mappings (Frontend Only)
While no persistence models change, the client-side representation mappings will be handled conceptually via code constants arrays:

| Entity / ID Key     | UI Avatar Path/Component (Conceptual) | Description                             |
|---------------------|---------------------------------------|-----------------------------------------|
| `code-reviewer`     | `<SheriffCowboyLogo />`              | Western sheriff hat logo for reviewers. |
| `scripter`          | `<BanditCowboyLogo />`               | Bandit/Rogue logo for coders.           |
| `(default/unknown)` | `<GenericHorseLogo />`               | Fallback logo for unlisted agents.      |
