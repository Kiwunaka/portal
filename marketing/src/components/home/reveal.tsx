"use client";

import { useEffect, useRef, type ReactNode } from "react";

type RevealProps = { children: ReactNode; className?: string; delay?: number };

/**
 * Scroll-reveal wrapper. SSR/no-JS/reduced-motion safe: content is always
 * rendered visible; JS only hides off-screen blocks and animates them in.
 */
export function Reveal({ children, className, delay = 0 }: RevealProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el || typeof IntersectionObserver === "undefined") return;
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;

    const easing = "opacity .7s cubic-bezier(.22,1,.36,1), transform .7s cubic-bezier(.22,1,.36,1)";
    let hidden = false;
    const io = new IntersectionObserver(
      (entries) => {
        const entry = entries[0];
        if (!entry) return;
        if (entry.isIntersecting) {
          el.style.transition = easing;
          el.style.transitionDelay = delay ? `${delay}ms` : "";
          el.style.opacity = "1";
          el.style.transform = "none";
          io.disconnect();
          el.addEventListener(
            "transitionend",
            () => {
              el.style.transition = "";
              el.style.transitionDelay = "";
              el.style.opacity = "";
              el.style.transform = "";
              el.style.willChange = "";
            },
            { once: true },
          );
        } else if (!hidden) {
          hidden = true;
          el.style.willChange = "opacity, transform";
          el.style.opacity = "0";
          el.style.transform = "translateY(22px)";
        }
      },
      { threshold: 0.12, rootMargin: "0px 0px -6% 0px" },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [delay]);

  return (
    <div ref={ref} className={className}>
      {children}
    </div>
  );
}

export default Reveal;
