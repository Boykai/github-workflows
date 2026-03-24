/**
 * SpotlightTour — orchestrator that composes SpotlightOverlay + SpotlightTooltip.
 * Defines the 14-step tour, manages target element detection, rect computation,
 * keyboard shortcuts, sidebar auto-expand, and aria-live announcements.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useOnboarding } from '@/hooks/useOnboarding';
import { SpotlightOverlay } from './SpotlightOverlay';
import { SpotlightTooltip } from './SpotlightTooltip';
import type { TourStep } from '@/types';
import {
  SunMoonIcon,
  CompassRoseIcon,
  StarChartIcon,
  ChatStarsIcon,
  ConstellationGridIcon,
  OrbitalRingsIcon,
  CelestialHandIcon,
  SunMoonToggleIcon,
  BookStarsIcon,
  TimelineStarsIcon,
} from '@/assets/onboarding/icons';

const TOUR_STEPS: TourStep[] = [
  {
    id: 1,
    targetSelector: null,
    title: 'Welcome to Solune',
    description: 'Your celestial workspace for agent-driven development. Let us show you around — it only takes a minute.',
    icon: SunMoonIcon,
    placement: 'bottom',
  },
  {
    id: 2,
    targetSelector: 'sidebar-nav',
    title: 'Sidebar Navigation',
    description: 'Access all areas of Solune from here. Each section has its own dedicated workspace.',
    icon: CompassRoseIcon,
    placement: 'right',
  },
  {
    id: 3,
    targetSelector: 'project-selector',
    title: 'Project Selector',
    description: 'Link a GitHub repository to get started. All boards, pipelines, and agents operate within your selected project.',
    icon: StarChartIcon,
    placement: 'right',
  },
  {
    id: 4,
    targetSelector: 'chat-toggle',
    title: 'Chat with Solune',
    description: 'Open the chat to create tasks, ask questions, or trigger agent workflows using natural language.',
    icon: ChatStarsIcon,
    placement: 'left',
  },
  {
    id: 5,
    targetSelector: 'projects-link',
    title: 'Projects Board',
    description: 'View and manage your project issues on a Kanban-style board with drag-and-drop status updates.',
    icon: ConstellationGridIcon,
    placement: 'right',
  },
  {
    id: 6,
    targetSelector: 'pipeline-link',
    title: 'Agent Pipelines',
    description: 'Define multi-step agent workflows that automatically process issues through your pipeline stages.',
    icon: OrbitalRingsIcon,
    placement: 'right',
  },
  {
    id: 7,
    targetSelector: 'agents-link',
    title: 'Agents',
    description: 'Browse, configure, and manage the AI agents available for your pipelines and chat commands.',
    icon: CelestialHandIcon,
    placement: 'right',
  },
  {
    id: 8,
    targetSelector: 'theme-toggle',
    title: 'Theme Toggle',
    description: 'Switch between light and dark mode. The celestial design adapts to your preference.',
    icon: SunMoonToggleIcon,
    placement: 'right',
  },
  {
    id: 9,
    targetSelector: 'help-link',
    title: 'Help & FAQ',
    description: 'Find answers, feature guides, and slash commands anytime. You can also replay this tour from there.',
    icon: BookStarsIcon,
    placement: 'right',
  },
  {
    id: 10,
    targetSelector: 'tools-link',
    title: 'Tools',
    description: 'Upload and manage MCP tool configurations that extend your agents with external capabilities.',
    icon: CelestialHandIcon,
    placement: 'right',
  },
  {
    id: 11,
    targetSelector: 'chores-link',
    title: 'Chores',
    description: 'Schedule recurring repository maintenance tasks and automate routine upkeep.',
    icon: OrbitalRingsIcon,
    placement: 'right',
  },
  {
    id: 12,
    targetSelector: 'settings-link',
    title: 'Settings',
    description: 'Configure project settings, workflow preferences, and integration options.',
    icon: StarChartIcon,
    placement: 'right',
  },
  {
    id: 13,
    targetSelector: 'apps-link',
    title: 'Apps',
    description: 'Create and manage applications — spin up new repos, link external ones, and monitor app status.',
    icon: ConstellationGridIcon,
    placement: 'right',
  },
  {
    id: 14,
    targetSelector: 'activity-link',
    title: 'Activity',
    description: 'Track recent actions, events, and changes across your workspace in a unified timeline.',
    icon: TimelineStarsIcon,
    placement: 'right',
  },
];

interface SpotlightTourProps {
  isSidebarCollapsed: boolean;
  onToggleSidebar: () => void;
}

export function SpotlightTour({ isSidebarCollapsed, onToggleSidebar }: SpotlightTourProps) {
  const { isActive, currentStep, totalSteps, next, prev, skip } = useOnboarding();
  const [targetRect, setTargetRect] = useState<DOMRect | null>(null);
  const wasCollapsedRef = useRef<boolean | null>(null);
  const announcerRef = useRef<HTMLDivElement>(null);

  const step = TOUR_STEPS[currentStep];

  // Compute target element bounding rect (called on scroll/resize — no scrollIntoView here)
  const updateRect = useCallback(() => {
    if (!step?.targetSelector) {
      setTargetRect(null);
      return;
    }
    const el = document.querySelector(`[data-tour-step="${step.targetSelector}"]`);
    if (el) {
      setTargetRect(el.getBoundingClientRect());
    } else {
      setTargetRect(null);
    }
  }, [step]);

  // On step change: scroll target into view and skip missing targets
  useEffect(() => {
    if (!isActive || !step?.targetSelector) return;

    const el = document.querySelector(`[data-tour-step="${step.targetSelector}"]`);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } else {
      // Target not found — advance past this step so the user isn't stranded
      next();
    }
  }, [isActive, step, next]);

  // Auto-expand sidebar for sidebar-related steps (steps 2–9)
  useEffect(() => {
    if (!isActive) {
      // Restore sidebar on tour end
      if (wasCollapsedRef.current === true) {
        onToggleSidebar();
        wasCollapsedRef.current = null;
      }
      return;
    }

    if (currentStep >= 1 && isSidebarCollapsed) {
      if (wasCollapsedRef.current === null) {
        wasCollapsedRef.current = true;
      }
      onToggleSidebar();
    }
  }, [isActive, currentStep, isSidebarCollapsed, onToggleSidebar]);

  // Update rect on step change and window events
  useEffect(() => {
    if (!isActive) return;

    // Slight delay to let sidebar expansion settle
    const timer = setTimeout(updateRect, 150);

    const handleResize = () => updateRect();
    window.addEventListener('resize', handleResize);
    window.addEventListener('scroll', handleResize, true);

    // ResizeObserver for layout changes
    const observer = new ResizeObserver(handleResize);
    observer.observe(document.body);

    return () => {
      clearTimeout(timer);
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('scroll', handleResize, true);
      observer.disconnect();
    };
  }, [isActive, currentStep, updateRect]);

  // Keyboard navigation
  useEffect(() => {
    if (!isActive) return;
    const handler = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowRight':
          e.preventDefault();
          next();
          break;
        case 'ArrowLeft':
          e.preventDefault();
          prev();
          break;
        case 'Escape':
          e.preventDefault();
          skip();
          break;
      }
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [isActive, next, prev, skip]);

  // Aria-live announcements
  useEffect(() => {
    if (!isActive || !step || !announcerRef.current) return;
    announcerRef.current.textContent = `Step ${currentStep + 1} of ${totalSteps}: ${step.title}. ${step.description}`;
  }, [isActive, currentStep, step, totalSteps]);

  if (!isActive || !step) return null;

  return (
    <>
      <SpotlightOverlay targetRect={targetRect} isVisible={isActive} />
      <SpotlightTooltip
        step={step}
        targetRect={targetRect}
        currentStep={currentStep}
        totalSteps={totalSteps}
        onNext={next}
        onBack={prev}
        onSkip={skip}
      />
      {/* Screen reader announcer */}
      <div
        ref={announcerRef}
        role="status"
        aria-live="polite"
        className="sr-only"
      />
    </>
  );
}
