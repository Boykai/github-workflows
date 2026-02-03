/**
 * Dark Theme Implementation
 * Handles theme toggling, system preference detection, and user preference persistence
 */

// Theme constants
const THEME_KEY = 'theme-preference';
const THEMES = {
    LIGHT: 'light',
    DARK: 'dark',
    AUTO: 'auto'
};

// Get system preference
function getSystemTheme() {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        return THEMES.DARK;
    }
    return THEMES.LIGHT;
}

// Get stored theme preference or default to auto
function getStoredTheme() {
    const stored = localStorage.getItem(THEME_KEY);
    return stored || THEMES.AUTO;
}

// Determine the actual theme to apply
function getEffectiveTheme(preference) {
    if (preference === THEMES.AUTO) {
        return getSystemTheme();
    }
    return preference;
}

// Apply theme to document
function applyTheme(theme) {
    const effectiveTheme = getEffectiveTheme(theme);
    document.documentElement.setAttribute('data-theme', effectiveTheme);
    updateThemeDisplay(theme, effectiveTheme);
}

// Update theme display information
function updateThemeDisplay(preference, effectiveTheme) {
    const currentThemeElement = document.getElementById('current-theme');
    if (currentThemeElement) {
        let displayText = preference;
        if (preference === THEMES.AUTO) {
            displayText = `Auto (${effectiveTheme})`;
        }
        currentThemeElement.textContent = displayText;
    }
}

// Save theme preference
function saveTheme(theme) {
    localStorage.setItem(THEME_KEY, theme);
    applyTheme(theme);
}

// Initialize theme on page load
function initializeTheme() {
    const storedTheme = getStoredTheme();
    applyTheme(storedTheme);
    
    // Set the radio button state
    const radioButtons = document.querySelectorAll('input[name="theme"]');
    radioButtons.forEach(radio => {
        if (radio.value === storedTheme) {
            radio.checked = true;
        }
    });
}

// Set up event listeners
function setupEventListeners() {
    // Theme toggle button
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const currentPreference = getStoredTheme();
            const currentEffective = getEffectiveTheme(currentPreference);
            
            // Toggle between light and dark
            const newTheme = currentEffective === THEMES.DARK ? THEMES.LIGHT : THEMES.DARK;
            saveTheme(newTheme);
            
            // Update radio buttons
            const radioButtons = document.querySelectorAll('input[name="theme"]');
            radioButtons.forEach(radio => {
                radio.checked = radio.value === newTheme;
            });
        });
    }

    // Radio button controls
    const radioButtons = document.querySelectorAll('input[name="theme"]');
    radioButtons.forEach(radio => {
        radio.addEventListener('change', (e) => {
            if (e.target.checked) {
                saveTheme(e.target.value);
            }
        });
    });

    // Listen for system theme changes
    if (window.matchMedia) {
        const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
        
        // Modern browsers
        if (darkModeQuery.addEventListener) {
            darkModeQuery.addEventListener('change', (e) => {
                const currentPreference = getStoredTheme();
                if (currentPreference === THEMES.AUTO) {
                    applyTheme(THEMES.AUTO);
                }
            });
        } 
        // Fallback for older browsers
        else if (darkModeQuery.addListener) {
            darkModeQuery.addListener((e) => {
                const currentPreference = getStoredTheme();
                if (currentPreference === THEMES.AUTO) {
                    applyTheme(THEMES.AUTO);
                }
            });
        }
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        initializeTheme();
        setupEventListeners();
    });
} else {
    initializeTheme();
    setupEventListeners();
}

// Export functions for testing purposes (if needed)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        getSystemTheme,
        getStoredTheme,
        getEffectiveTheme,
        applyTheme,
        saveTheme,
        THEMES
    };
}
