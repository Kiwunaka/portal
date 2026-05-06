"use client";

import { motion } from "framer-motion";
import type { ReactNode, ElementType } from "react";

interface FadeUpProps {
  children: ReactNode;
  delay?: number;
  className?: string;
  as?: ElementType;
  id?: string;
}

export function FadeUp({ children, delay = 0, className, id, as: Component = "div" }: FadeUpProps) {
  const MotionComponent = motion(Component as any);

  return (
    <MotionComponent
      id={id}
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
