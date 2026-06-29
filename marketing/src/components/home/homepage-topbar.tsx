"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { MarketingBrandLogo } from "../marketing-brand-logo";
import styles from "./homepage.module.css";

type TopbarProps = { cabinetHref: string; installHref: string };

const NAV = [
  { href: "#features", label: "Возможности" },
  { href: "#how-it-works", label: "Как начать" },
  { href: "#pricing", label: "Тарифы" },
  { href: "#faq", label: "FAQ" },
];

function Arrow() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M5 12h13M13 6.5 18.5 12 13 17.5" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export default function HomepageTopbar({ cabinetHref, installHref }: TopbarProps) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prev;
    };
  }, [open]);

  return (
    <>
      <header className={styles.topbar}>
        <Link href="/" className={styles.brand}>
          <MarketingBrandLogo className={styles.brandMark} priority />
          <span className={styles.brandText}>
            <strong>POKROV</strong>
            <small>Android и Windows · бета</small>
          </span>
        </Link>

        <nav className={styles.nav} aria-label="Навигация по главной">
          {NAV.map((item) => (
            <a key={item.href} href={item.href}>
              {item.label}
            </a>
          ))}
        </nav>

        <div className={styles.topbarActions}>
          <a href={cabinetHref} className={styles.btnGhost}>
            Кабинет
          </a>
          <Link href={installHref} className={`${styles.btnPrimary} ${styles.btnMagnet} ${styles.topbarCta}`}>
            Попробовать бесплатно
            <span className={styles.btnArrow}>
              <Arrow />
            </span>
          </Link>
          <button
            type="button"
            className={styles.menuBtn}
            aria-label="Открыть меню"
            aria-expanded={open}
            onClick={() => setOpen(true)}
          >
            <span className={styles.menuBars}>
              <span />
              <span />
            </span>
          </button>
        </div>
      </header>

      <div className={styles.menuOverlay} data-open={open} role="dialog" aria-modal="true" aria-hidden={!open} onClick={() => setOpen(false)}>
        <div className={styles.menuPanel} onClick={(e) => e.stopPropagation()}>
          <div className={styles.menuTop}>
            <span className={styles.brand}>
              <MarketingBrandLogo className={styles.brandMark} />
              <span className={styles.brandText}>
                <strong>POKROV</strong>
              </span>
            </span>
            <button type="button" className={styles.menuClose} aria-label="Закрыть меню" onClick={() => setOpen(false)}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path d="M6 6l12 12M18 6 6 18" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
              </svg>
            </button>
          </div>
          <nav className={styles.menuNav} aria-label="Меню">
            {NAV.map((item, index) => (
              <a key={item.href} href={item.href} style={{ transitionDelay: open ? `${0.06 + index * 0.05}s` : "0s" }} onClick={() => setOpen(false)}>
                {item.label}
              </a>
            ))}
          </nav>
          <div className={styles.menuActions}>
            <Link href={installHref} className={`${styles.btnPrimary} ${styles.btnLg} ${styles.btnMagnet}`} onClick={() => setOpen(false)}>
              Попробовать 5 дней бесплатно
              <span className={styles.btnArrow}>
                <Arrow />
              </span>
            </Link>
            <a href={cabinetHref} className={`${styles.btnSecondary} ${styles.btnLg}`} onClick={() => setOpen(false)}>
              Открыть кабинет
            </a>
          </div>
        </div>
      </div>
    </>
  );
}
