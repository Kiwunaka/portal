"use client";

import { useEffect, useState } from "react";
import { useMotionValueEvent, useReducedMotion, useSpring } from "framer-motion";

import { cn } from "@/components/utils";
import { ruPlural } from "@/lib/ru-plural";

const SPRING = { stiffness: 120, damping: 26, mass: 0.9 } as const;

function useAnimatedInteger(value: number): number {
  const target = Number.isFinite(value) ? Math.round(value) : 0;
  const reduceMotion = useReducedMotion();
  const spring = useSpring(target, SPRING);
  const [display, setDisplay] = useState(target);

  useMotionValueEvent(spring, "change", (next) => setDisplay(Math.round(next)));

  useEffect(() => {
    if (reduceMotion) {
      spring.jump(target);
      return;
    }
    spring.set(target);
  }, [reduceMotion, spring, target]);

  return reduceMotion ? target : display;
}

export function AnimatedNumber({ value, className }: { value: number; className?: string }) {
  const display = useAnimatedInteger(value);
  return <span className={cn("tabular-nums", className)}>{display}</span>;
}

export function AnimatedDays({ value, className }: { value: number; className?: string }) {
  const display = useAnimatedInteger(value);
  return (
    <span className={className}>
      <span className="tabular-nums">{display}</span> {ruPlural(display, "день", "дня", "дней")}
    </span>
  );
}
