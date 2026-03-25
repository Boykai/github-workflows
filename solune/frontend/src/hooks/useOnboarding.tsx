/**
 * useOnboarding — manages onboarding spotlight tour state with localStorage persistence.
 * Uses React Context so all consumers (SpotlightTour, HelpPage) share the same state.
 * Follows the useSidebarState try/catch pattern for localStorage access.
 */

import { createContext, useContext, useState, useCallback } from 'react';

const STORAGE_KEY = 'solune-onboarding-completed';
const TOTAL_STEPS = 14;

function loadCompleted(): boolean {
  try {
    return localStorage.getItem(STORAGE_KEY) === 'true';
  } catch {
    return false;
  }
}

function saveCompleted(value: boolean): void {
  try {
    localStorage.setItem(STORAGE_KEY, String(value));
  } catch {
    /* ignore quota/privacy errors */
  }
}

interface OnboardingContextValue {
  isActive: boolean;
  hasCompleted: boolean;
  currentStep: number;
  totalSteps: number;
  next: () => void;
  prev: () => void;
  skip: () => void;
  restart: () => void;
}

const OnboardingContext = createContext<OnboardingContextValue | undefined>(undefined);

export function OnboardingProvider({ children }: { children: React.ReactNode }) {
  const [hasCompleted, setHasCompleted] = useState(loadCompleted);
  const [isActive, setIsActive] = useState(() => !loadCompleted());
  const [currentStep, setCurrentStep] = useState(0);

  const next = useCallback(() => {
    setCurrentStep((prev) => {
      if (prev >= TOTAL_STEPS - 1) {
        setIsActive(false);
        setHasCompleted(true);
        saveCompleted(true);
        return prev;
      }
      return prev + 1;
    });
  }, []);

  const prev = useCallback(() => {
    setCurrentStep((prev) => Math.max(0, prev - 1));
  }, []);

  const skip = useCallback(() => {
    setIsActive(false);
    setHasCompleted(true);
    saveCompleted(true);
  }, []);

  const restart = useCallback(() => {
    setCurrentStep(0);
    setIsActive(true);
  }, []);

  return (
    <OnboardingContext.Provider
      value={{ isActive, hasCompleted, currentStep, totalSteps: TOTAL_STEPS, next, prev, skip, restart }}
    >
      {children}
    </OnboardingContext.Provider>
  );
}

export function useOnboarding(): OnboardingContextValue {
  const ctx = useContext(OnboardingContext);
  if (!ctx) {
    throw new Error('useOnboarding must be used within an OnboardingProvider');
  }
  return ctx;
}
