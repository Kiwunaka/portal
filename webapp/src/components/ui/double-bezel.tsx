"use client";

import { motion } from "framer-motion";
import type { ReactNode } from "react";

interface DoubleBezelProps {
  children: ReactNode;
  className?: string;
  innerClassName?: string;
  tone?: "default" | "success" | "warning" | "danger" | "info" | "glass";
  delay?: number;
}

export function DoubleBezel({ children, className = "", innerClassName = "", tone = "default", delay = 0 }: DoubleBezelProps) {
  const baseOuter = "relative transition-colors duration-200 ease-[cubic-bezier(0.32,0.72,0,1)]";
  const baseInner = "relative h-full w-full overflow-hidden transition-colors duration-200 ease-[cubic-bezier(0.32,0.72,0,1)]";

  let outerColors = "";
  let innerColors = "";

  switch (tone) {
    case "glass":
      outerColors = "rounded-[2rem] p-1.5 bg-white/5 ring-1 ring-black/5 dark:bg-black/10 dark:ring-white/10";
      innerColors = "rounded-[calc(2rem-0.375rem)] shadow-[inset_0_1px_1px_rgba(255,255,255,0.15)] bg-white/80 dark:bg-white/[0.04] backdrop-blur-xl";
      break;
    case "success":
      outerColors = "rounded-[2rem] p-1.5 bg-emerald-500/10 ring-1 ring-emerald-500/20 dark:bg-emerald-500/5";
      innerColors = "rounded-[calc(2rem-0.375rem)] shadow-[inset_0_1px_1px_rgba(255,255,255,0.15)] bg-emerald-50/90 dark:bg-emerald-900/20";
      break;
    case "warning":
      outerColors = "rounded-[2rem] p-1.5 bg-amber-500/10 ring-1 ring-amber-500/20 dark:bg-amber-500/5";
      innerColors = "rounded-[calc(2rem-0.375rem)] shadow-[inset_0_1px_1px_rgba(255,255,255,0.15)] bg-amber-50/90 dark:bg-amber-900/20";
      break;
    case "danger":
      outerColors = "rounded-[2rem] p-1.5 bg-rose-500/10 ring-1 ring-rose-500/20 dark:bg-rose-500/5";
      innerColors = "rounded-[calc(2rem-0.375rem)] shadow-[inset_0_1px_1px_rgba(255,255,255,0.15)] bg-rose-50/90 dark:bg-rose-900/20";
      break;
    case "info":
      outerColors = "rounded-[2rem] p-1.5 bg-blue-500/10 ring-1 ring-blue-500/20 dark:bg-blue-500/5";
      innerColors = "rounded-[calc(2rem-0.375rem)] shadow-[inset_0_1px_1px_rgba(255,255,255,0.15)] bg-blue-50/90 dark:bg-blue-900/20";
      break;
    default:
      outerColors = "rounded-[24px] border border-slate-200 shadow-sm dark:border-white/10 dark:shadow-none p-0 bg-white dark:bg-[#101713]";
      innerColors = "rounded-[24px]";
      break;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.995 }}
      whileInView={{ opacity: 1, y: 0, scale: 1 }}
      viewport={{ once: true, margin: "-10%" }}
      transition={{ duration: 0.28, delay, ease: [0.32, 0.72, 0, 1] }}
      className={`${baseOuter} ${outerColors} ${className}`}
    >
      <div className={`${baseInner} ${innerColors} ${innerClassName}`}>
        {children}
      </div>
    </motion.div>
  );
}
