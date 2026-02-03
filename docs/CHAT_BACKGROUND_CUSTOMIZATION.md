# Chat Background Customization Feature

## Overview

This feature enables users to personalize their chat experience by customizing the chat background. Users can choose from preset background options, upload custom images, or reset to the default background.

## Features Implemented

### 1. **Background Settings Modal**
- Accessible via a settings button (⚙️) in the chat interface header
- Clean, modal-based UI for selecting backgrounds
- Click outside modal or use close/done buttons to dismiss

### 2. **Preset Backgrounds** (5 Options)
The system provides five beautiful gradient backgrounds:
- **Ocean Blue**: Linear gradient from blue to purple
- **Sunset**: Linear gradient from pink to red
- **Forest**: Linear gradient from light blue to cyan
- **Purple Dream**: Linear gradient from teal to pink
- **Dark Mode**: Linear gradient from dark gray tones

### 3. **Custom Image Upload**
- Supports JPEG and PNG formats only
- Maximum file size: 2MB
- Real-time preview of uploaded image
- Validation with user-friendly error messages

### 4. **Persistence**
- Background settings persist across browser sessions using localStorage
- Settings survive page reloads and browser restarts
- Automatic restoration of user's preferred background on app load

### 5. **Reset to Default**
- One-click reset button to restore the original white background
- Clears any custom preferences and returns to default state

### 6. **Accessibility**
- Semi-transparent white overlay ensures text readability on all backgrounds
- ARIA labels on interactive elements
- Keyboard navigation support
- Sufficient color contrast maintained

## Technical Implementation

### File Structure

```
frontend/src/
├── components/chat/
│   ├── BackgroundSettings.tsx       # Settings modal component
│   ├── BackgroundSettings.css       # Modal styling
│   ├── ChatInterface.tsx            # Updated with background support
│   └── ChatInterface.css            # Updated with header and overlay
├── hooks/
│   ├── useBackgroundSettings.ts     # Background state management hook
│   └── useBackgroundSettings.test.tsx  # Unit tests
└── e2e/
    └── background-settings.spec.ts  # End-to-end tests
```

### Key Components

#### `useBackgroundSettings` Hook
Manages background state with localStorage persistence:
```typescript
const {
  background,           // Current background settings
  setPresetBackground,  // Set a preset background
  setCustomBackground,  // Upload custom image
  resetToDefault,       // Reset to default
} = useBackgroundSettings();
```

#### `BackgroundSettings` Component
Modal UI for background selection:
- Grid of preset options with visual previews
- File upload for custom images with validation
- Reset and Done buttons

#### `ChatInterface` Updates
- Settings button in header
- Background applied to `.chat-messages` container
- Semi-transparent overlay for readability

### Data Structure

Background settings stored in localStorage as:
```json
{
  "type": "preset" | "custom" | "default",
  "value": "CSS value or data URL"
}
```

## Usage

1. **Open Settings**: Click the ⚙️ settings button in the chat header
2. **Select Preset**: Click any preset background tile
3. **Upload Custom**: Click "Upload Image" and select a JPEG/PNG file (max 2MB)
4. **Reset**: Click "Reset to Default" to restore original background
5. **Close**: Click "Done" or outside the modal to save and close

## Validation Rules

### File Type Validation
- ✅ JPEG (image/jpeg)
- ✅ PNG (image/png)
- ❌ GIF, SVG, WebP, or other formats

### File Size Validation
- ✅ Up to 2MB (2,097,152 bytes)
- ❌ Files larger than 2MB show error message

### Error Messages
- "Only JPEG and PNG images are allowed." - Invalid file type
- "Image must be less than 2MB." - File too large
- "Failed to read image file." - File reading error

## Testing

### Unit Tests
Run unit tests for the background settings hook:
```bash
npm test -- useBackgroundSettings.test.tsx
```

Tests cover:
- Default initialization
- localStorage persistence
- Preset background selection
- Custom image handling
- Reset functionality
- Invalid data handling

### E2E Tests
Run end-to-end tests:
```bash
npm run test:e2e -- background-settings.spec.ts
```

Tests cover:
- Settings button visibility
- Modal interactions
- Preset selection
- Custom upload validation
- Persistence across sessions
- Accessibility features

### Manual Testing Checklist

- [ ] Settings button appears in chat interface header
- [ ] Modal opens when clicking settings button
- [ ] All 5 preset backgrounds are visible
- [ ] Clicking a preset immediately updates the background
- [ ] Upload button accepts JPEG and PNG files
- [ ] Upload validates file size (max 2MB)
- [ ] Custom image shows preview after upload
- [ ] Error messages display for invalid files
- [ ] Reset button restores default background
- [ ] Background persists after page reload
- [ ] Background persists after closing browser
- [ ] Modal closes when clicking outside
- [ ] Modal closes when clicking Done button
- [ ] Text remains readable on all backgrounds

## Browser Compatibility

- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

## Performance Considerations

- Custom images stored as data URLs in localStorage
- 2MB size limit prevents excessive storage usage
- Lazy loading of background images
- CSS-based gradients for optimal performance

## Future Enhancements

Potential improvements for future iterations:
- Color picker for solid color backgrounds
- Gradient customizer
- Image effects (blur, brightness, contrast)
- Background image gallery from external sources
- Sync settings across devices via backend API
- Pattern library (dots, stripes, geometric)
- Seasonal/themed backgrounds

## Security Notes

- File type validation prevents execution of malicious scripts
- Size limit prevents DoS via localStorage exhaustion
- Data URLs are sandboxed by browser security model
- No external URLs loaded (XSS protection)

## Troubleshooting

### Background not persisting
- Check browser localStorage is enabled
- Verify no browser extensions are blocking localStorage
- Check browser console for errors

### Upload not working
- Verify file is JPEG or PNG
- Check file size is under 2MB
- Try a different image file

### Text hard to read
- The overlay layer should ensure readability
- Try a different preset background
- Reset to default for best contrast

## Requirements Checklist

✅ System provides at least five preset background options  
✅ System updates chat background immediately upon selection  
✅ System allows custom background image upload (JPEG/PNG, max 2MB)  
✅ System persists selected background across sessions  
✅ System includes 'Reset to Default' button  
✅ UI includes 'Change Background' option in chat interface  
✅ Settings displayed in modal/panel with background choices  
✅ Includes preview functionality  
✅ Ensures accessibility with sufficient color contrast  
✅ Clear visual feedback for selection
