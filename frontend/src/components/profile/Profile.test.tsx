/**
 * Unit tests for Profile component
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Profile } from './Profile';
import * as api from '@/services/api';
import type { ReactNode } from 'react';

// Mock the API module
vi.mock('@/services/api', () => ({
  authApi: {
    updateProfile: vi.fn(),
  },
}));

// Mock useAuth hook
const mockUser = {
  github_user_id: '12345',
  github_username: 'testuser',
  github_avatar_url: 'https://example.com/avatar.jpg',
  email: 'test@example.com',
  bio: 'Test bio',
  contact_phone: '+1-555-0123',
  contact_location: 'San Francisco, CA',
};

const mockRefetch = vi.fn();

vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    user: mockUser,
    refetch: mockRefetch,
  }),
}));

const mockAuthApi = api.authApi as unknown as {
  updateProfile: ReturnType<typeof vi.fn>;
};

// Create wrapper with QueryClientProvider
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );
  };
}

describe('Profile Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders profile information in view mode', () => {
    const wrapper = createWrapper();
    render(<Profile />, { wrapper });

    // Check if user information is displayed
    expect(screen.getByText('testuser')).toBeTruthy();
    expect(screen.getByText('test@example.com')).toBeTruthy();
    expect(screen.getByText('Test bio')).toBeTruthy();
    expect(screen.getByText('+1-555-0123')).toBeTruthy();
    expect(screen.getByText('San Francisco, CA')).toBeTruthy();
    
    // Check for Edit Profile button
    expect(screen.getByText('Edit Profile')).toBeTruthy();
  });

  it('switches to edit mode when Edit Profile button is clicked', () => {
    const wrapper = createWrapper();
    render(<Profile />, { wrapper });

    const editButton = screen.getByText('Edit Profile');
    fireEvent.click(editButton);

    // Check if form inputs appear
    expect(screen.getByPlaceholderText('Enter your email')).toBeTruthy();
    expect(screen.getByPlaceholderText('Tell us about yourself')).toBeTruthy();
    expect(screen.getByPlaceholderText('Enter your phone number')).toBeTruthy();
    expect(screen.getByPlaceholderText('Enter your location')).toBeTruthy();
    
    // Check for Save and Cancel buttons
    expect(screen.getByText('Save Changes')).toBeTruthy();
    expect(screen.getByText('Cancel')).toBeTruthy();
  });

  it('validates email format', async () => {
    const wrapper = createWrapper();
    render(<Profile />, { wrapper });

    // Enter edit mode
    fireEvent.click(screen.getByText('Edit Profile'));

    // Enter invalid email
    const emailInput = screen.getByPlaceholderText('Enter your email') as HTMLInputElement;
    fireEvent.change(emailInput, { target: { value: 'invalid-email' } });

    // Try to save
    fireEvent.click(screen.getByText('Save Changes'));

    // Check for error message
    await waitFor(() => {
      expect(screen.getByText('Please enter a valid email address')).toBeTruthy();
    });

    // API should not be called
    expect(mockAuthApi.updateProfile).not.toHaveBeenCalled();
  });

  it('validates bio length', async () => {
    const wrapper = createWrapper();
    render(<Profile />, { wrapper });

    // Enter edit mode
    fireEvent.click(screen.getByText('Edit Profile'));

    // Enter bio that's too long
    const bioInput = screen.getByPlaceholderText('Tell us about yourself') as HTMLTextAreaElement;
    const longBio = 'a'.repeat(501);
    fireEvent.change(bioInput, { target: { value: longBio } });

    // Try to save
    fireEvent.click(screen.getByText('Save Changes'));

    // Check for error message
    await waitFor(() => {
      expect(screen.getByText('Bio must be 500 characters or less')).toBeTruthy();
    });

    // API should not be called
    expect(mockAuthApi.updateProfile).not.toHaveBeenCalled();
  });

  it('cancels edit mode without saving', () => {
    const wrapper = createWrapper();
    render(<Profile />, { wrapper });

    // Enter edit mode
    fireEvent.click(screen.getByText('Edit Profile'));

    // Change email
    const emailInput = screen.getByPlaceholderText('Enter your email') as HTMLInputElement;
    fireEvent.change(emailInput, { target: { value: 'newemail@example.com' } });

    // Cancel
    fireEvent.click(screen.getByText('Cancel'));

    // Should return to view mode
    expect(screen.getByText('Edit Profile')).toBeTruthy();
    // Original email should still be displayed
    expect(screen.getByText('test@example.com')).toBeTruthy();
    
    // API should not be called
    expect(mockAuthApi.updateProfile).not.toHaveBeenCalled();
  });

  it('successfully updates profile', async () => {
    const wrapper = createWrapper();
    mockAuthApi.updateProfile.mockResolvedValueOnce(mockUser);
    
    render(<Profile />, { wrapper });

    // Enter edit mode
    fireEvent.click(screen.getByText('Edit Profile'));

    // Update email
    const emailInput = screen.getByPlaceholderText('Enter your email') as HTMLInputElement;
    fireEvent.change(emailInput, { target: { value: 'newemail@example.com' } });

    // Save changes
    fireEvent.click(screen.getByText('Save Changes'));

    // Wait for API call
    await waitFor(() => {
      expect(mockAuthApi.updateProfile).toHaveBeenCalledWith({
        email: 'newemail@example.com',
        bio: 'Test bio',
        contact_phone: '+1-555-0123',
        contact_location: 'San Francisco, CA',
      });
    });

    // Refetch should be called
    await waitFor(() => {
      expect(mockRefetch).toHaveBeenCalled();
    });

    // Success message should appear
    await waitFor(() => {
      expect(screen.getByText(/Profile updated successfully/)).toBeTruthy();
    });
  });

  it('displays character count for bio', () => {
    const wrapper = createWrapper();
    render(<Profile />, { wrapper });

    // Enter edit mode
    fireEvent.click(screen.getByText('Edit Profile'));

    // Check initial character count
    expect(screen.getByText('8 / 500')).toBeTruthy();

    // Update bio
    const bioInput = screen.getByPlaceholderText('Tell us about yourself') as HTMLTextAreaElement;
    fireEvent.change(bioInput, { target: { value: 'New bio text' } });

    // Check updated character count
    expect(screen.getByText('12 / 500')).toBeTruthy();
  });
});
