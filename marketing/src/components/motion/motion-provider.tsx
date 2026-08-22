"use client";

import { LazyMotion } from "framer-motion";
import type { ReactNode } from "react";

const loadMotionFeatures = () => import("./motion-features").then((module) => module.default);

export function MarketingMotionProvider({ children }: { children: ReactNode }) {
  return (
    <LazyMotion features={loadMotionFeatures} strict>
      {children}
    </LazyMotion>
  );
}
