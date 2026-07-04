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
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    if (typeof IntersectionObserver === "undefined") {
      setVisible(true);
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
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  const style: CSSProperties | undefined = delay ? { transitionDelay: `${delay}ms` } : undefined;

  return (
    <Tag
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      ref={ref as any}
      id={id}
      className={cn("reveal", visible && "is-visible", className)}
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

/** Wraps each child in a Reveal with an incremental delay. */
export function Stagger({ children, className, step = 60 }: StaggerProps) {
  const items = Children.toArray(children);
  return (
    <>
      {items.map((child, index) => (
        <Reveal key={index} className={className} delay={index * step}>
          {child}
        </Reveal>
      ))}
    </>
  );
}
