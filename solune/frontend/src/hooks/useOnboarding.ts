/**
 * useOnboarding — manages onboarding spotlight tour state with localStorage persistence.
 * Follows the useSidebarState try/catch pattern for localStorage access.
 */

import { useState, useCallback } from 'react';

const STORAGE_KEY = 'solune-onboarding-completed';
const TOTAL_STEPS = 9;

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

export function useOnboarding() {
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

  return {
    isActive,
    hasCompleted,
    currentStep,
    totalSteps: TOTAL_STEPS,
    next,
    prev,
    skip,
    restart,
  };
}
