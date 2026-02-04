# Weather Widget - Visual Mockup

## Header Layout
```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  GitHub Projects Chat          [Weather Widget]         [Login Button]      │
│  ─────────────────            ─────────────────────     ─────────────        │
│  (App Title)                  │ ⛅ 19°C             │    Login with GitHub   │
│                               │ partly cloudy      │    or                  │
│                               │ 📍 San Francisco   │    [User Avatar]       │
│                               │ 🔄 Updated: 11:07  │                        │
│                               └────────────────────┘                         │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Widget States

### 1. Normal State (with data)
```
┌─────────────────────────────┐
│  ⛅  19°C                    │
│      partly cloudy          │
│                             │
│  📍 San Francisco, US       │
│                         🔄  │
│                             │
│  Updated: 11:07:32 PM       │
└─────────────────────────────┘
```

### 2. Loading State
```
┌─────────────────────────────┐
│         ◌                   │
│    Loading weather...       │
│                             │
└─────────────────────────────┘
```
*(◌ represents spinning animation)*

### 3. Error State
```
┌─────────────────────────────┐
│  ⚠️  Unable to fetch        │
│      weather data           │
│                         🔄  │
└─────────────────────────────┘
```

### 4. Mock Data Notice (when no API key)
```
┌─────────────────────────────┐
│  ⛅  19°C                    │
│      partly cloudy          │
│                             │
│  📍 San Francisco, US       │
│                         🔄  │
│                             │
│  ┌───────────────────────┐  │
│  │ ⚠️ Demo data - Config │  │
│  │   OPENWEATHER_API_KEY │  │
│  └───────────────────────┘  │
│                             │
│  Updated: 11:07:32 PM       │
└─────────────────────────────┘
```

## Color Scheme

### Normal State
- Background: `#f6f8fa` (light gray)
- Border: `#d0d7de` (medium gray)
- Text: `#24292f` (dark gray)
- Temperature: Large, bold
- Description: Smaller, secondary color
- Icons: Emoji (native colors)

### Error State
- Background: `#fff1f0` (light red)
- Border: `#cf222e` (red)
- Text: `#cf222e` (red)
- Icon: ⚠️ warning emoji

### Mock Notice
- Background: `#fff8c5` (light yellow)
- Border: `#9a6700` (amber)
- Text: `#9a6700` (amber)
- Font size: Small (11px)

### Hover/Interactive
- Widget hover: Adds subtle shadow
- Refresh button hover: Background color change
- Loading button: Disabled state with reduced opacity

## Responsive Behavior

### Desktop (>768px)
```
[Title]  [⛅ 19°C partly cloudy 📍 SF, US 🔄]  [Login]
```
- Full widget display
- All information visible
- Comfortable spacing

### Mobile (<768px)
```
[Title]         [⛅ 19°C 🔄]         [Login]
```
- Compact display
- Location hidden
- Icon and temperature only
- Refresh button remains

## Accessibility Features

### ARIA Labels
- `role="region"` on widget container
- `aria-label="Current weather information"`
- `aria-live="polite"` for dynamic updates
- `role="alert"` on error messages
- `role="status"` on update timestamp

### Keyboard Navigation
1. Tab to refresh button
2. Enter/Space to trigger refresh
3. Visual focus indicator (outline)

### Screen Reader Announcements
- Loading: "Loading weather..."
- Success: "Weather data updated"
- Error: "Unable to fetch weather data"
- Mock: "Demo data displayed"

## Animation Details

### Refresh Button
- Normal: Static 🔄
- Loading: Rotating 360° continuously
- Duration: 0.8s linear infinite
- Respects `prefers-reduced-motion`

### Widget Hover
- Adds box-shadow on hover
- Smooth transition (0.2s ease)
- Subtle elevation effect

## Typography

### Temperature
- Size: 20px
- Weight: 600 (semi-bold)
- Color: Primary text color

### Description
- Size: 12px
- Weight: 400 (normal)
- Color: Secondary text color
- Text-transform: capitalize

### Location
- Size: 12px
- Weight: 400 (normal)
- Color: Secondary text color
- Overflow: ellipsis

### Timestamp
- Size: 11px
- Weight: 400 (normal)
- Color: Secondary text color
- Align: right

## Integration Points

### App.tsx
```tsx
<header className="app-header">
  <h1>GitHub Projects Chat</h1>
  <WeatherWidget />        ← Inserted here
  <LoginButton />
</header>
```

### App.css
```css
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;                ← Added for spacing
  padding: 12px 24px;
}
```

## Example Weather Icons by Condition

| Condition    | Day Icon | Night Icon | Code |
|--------------|----------|------------|------|
| Clear        | ☀️       | 🌙         | 01   |
| Few Clouds   | ⛅       | ☁️         | 02   |
| Clouds       | ☁️       | ☁️         | 03   |
| Rain         | 🌧️       | 🌧️         | 09   |
| Rain (day)   | 🌦️       | 🌧️         | 10   |
| Thunderstorm | ⛈️       | ⛈️         | 11   |
| Snow         | ❄️       | ❄️         | 13   |
| Mist         | 🌫️       | 🌫️         | 50   |

## User Interactions

1. **Initial Load**
   - Widget appears in loading state
   - Fetches weather data
   - Displays result or error
   - Announces to screen readers

2. **Manual Refresh**
   - Click refresh button
   - Button shows spinning animation
   - Fetches updated data
   - Updates display
   - Announces update to screen readers

3. **Error Recovery**
   - Error state displays
   - Retry button available
   - Click to re-fetch
   - Success or new error shown

4. **Keyboard Navigation**
   - Tab to reach refresh button
   - Enter/Space to activate
   - Visible focus indicator
   - All actions accessible

---
*This mockup represents the visual design and behavior of the weather widget as implemented in the code.*
