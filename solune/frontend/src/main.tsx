/**
 * Application entry point.
 */

import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './index.css';
import { ThemeProvider } from './components/ThemeProvider';

/* ── Global error telemetry ── */
window.onerror = (message, source, lineno, colno, error) => {
  console.error('[global:onerror]', { message, source, lineno, colno, error });
};

window.addEventListener('unhandledrejection', (event: PromiseRejectionEvent) => {
  console.error('[global:unhandledrejection]', event.reason);
});

const root = document.getElementById('root');
if (root) {
  createRoot(root).render(
    <StrictMode>
      <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
        <App />
      </ThemeProvider>
    </StrictMode>
  );
}
