/**
 * ProfilePage — main profile page composing header, form, and metadata.
 */

import { useCallback, useEffect, useState } from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ProfileHeader } from '@/components/profile/ProfileHeader';
import { ProfileForm } from '@/components/profile/ProfileForm';
import { ProfileMetadata } from '@/components/profile/ProfileMetadata';
import { useProfile } from '@/hooks/useProfile';
import { useUnsavedChanges } from '@/hooks/useUnsavedChanges';
import type { UserProfileUpdate } from '@/types';

type FeedbackState = {
  type: 'success' | 'error';
  message: string;
} | null;

export function ProfilePage() {
  const { profile, isLoading, error, refetch, updateProfile, uploadAvatar, isSaving } = useProfile();
  const [isEditing, setIsEditing] = useState(false);
  const [avatarFile, setAvatarFile] = useState<File | null>(null);
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const [avatarError, setAvatarError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<FeedbackState>(null);
  const { blocker, isBlocked } = useUnsavedChanges({ isDirty: isEditing });

  // Cleanup avatar preview URL on unmount
  useEffect(() => {
    return () => {
      if (avatarPreview) {
        URL.revokeObjectURL(avatarPreview);
      }
    };
  }, [avatarPreview]);

  // Auto-dismiss feedback
  useEffect(() => {
    if (!feedback) return;
    const ms = feedback.type === 'success' ? 3000 : 5000;
    const timer = setTimeout(() => setFeedback(null), ms);
    return () => clearTimeout(timer);
  }, [feedback]);

  const handleEdit = useCallback(() => {
    setIsEditing(true);
    setFeedback(null);
  }, []);

  const handleCancel = useCallback(() => {
    setIsEditing(false);
    setAvatarFile(null);
    if (avatarPreview) {
      URL.revokeObjectURL(avatarPreview);
      setAvatarPreview(null);
    }
    setAvatarError(null);
    setFeedback(null);
  }, [avatarPreview]);

  const handleSave = useCallback(async (data: UserProfileUpdate) => {
    try {
      // Upload avatar first if changed
      if (avatarFile) {
        await uploadAvatar(avatarFile);
      }
      await updateProfile(data);
      setIsEditing(false);
      setAvatarFile(null);
      if (avatarPreview) {
        URL.revokeObjectURL(avatarPreview);
        setAvatarPreview(null);
      }
      setAvatarError(null);
      setFeedback({ type: 'success', message: 'Profile updated successfully' });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to update profile. Please try again.';
      setFeedback({ type: 'error', message });
    }
  }, [avatarFile, avatarPreview, updateProfile, uploadAvatar]);

  const handleAvatarSelect = useCallback((file: File) => {
    if (avatarPreview) {
      URL.revokeObjectURL(avatarPreview);
    }
    setAvatarFile(file);
    setAvatarPreview(URL.createObjectURL(file));
    setAvatarError(null);
  }, [avatarPreview]);

  const handleAvatarError = useCallback((message: string) => {
    setAvatarError(message);
  }, []);

  // Loading skeleton
  if (isLoading) {
    return (
      <div className="flex h-full w-full max-w-2xl flex-col overflow-y-auto p-4 sm:p-8 mx-auto">
        <Card className="hover:translate-y-0 hover:shadow-sm">
          <CardHeader>
            <div className="flex flex-col items-center gap-3 sm:flex-row sm:gap-4 animate-pulse">
              <div className="h-20 w-20 sm:h-24 sm:w-24 rounded-full bg-muted" />
              <div className="space-y-2 text-center sm:text-left">
                <div className="h-7 w-40 rounded bg-muted" />
                <div className="h-4 w-24 rounded bg-muted" />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4 animate-pulse">
              <div className="h-4 w-20 rounded bg-muted" />
              <div className="h-10 w-full rounded bg-muted" />
              <div className="h-4 w-16 rounded bg-muted" />
              <div className="h-20 w-full rounded bg-muted" />
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Error state
  if (error || !profile) {
    return (
      <div className="flex h-full w-full max-w-2xl flex-col items-center justify-center gap-4 p-4 sm:p-8 mx-auto">
        <p className="text-muted-foreground">Failed to load profile data.</p>
        <Button variant="outline" onClick={() => refetch()}>
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="flex h-full w-full max-w-2xl flex-col overflow-y-auto p-4 sm:p-8 mx-auto">
      <div className="mb-8">
        <p className="mb-1 text-xs uppercase tracking-[0.24em] text-primary/80">Identity</p>
        <h2 className="mb-2 text-3xl font-display font-medium tracking-[0.04em]">Profile</h2>
        <p className="text-muted-foreground">View and manage your personal information.</p>
      </div>

      {/* Feedback banner */}
      {feedback && (
        <div
          className={`mb-4 rounded-lg px-4 py-3 text-sm ${
            feedback.type === 'success'
              ? 'bg-emerald-100/80 text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-300'
              : 'bg-red-100/80 text-red-800 dark:bg-red-950/50 dark:text-red-300'
          }`}
        >
          {feedback.message}
        </div>
      )}

      {/* Avatar error */}
      {avatarError && (
        <div className="mb-4 rounded-lg px-4 py-3 text-sm bg-red-100/80 text-red-800 dark:bg-red-950/50 dark:text-red-300">
          {avatarError}
        </div>
      )}

      <Card className="hover:translate-y-0 hover:shadow-sm">
        <CardHeader>
          <ProfileHeader
            profile={profile}
            avatarPreview={avatarPreview}
            isEditing={isEditing}
            onAvatarSelect={handleAvatarSelect}
            onAvatarError={handleAvatarError}
          />
        </CardHeader>
        <CardContent>
          <ProfileForm
            profile={profile}
            isEditing={isEditing}
            isSaving={isSaving}
            onEdit={handleEdit}
            onSave={handleSave}
            onCancel={handleCancel}
          />
          <ProfileMetadata profile={profile} />
        </CardContent>
      </Card>

      {isBlocked && (
        <div className="fixed inset-0 z-[70] flex items-center justify-center">
          <div className="absolute inset-0 bg-black/50" role="presentation" />
          <div className="relative z-10 mx-4 w-full max-w-sm rounded-lg border border-border bg-background p-6 text-center shadow-xl">
            <h3 className="mb-2 text-lg font-semibold text-foreground">Unsaved Changes</h3>
            <p className="mb-4 text-sm text-muted-foreground">
              You have unsaved changes — are you sure you want to leave?
            </p>
            <div className="flex justify-center gap-3">
              <Button variant="outline" onClick={() => blocker.reset?.()}>
                Stay
              </Button>
              <Button variant="destructive" onClick={() => blocker.proceed?.()}>
                Discard and Leave
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
