/**
 * ProfileForm — editable profile fields (display name, bio) with Save/Cancel actions.
 */

import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import type { UserProfile, UserProfileUpdate } from '@/types';

interface ProfileFormProps {
  profile: UserProfile;
  isEditing: boolean;
  isSaving: boolean;
  onEdit: () => void;
  onSave: (data: UserProfileUpdate) => void;
  onCancel: () => void;
}

export function ProfileForm({ profile, isEditing, isSaving, onEdit, onSave, onCancel }: ProfileFormProps) {
  const [displayName, setDisplayName] = useState(profile.display_name ?? '');
  const [bio, setBio] = useState(profile.bio ?? '');
  const [nameError, setNameError] = useState<string | null>(null);

  // Reset form values when profile changes or when entering edit mode
  useEffect(() => {
    if (!isEditing) {
      setDisplayName(profile.display_name ?? '');
      setBio(profile.bio ?? '');
      setNameError(null);
    }
  }, [isEditing, profile.display_name, profile.bio]);

  const validateName = (value: string): boolean => {
    if (!value.trim()) {
      setNameError('Display name cannot be empty');
      return false;
    }
    setNameError(null);
    return true;
  };

  const handleSave = () => {
    if (!validateName(displayName)) return;
    onSave({
      display_name: displayName.trim(),
      bio: bio,
    });
  };

  const handleCancel = () => {
    setDisplayName(profile.display_name ?? '');
    setBio(profile.bio ?? '');
    setNameError(null);
    onCancel();
  };

  if (!isEditing) {
    return (
      <div className="space-y-4">
        <div>
          <p className="text-xs uppercase tracking-wide text-muted-foreground">Display Name</p>
          <p className="text-sm text-foreground">{profile.display_name || profile.github_username}</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-wide text-muted-foreground">Bio</p>
          <p className="text-sm text-foreground">{profile.bio || '—'}</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-wide text-muted-foreground">Email</p>
          <p className="text-sm text-muted-foreground">Managed via GitHub</p>
        </div>
        <div className="pt-2">
          <Button variant="outline" onClick={onEdit}>Edit Profile</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <label htmlFor="profile-display-name" className="text-sm font-medium text-foreground">
          Display Name
        </label>
        <Input
          id="profile-display-name"
          value={displayName}
          onChange={(e) => {
            setDisplayName(e.target.value);
            if (nameError) validateName(e.target.value);
          }}
          onBlur={() => validateName(displayName)}
          placeholder="Enter your display name"
          className="mt-1"
        />
        {nameError && (
          <p className="text-xs text-destructive mt-1">{nameError}</p>
        )}
      </div>
      <div>
        <label htmlFor="profile-bio" className="text-sm font-medium text-foreground">
          Bio
        </label>
        <textarea
          id="profile-bio"
          value={bio}
          onChange={(e) => setBio(e.target.value)}
          placeholder="Tell us about yourself"
          rows={3}
          maxLength={500}
          className="mt-1 flex w-full rounded-md border border-input bg-background/72 px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus:border-primary disabled:cursor-not-allowed disabled:opacity-50 resize-none"
        />
        <p className="text-xs text-muted-foreground mt-1">{bio.length}/500</p>
      </div>
      <div>
        <p className="text-xs uppercase tracking-wide text-muted-foreground">Email</p>
        <p className="text-sm text-muted-foreground">Managed via GitHub</p>
      </div>
      <div className="flex gap-2 pt-2">
        <Button
          onClick={handleSave}
          disabled={isSaving || !!nameError}
        >
          {isSaving ? 'Saving...' : 'Save'}
        </Button>
        <Button variant="outline" onClick={handleCancel} disabled={isSaving}>
          Cancel
        </Button>
      </div>
    </div>
  );
}
