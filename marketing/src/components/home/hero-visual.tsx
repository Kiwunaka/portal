"use client";

import { motion, useMotionValue, useReducedMotion, useSpring, useTransform } from "framer-motion";
import { Zap } from "lucide-react";
import { useRef } from "react";

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

/** Client hero visual: live app screen with gently floating trust chips and a
 * subtle desktop pointer tilt (transform-only, reduced-motion safe). */
export function HeroVisual() {
  const reduceMotion = useReducedMotion();
  const frameRef = useRef<HTMLDivElement | null>(null);
  const pointerX = useMotionValue(0.5);
  const pointerY = useMotionValue(0.5);
  const rotateX = useSpring(useTransform(pointerY, [0, 1], [3.5, -3.5]), { stiffness: 180, damping: 24 });
  const rotateY = useSpring(useTransform(pointerX, [0, 1], [-4, 4]), { stiffness: 180, damping: 24 });

  const onPointerMove = (event: React.PointerEvent<HTMLDivElement>) => {
    if (reduceMotion || event.pointerType !== "mouse") return;
    const bounds = frameRef.current?.getBoundingClientRect();
    if (!bounds) return;
    pointerX.set((event.clientX - bounds.left) / bounds.width);
    pointerY.set((event.clientY - bounds.top) / bounds.height);
  };

  const onPointerLeave = () => {
    pointerX.set(0.5);
    pointerY.set(0.5);
  };

  return (
    <div className="relative flex justify-center lg:justify-end" style={{ perspective: 1100 }}>
      <motion.div
        ref={frameRef}
        onPointerMove={onPointerMove}
        onPointerLeave={onPointerLeave}
        initial={reduceMotion ? { opacity: 0 } : { opacity: 0, y: 20 }}
        animate={reduceMotion ? { opacity: 1 } : { opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: EASE }}
        style={reduceMotion ? undefined : { rotateX, rotateY, transformStyle: "preserve-3d" }}
      >
        <AppPhoneIllustration variant="connect" />
      </motion.div>

      <FloatingChip delay={0.35} className="top-14 -left-1 sm:left-2 lg:-left-10">
        <Zap size={12} strokeWidth={1.5} fill="currentColor" className="text-brand" aria-hidden="true" />
        1 тап — и работает
      </FloatingChip>

      <FloatingChip delay={0.55} className="top-36 -right-1 sm:right-0 lg:-right-8">
        <span className="size-1.5 rounded-full bg-brand" />
        YouTube снова быстрый
      </FloatingChip>
    </div>
  );
}
