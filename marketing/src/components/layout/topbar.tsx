"use client";

import Link from "next/link";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { Menu, X } from "lucide-react";
import { useEffect, useState } from "react";

import { MarketingBrandLogo } from "../marketing-brand-logo";
import { Button } from "../ui/button";
import { cn } from "../utils";

export type TopbarLabels = {
  brand: string;
  cabinet: string;
  cabinetHref: string;
  download: string;
  downloadHref: string;
  menuClose: string;
  menuOpen: string;
  nav: { href: string; label: string }[];
};

export function Topbar({ labels }: { labels: TopbarLabels }) {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const reduceMotion = useReducedMotion();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={cn(
        "fixed inset-x-0 top-0 z-50 bg-canvas transition-[box-shadow,border-color] duration-200 ease-(--ease-apple)",
        scrolled ? "border-b border-line shadow-soft" : "border-b border-transparent",
      )}
    >
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
        <Link href="/" className="flex min-h-11 items-center gap-2.5 no-underline" aria-label={labels.brand}>
          <MarketingBrandLogo width={32} height={32} priority />
          <span className="font-display text-[1.0625rem] font-bold tracking-[0.01em] text-ink">{labels.brand}</span>
        </Link>

        <nav className="hidden items-center gap-1 md:flex" aria-label="Основная навигация">
          {labels.nav.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="flex min-h-11 items-center rounded-full px-3.5 text-[0.9375rem] font-medium text-ink-soft no-underline transition-colors duration-200 hover:bg-canvas-alt hover:text-ink focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="hidden items-center gap-2 md:flex">
          <Button href={labels.cabinetHref} variant="ghost">
            {labels.cabinet}
          </Button>
          <Button href={labels.downloadHref} variant="primary">
            {labels.download}
          </Button>
        </div>

        <div className="flex items-center gap-1.5 md:hidden">
          <Button
            href={labels.downloadHref}
            variant="primary"
            className="px-4"
            aria-label={labels.download}
          >
            <span className="sm:hidden">Скачать</span>
            <span className="hidden sm:inline">{labels.download}</span>
          </Button>
          <button
            type="button"
            className="flex size-11 items-center justify-center rounded-full text-ink focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
            aria-expanded={menuOpen}
            aria-label={menuOpen ? labels.menuClose : labels.menuOpen}
            onClick={() => setMenuOpen((value) => !value)}
          >
            {menuOpen ? (
              <X size={20} strokeWidth={1.8} aria-hidden="true" />
            ) : (
              <Menu size={20} strokeWidth={1.8} aria-hidden="true" />
            )}
          </button>
        </div>
      </div>

      <AnimatePresence>
        {menuOpen ? (
          <motion.nav
            aria-label="Мобильная навигация"
            initial={reduceMotion ? { opacity: 0 } : { opacity: 0, y: -8 }}
            animate={reduceMotion ? { opacity: 1 } : { opacity: 1, y: 0 }}
            exit={reduceMotion ? { opacity: 0 } : { opacity: 0, y: -8 }}
            transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
            className="border-t border-line bg-canvas px-4 pt-2 pb-4 shadow-medium md:hidden"
          >
            <ul className="m-0 flex list-none flex-col p-0">
              {labels.nav.map((item) => (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    onClick={() => setMenuOpen(false)}
                    className="flex min-h-11 items-center rounded-(--radius-control) px-3 text-base font-medium text-ink no-underline hover:bg-canvas-alt focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
                  >
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
            <div className="mt-3 flex flex-col gap-2">
              <Button href={labels.cabinetHref} variant="secondary" className="w-full">
                {labels.cabinet}
              </Button>
              <Button href={labels.downloadHref} variant="primary" className="w-full">
                {labels.download}
              </Button>
            </div>
          </motion.nav>
        ) : null}
      </AnimatePresence>
    </header>
  );
}
