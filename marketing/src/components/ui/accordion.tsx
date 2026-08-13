"use client";

import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { Plus } from "lucide-react";
import { useId, useState, type ReactNode } from "react";

import { cn } from "../utils";

export type AccordionItem = {
  answer: ReactNode;
  question: string;
};

function AccordionRow({ item, defaultOpen = false }: { item: AccordionItem; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen);
  const reduceMotion = useReducedMotion();
  const regionId = useId();

  return (
    <div className="border-b border-line last:border-b-0">
      <button
        type="button"
        aria-expanded={open}
        aria-controls={regionId}
        onClick={() => setOpen((value) => !value)}
        className="flex min-h-11 w-full items-center justify-between gap-4 py-5 text-left focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
      >
        <span className="text-base font-semibold text-ink">{item.question}</span>
        <span
          aria-hidden="true"
          className={cn(
            "flex size-7 shrink-0 items-center justify-center rounded-full bg-brand-soft text-brand transition-transform duration-300 ease-(--ease-spring)",
            open && "rotate-45",
          )}
        >
          <Plus size={14} strokeWidth={2} aria-hidden="true" />
        </span>
      </button>
      <AnimatePresence initial={false}>
        {open ? (
          <motion.div
            id={regionId}
            role="region"
            initial={reduceMotion ? { opacity: 0 } : { height: 0, opacity: 0 }}
            animate={reduceMotion ? { opacity: 1 } : { height: "auto", opacity: 1 }}
            exit={reduceMotion ? { opacity: 0 } : { height: 0, opacity: 0 }}
            transition={{ duration: 0.32, ease: [0.22, 1, 0.36, 1] }}
            className="overflow-hidden"
          >
            <p className="max-w-2xl pb-5 text-[0.9375rem] leading-relaxed text-ink-soft">{item.answer}</p>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </div>
  );
}

export function Accordion({
  className,
  defaultOpenFirst = true,
  items,
}: {
  className?: string;
  defaultOpenFirst?: boolean;
  items: AccordionItem[];
}) {
  return (
    <div className={cn("rounded-(--radius-panel) border border-line bg-surface px-6 shadow-soft sm:px-8", className)}>
      {items.map((item, index) => (
        <AccordionRow key={item.question} item={item} defaultOpen={defaultOpenFirst && index === 0} />
      ))}
    </div>
  );
}
