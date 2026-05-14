"use client";

import { motion } from "framer-motion";
import type { ReactNode } from "react";

const MOTION_COMPONENTS = {
  div: motion.div,
  section: motion.section,
} as const;

interface FadeUpProps {
  children: ReactNode;
  delay?: number;
  className?: string;
  as?: keyof typeof MOTION_COMPONENTS;
}

export function FadeUp({ children, delay = 0, className, as = "div" }: FadeUpProps) {
  const MotionComponent = MOTION_COMPONENTS[as];

  return (
    <MotionComponent
      initial={{ opacity: 0, y: 32, filter: "blur(8px)" }}
      whileInView={{ opacity: 1, y: 0, filter: "blur(0px)" }}
      viewport={{ once: true, margin: "-10%" }}
      transition={{
        duration: 0.9,
        delay,
        ease: [0.32, 0.72, 0, 1], // Custom cubic-bezier for a natural spring feel
      }}
      className={className}
    >
      {children}
    </MotionComponent>
  );
}
