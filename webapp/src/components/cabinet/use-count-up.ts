"use client";

import { useEffect, useRef, useState } from "react";

/*
 * Animates a numeric value toward its target with requestAnimationFrame.
 * Counts up (or down) over ~600ms with the same deceleration feel as
 * --ease-apple. Respects prefers-reduced-motion: the value snaps to the
 * target on the first frame instead of animating.
 */

const COUNT_UP_DURATION_MS = 600;

function easeOut(t: number): number {
  return 1 - Math.pow(1 - t, 3);
}

export function useCountUp(value: number): number {
  // Start from 0 so the first paint counts up to the loaded value.
  const [display, setDisplay] = useState(0);
  const frameRef = useRef<number | null>(null);
  const displayRef = useRef(0);

  useEffect(() => {
    const target = Number.isFinite(value) ? value : 0;
    const from = displayRef.current;
    if (from === target) return;

    const reduceMotion =
      typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const startedAt = performance.now();
    const step = (now: number) => {
      const progress = reduceMotion ? 1 : Math.min(1, (now - startedAt) / COUNT_UP_DURATION_MS);
      const next = progress >= 1 ? target : Math.round(from + (target - from) * easeOut(progress));
      displayRef.current = next;
      setDisplay(next);
      if (progress < 1) {
        frameRef.current = window.requestAnimationFrame(step);
      }
    };
    frameRef.current = window.requestAnimationFrame(step);

    return () => {
      if (frameRef.current !== null) window.cancelAnimationFrame(frameRef.current);
    };
  }, [value]);

  return display;
}

export default useCountUp;
