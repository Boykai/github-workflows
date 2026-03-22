/**
 * FaqAccordion — collapsible FAQ grouped by category.
 * Exclusive toggle (one item open at a time), celestial-panel styling,
 * grid-template-rows animation, keyboard accessible.
 */

import { useState } from 'react';
import { ChevronDown } from '@/lib/icons';
import type { FaqEntry, FaqCategory } from '@/types';
import { cn } from '@/lib/utils';

interface FaqAccordionProps {
  entries: FaqEntry[];
}

const CATEGORY_LABELS: Record<FaqCategory, string> = {
  'getting-started': 'Getting Started',
  'agents-pipelines': 'Agents & Pipelines',
  'chat-voice': 'Chat & Voice',
  'settings-integration': 'Settings & Integration',
};

const CATEGORY_ORDER: FaqCategory[] = [
  'getting-started',
  'agents-pipelines',
  'chat-voice',
  'settings-integration',
];

export function FaqAccordion({ entries }: FaqAccordionProps) {
  const [openId, setOpenId] = useState<string | null>(null);

  const grouped = CATEGORY_ORDER.map((cat) => ({
    category: cat,
    label: CATEGORY_LABELS[cat],
    items: entries.filter((e) => e.category === cat),
  })).filter((g) => g.items.length > 0);

  const toggle = (id: string) => {
    setOpenId((prev) => (prev === id ? null : id));
  };

  return (
    <div className="space-y-8">
      {grouped.map((group) => (
        <div key={group.category}>
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-[0.24em] text-primary/70">
            {group.label}
          </h3>
          <div className="space-y-2">
            {group.items.map((item) => {
              const isOpen = openId === item.id;
              return (
                <div
                  key={item.id}
                  className="celestial-panel overflow-hidden rounded-2xl border border-border/50"
                >
                  <button
                    type="button"
                    id={`faq-question-${item.id}`}
                    aria-expanded={isOpen}
                    aria-controls={`faq-answer-${item.id}`}
                    className="flex w-full items-center justify-between gap-3 px-5 py-4 text-left text-sm font-medium text-foreground transition-colors hover:bg-primary/5"
                    onClick={() => toggle(item.id)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        toggle(item.id);
                      }
                    }}
                  >
                    <span>{item.question}</span>
                    <ChevronDown
                      className={cn(
                        'h-4 w-4 shrink-0 text-primary transition-transform duration-300',
                        isOpen && 'rotate-180',
                      )}
                    />
                  </button>
                  <div
                    id={`faq-answer-${item.id}`}
                    role="region"
                    aria-labelledby={`faq-question-${item.id}`}
                    className={cn(
                      'grid transition-[grid-template-rows] duration-300 ease-in-out',
                      isOpen ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]',
                    )}
                  >
                    <div className="overflow-hidden">
                      <div className="celestial-fade-in px-5 pb-4 text-sm leading-relaxed text-muted-foreground">
                        {item.answer}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
