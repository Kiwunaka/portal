"use client";

import {
  Children,
  useEffect,
  useRef,
  useState,
  type CSSProperties,
  type ElementType,
  type ReactNode,
} from "react";

import { cn } from "../utils";

type RevealProps = {
  as?: ElementType;
  children: ReactNode;
  className?: string;
  /** Extra transition delay in ms (used by Stagger). */
  delay?: number;
  id?: string;
};

/**
 * Scroll reveal: rise 12px + fade, once, threshold 0.2.
 * Styling lives in globals.css (.reveal / .is-visible) so the
 * prefers-reduced-motion media query can collapse it to fade-only.
 */
export function Reveal({ as: Tag = "div", children, className, delay = 0, id }: RevealProps) {
  const ref = useRef<HTMLElement | null>(null);
  const [enhanced, setEnhanced] = useState(false);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    if (typeof IntersectionObserver === "undefined") {
      return;
    }
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setVisible(true);
            observer.disconnect();
            break;
          }
        }
      },
      { threshold: 0.2, rootMargin: "0px 0px -40px 0px" },
    );
    const enhancementFrame = window.requestAnimationFrame(() => {
      setEnhanced(true);
      observer.observe(node);
    });
    return () => {
      window.cancelAnimationFrame(enhancementFrame);
      observer.disconnect();
    };
  }, []);

  const style: CSSProperties | undefined = delay ? { transitionDelay: `${delay}ms` } : undefined;

  return (
    <Tag
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      ref={ref as any}
      id={id}
      className={cn("reveal", visible && "is-visible", className)}
      data-motion-enhanced={enhanced ? "true" : undefined}
      style={style}
    >
      {children}
    </Tag>
  );
}

type StaggerProps = {
  children: ReactNode;
  className?: string;
  /** Delay between children in ms. */
  step?: number;
};

/**
 * Staggers only compact groups. Delays stay within the motion contract:
 * <= 60 ms per item and <= 240 ms total. Long lists render together.
 */
export function Stagger({ children, className, step = 60 }: StaggerProps) {
  const items = Children.toArray(children);
  const boundedStep = Math.min(60, Math.max(0, step));
  const staggerCompactGroup = items.length <= 5;
  return (
    <>
      {items.map((child, index) => (
        <Reveal
          key={index}
          className={className}
          delay={staggerCompactGroup ? Math.min(index * boundedStep, 240) : 0}
        >
          {child}
        </Reveal>
      ))}
    </>
  );
}
