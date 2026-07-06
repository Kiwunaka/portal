"use client";

import { motion, useReducedMotion } from "framer-motion";
import { Zap } from "lucide-react";

import { AppPhoneIllustration } from "../illustrations/app-phone";

const EASE = [0.22, 1, 0.36, 1] as const;

function FloatingChip({
  children,
  className,
  delay = 0,
}: {
  children: React.ReactNode;
  className?: string;
  delay?: number;
}) {
  const reduceMotion = useReducedMotion();
  return (
    <motion.span
      aria-hidden="true"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay, ease: EASE }}
      className={`absolute z-10 ${className || ""}`}
    >
      <motion.span
        animate={reduceMotion ? undefined : { y: [0, -6, 0] }}
        transition={reduceMotion ? undefined : { duration: 4.5, delay, repeat: Infinity, ease: "easeInOut" }}
        className="flex items-center gap-1.5 rounded-full border border-line bg-surface px-3 py-1.5 text-xs font-semibold text-ink shadow-medium"
      >
        {children}
      </motion.span>
    </motion.span>
  );
}

/** Client hero visual: live app screen with gently floating trust chips. */
export function HeroVisual() {
  const reduceMotion = useReducedMotion();

  return (
    <div className="relative flex justify-center lg:justify-end">
      <motion.div
        initial={reduceMotion ? { opacity: 0 } : { opacity: 0, y: 20 }}
        animate={reduceMotion ? { opacity: 1 } : { opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: EASE }}
      >
        <AppPhoneIllustration variant="connect" />
      </motion.div>

      <FloatingChip delay={0.35} className="top-14 -left-1 sm:left-2 lg:-left-10">
        <Zap size={12} strokeWidth={1.5} fill="currentColor" className="text-status-green" aria-hidden="true" />
        1 тап — и работает
      </FloatingChip>

      <FloatingChip delay={0.55} className="right-0 bottom-24 sm:right-4 lg:-right-6">
        <span className="size-1.5 rounded-full bg-status-green" />
        YouTube снова быстрый
      </FloatingChip>
    </div>
  );
}
