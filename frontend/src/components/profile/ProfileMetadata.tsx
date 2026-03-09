/**
 * ProfileMetadata — displays read-only account metadata (creation date, role).
 */

import type { UserProfile } from '@/types';

interface ProfileMetadataProps {
  profile: UserProfile;
}

function formatMemberSince(dateStr: string | null): string {
  if (!dateStr) return '—';
  try {
    const date = new Date(dateStr);
    return `Member since ${date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}`;
  } catch {
    return '—';
  }
}

export function ProfileMetadata({ profile }: ProfileMetadataProps) {
  return (
    <div className="border-t border-border/60 pt-4 mt-4">
      <div className="flex flex-wrap gap-x-8 gap-y-3">
        <div>
          <p className="text-xs uppercase tracking-wide text-muted-foreground">Account</p>
          <p className="text-sm text-foreground">
            {formatMemberSince(profile.account_created_at)}
          </p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-wide text-muted-foreground">Role</p>
          <span className="inline-flex px-2 py-0.5 rounded-full text-xs bg-primary/10 text-primary">
            {profile.role ?? 'member'}
          </span>
        </div>
      </div>
    </div>
  );
}
