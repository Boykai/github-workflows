# Data Model: Modern UI Refresh

*Note: This feature is primarily a UI/frontend refresh and does not introduce new backend data models or database schema changes.*

## Frontend State Models

### Theme State
- **Entity**: `Theme`
- **Fields**:
  - `mode`: `'light' | 'dark' | 'system'`
- **Description**: Manages the current visual theme of the application. Stored in local storage and React Context.

### UI Component Variants
- **Entity**: `ComponentVariant`
- **Description**: Standardized variants for core UI components to ensure consistency across the application, managed via `class-variance-authority` (cva).
- **Examples**:
  - `Button`: `default`, `destructive`, `outline`, `secondary`, `ghost`, `link`
  - `Badge`: `default`, `secondary`, `destructive`, `outline`
