/**
 * LoginPage — Solune-branded login page for unauthenticated users.
 * Renders outside AppLayout (no sidebar/topbar).
 */

import { LoginButton } from '@/components/auth/LoginButton';

export function LoginPage() {
  return (
    <div className="flex flex-col items-center justify-center h-screen gap-6 bg-gradient-to-br from-primary/5 via-background to-accent/5">
      <div className="flex flex-col items-center gap-6 p-10 rounded-xl border border-border bg-card shadow-lg max-w-sm w-full mx-4">
        <div className="text-center">
          <h1 className="text-3xl font-display font-bold tracking-tight text-primary mb-2">
            Solune
          </h1>
          <p className="text-muted-foreground text-sm">
            Manage your GitHub Projects with AI-powered workflows
          </p>
        </div>
        <LoginButton />
      </div>
    </div>
  );
}
