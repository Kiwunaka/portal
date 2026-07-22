"use client";

import type { ReactNode } from "react";
import { useId, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { ChevronDown } from "lucide-react";

import { cn } from "@/components/utils";

/*
 * Illustrated instruction steps + FAQ accordion for cabinet surfaces.
 * Pictograms are inline SVG drawn with adaptive --pokrov-* variables,
 * so they follow light/dark themes without extra assets.
 */

export type StepArtKind = "download" | "login" | "connect" | "shield" | "link" | "refresh";

const ART_STROKE = "var(--pokrov-accent)";
const ART_SOFT = "var(--pokrov-status-success-bg)";
const ART_LINE = "var(--pokrov-line-strong)";

export function StepArt({ kind }: { kind: StepArtKind }) {
  const common = {
    width: 44,
    height: 44,
    viewBox: "0 0 44 44",
    fill: "none",
    "aria-hidden": true as const,
  };
  switch (kind) {
    case "download":
      return (
        <svg {...common}>
          <rect x="10" y="6" width="24" height="32" rx="5" fill={ART_SOFT} stroke={ART_LINE} strokeWidth="1.5" />
          <path d="M22 13v12m0 0-5-5m5 5 5-5" stroke={ART_STROKE} strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M16 32h12" stroke={ART_STROKE} strokeWidth="2.4" strokeLinecap="round" />
        </svg>
      );
    case "login":
      return (
        <svg {...common}>
          <circle cx="18" cy="16" r="6" fill={ART_SOFT} stroke={ART_STROKE} strokeWidth="2" />
          <path d="M8 36c1.6-6 5.4-9 10-9s8.4 3 10 9" stroke={ART_STROKE} strokeWidth="2.2" strokeLinecap="round" />
          <circle cx="32" cy="24" r="4" stroke={ART_STROKE} strokeWidth="2" />
          <path d="M35 27l4 4m-2-1-2 2" stroke={ART_STROKE} strokeWidth="2" strokeLinecap="round" />
        </svg>
      );
    case "connect":
      return (
        <svg {...common}>
          <circle cx="22" cy="24" r="11" fill={ART_SOFT} stroke={ART_STROKE} strokeWidth="2.2" />
          <path d="M22 13v9" stroke={ART_STROKE} strokeWidth="2.6" strokeLinecap="round" />
          <path d="M9.5 12.5a17 17 0 0 1 25 0" stroke={ART_LINE} strokeWidth="2" strokeLinecap="round" />
          <path d="M13.5 8a12 12 0 0 1 17 0" stroke={ART_LINE} strokeWidth="2" strokeLinecap="round" opacity="0.6" />
        </svg>
      );
    case "shield":
      return (
        <svg {...common}>
          <path d="M22 6l13 5v9c0 8.5-5.4 14.6-13 18-7.6-3.4-13-9.5-13-18v-9l13-5Z" fill={ART_SOFT} stroke={ART_STROKE} strokeWidth="2" strokeLinejoin="round" />
          <path d="M16 22.5l4.2 4.2L28.5 18" stroke={ART_STROKE} strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "link":
      return (
        <svg {...common}>
          <rect x="6" y="18" width="14" height="8" rx="4" stroke={ART_STROKE} strokeWidth="2.2" />
          <rect x="24" y="18" width="14" height="8" rx="4" stroke={ART_STROKE} strokeWidth="2.2" />
          <path d="M17 22h10" stroke={ART_STROKE} strokeWidth="2.6" strokeLinecap="round" />
        </svg>
      );
    case "refresh":
      return (
        <svg {...common}>
          <path d="M34 22a12 12 0 1 1-4-9" stroke={ART_STROKE} strokeWidth="2.4" strokeLinecap="round" />
          <path d="M34 7v7h-7" stroke={ART_STROKE} strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    default:
      return null;
  }
}

export type InstructionStep = {
  art: StepArtKind;
  title: ReactNode;
  description: ReactNode;
};

type InstructionStepsProps = {
  steps: InstructionStep[];
  className?: string;
};

export function InstructionSteps({ steps, className }: InstructionStepsProps) {
  return (
    <ol className={cn("m-0 grid list-none gap-3 p-0 sm:grid-cols-3", className)}>
      {steps.map((step, index) => (
        <li key={index} className="flex gap-3.5 rounded-card border border-line bg-surface p-4 shadow-soft sm:flex-col">
          <span className="relative grid size-14 shrink-0 place-items-center rounded-2xl bg-canvas-alt" aria-hidden="true">
            <StepArt kind={step.art} />
            <span className="absolute -top-1.5 -right-1.5 grid size-5 place-items-center rounded-full bg-brand text-[11px] font-bold text-brand-contrast">
              {index + 1}
            </span>
          </span>
          <span className="min-w-0">
            <span className="block text-sm font-semibold text-ink">{step.title}</span>
            <span className="mt-1 block text-[13px] leading-5 text-ink-soft">{step.description}</span>
          </span>
        </li>
      ))}
    </ol>
  );
}

export type FaqEntry = {
  question: ReactNode;
  answer: ReactNode;
};

type FaqAccordionProps = {
  entries: FaqEntry[];
  className?: string;
};

function FaqRow({ entry }: { entry: FaqEntry }) {
  const [open, setOpen] = useState(false);
  const reduceMotion = useReducedMotion();
  const regionId = useId();

  return (
    <div>
      <button
        type="button"
        aria-expanded={open}
        aria-controls={regionId}
        onClick={() => setOpen((value) => !value)}
        className="flex min-h-[52px] w-full items-center gap-3 px-4 py-3 text-left text-sm font-semibold text-ink transition-colors duration-150 hover:bg-canvas-alt motion-reduce:transition-none"
      >
        <span className="min-w-0 flex-1">{entry.question}</span>
        <motion.span
          animate={{ rotate: open ? 180 : 0 }}
          transition={{ duration: reduceMotion ? 0 : 0.24, ease: [0.22, 1, 0.36, 1] }}
          className="shrink-0 text-ink-muted"
        >
          <ChevronDown size={18} strokeWidth={2} aria-hidden="true" />
        </motion.span>
      </button>
      <AnimatePresence initial={false}>
        {open ? (
          <motion.div
            id={regionId}
            role="region"
            initial={reduceMotion ? { opacity: 0 } : { height: 0, opacity: 0 }}
            animate={reduceMotion ? { opacity: 1 } : { height: "auto", opacity: 1 }}
            exit={reduceMotion ? { opacity: 0 } : { height: 0, opacity: 0 }}
            transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 text-sm leading-6 whitespace-pre-line text-ink-soft">{entry.answer}</div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </div>
  );
}

export function FaqAccordion({ entries, className }: FaqAccordionProps) {
  return (
    <div className={cn("divide-y divide-line overflow-hidden rounded-card border border-line bg-surface shadow-soft", className)}>
      {entries.map((entry, index) => (
        <FaqRow key={index} entry={entry} />
      ))}
    </div>
  );
}
