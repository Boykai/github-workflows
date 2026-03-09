/**
 * ProfileHeader — displays user avatar with upload capability, display name, and username.
 */

import { useRef } from 'react';
import { Camera } from 'lucide-react';
import type { UserProfile } from '@/types';
import { ACCEPTED_AVATAR_TYPES, MAX_AVATAR_SIZE } from '@/types';

interface ProfileHeaderProps {
  profile: UserProfile;
  avatarFile: File | null;
  avatarPreview: string | null;
  isEditing: boolean;
  onAvatarSelect: (file: File) => void;
  onAvatarError: (message: string) => void;
}

function getInitials(name: string | null, username: string): string {
  const source = name || username;
  return source
    .split(/[\s_-]+/)
    .map((part) => part.charAt(0).toUpperCase())
    .slice(0, 2)
    .join('');
}

export function ProfileHeader({
  profile,
  avatarPreview,
  isEditing,
  onAvatarSelect,
  onAvatarError,
}: ProfileHeaderProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const avatarSrc = avatarPreview || profile.avatar_url;
  const displayName = profile.display_name || profile.github_username;
  const initials = getInitials(profile.display_name, profile.github_username);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate type
    if (!ACCEPTED_AVATAR_TYPES.includes(file.type)) {
      onAvatarError('Please select a PNG, JPG, or WebP image');
      e.target.value = '';
      return;
    }

    // Validate size
    if (file.size > MAX_AVATAR_SIZE) {
      onAvatarError('Image must be smaller than 5 MB');
      e.target.value = '';
      return;
    }

    onAvatarSelect(file);
    e.target.value = '';
  };

  const handleAvatarClick = () => {
    if (isEditing && fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  return (
    <div className="flex flex-col items-center gap-3 sm:flex-row sm:gap-4">
      {/* Avatar */}
      <div className="relative shrink-0">
        <button
          type="button"
          onClick={handleAvatarClick}
          disabled={!isEditing}
          className="relative h-20 w-20 sm:h-24 sm:w-24 rounded-full border-2 border-primary/30 shadow-sm overflow-hidden focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-default"
        >
          {avatarSrc ? (
            <img
              src={avatarSrc}
              alt={displayName}
              className="h-full w-full object-cover"
            />
          ) : (
            <div className="flex h-full w-full items-center justify-center bg-primary/10 text-primary text-lg font-semibold">
              {initials}
            </div>
          )}
          {isEditing && (
            <div className="absolute inset-0 flex items-center justify-center rounded-full bg-black/40 opacity-0 transition-opacity hover:opacity-100">
              <Camera className="h-5 w-5 text-white" />
            </div>
          )}
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/png,image/jpeg,image/webp"
          className="hidden"
          onChange={handleFileChange}
        />
      </div>

      {/* Name & Username */}
      <div className="text-center sm:text-left">
        <h1 className="text-2xl font-semibold text-foreground">{displayName}</h1>
        <p className="text-sm text-muted-foreground">@{profile.github_username}</p>
      </div>
    </div>
  );
}
