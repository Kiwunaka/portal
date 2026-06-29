"use client";

import { AnimatePresence, motion } from "framer-motion";
import { usePathname } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

type Metrics = {
  interactive: number;
  links: number;
  buttons: number;
  inputs: number;
  disabled: number;
  iconOnlyButtons: number;
};

type LinkStatus = {
  href: string;
  status: number;
};

const INTERACTIVE_SELECTOR =
  "a,button,input,textarea,select,[role='button'],label[for],summary,[tabindex]:not([tabindex='-1'])";

const PANEL_EASE = [0.22, 1, 0.36, 1] as const;

function isVisible(el: HTMLElement): boolean {
  const style = window.getComputedStyle(el);
  if (style.display === "none" || style.visibility === "hidden") return false;
  if (el.getAttribute("aria-hidden") === "true") return false;
  return true;
}

function collectMetrics(): Metrics {
  const nodes = Array.from(document.querySelectorAll<HTMLElement>(INTERACTIVE_SELECTOR)).filter(isVisible);

  const links = nodes.filter((node) => node.tagName === "A");
  const buttons = nodes.filter((node) => node.tagName === "BUTTON" || node.getAttribute("role") === "button");
  const inputs = nodes.filter((node) => ["INPUT", "TEXTAREA", "SELECT"].includes(node.tagName));
  const disabled = nodes.filter(
    (node) =>
      node.hasAttribute("disabled") ||
      node.getAttribute("aria-disabled") === "true" ||
      (node as HTMLInputElement).disabled === true,
  );

  const iconOnlyButtons = Array.from(document.querySelectorAll<HTMLButtonElement>("button")).filter((button) => {
    if (!isVisible(button)) return false;
    if (button.getAttribute("aria-label")) return false;
    if (button.getAttribute("title")) return false;
    const hasMaterialIcon = Boolean(button.querySelector("svg, .material-symbols-rounded, .material-symbols-outlined"));
    const text = (button.textContent || "").replace(/\s+/g, " ").trim();
    return hasMaterialIcon && (text.length === 0 || /^[a-z_]+$/i.test(text));
  });

  return {
    interactive: nodes.length,
    links: links.length,
    buttons: buttons.length,
    inputs: inputs.length,
    disabled: disabled.length,
    iconOnlyButtons: iconOnlyButtons.length,
  };
}

async function scanInternalLinks(): Promise<LinkStatus[]> {
  const hrefs = Array.from(document.querySelectorAll<HTMLAnchorElement>("a[href^='/']"))
    .map((a) => a.getAttribute("href") || "")
    .filter(Boolean);

  const unique = [...new Set(hrefs)].slice(0, 24);

  const results = await Promise.all(
    unique.map(async (href) => {
      try {
        const response = await fetch(href, { method: "GET", cache: "no-store" });
        return { href, status: response.status };
      } catch {
        return { href, status: 0 };
      }
    }),
  );

  return results;
}

export default function QaOverlay() {
  const pathname = usePathname();
  const [open, setOpen] = useState<boolean>(() => {
    if (typeof window === "undefined") return false;
    return localStorage.getItem("portal-qa-open") === "1";
  });
  const [hitbox, setHitbox] = useState<boolean>(() => {
    if (typeof window === "undefined") return false;
    return localStorage.getItem("portal-qa-hitbox") === "1";
  });
  const [metrics, setMetrics] = useState<Metrics>(() => ({
    interactive: 0,
    links: 0,
    buttons: 0,
    inputs: 0,
    disabled: 0,
    iconOnlyButtons: 0,
  }));
  const [scanning, setScanning] = useState(false);
  const [links, setLinks] = useState<LinkStatus[]>([]);

  useEffect(() => {
    localStorage.setItem("portal-qa-open", open ? "1" : "0");
  }, [open]);

  useEffect(() => {
    localStorage.setItem("portal-qa-hitbox", hitbox ? "1" : "0");
    document.body.classList.toggle("qa-hitbox", hitbox);
    return () => {
      document.body.classList.remove("qa-hitbox");
    };
  }, [hitbox]);

  useEffect(() => {
    const recalc = (): void => setMetrics(collectMetrics());
    const schedule = window.setTimeout(recalc, 60);
    return () => window.clearTimeout(schedule);
  }, [pathname, open]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent): void => {
      if (event.ctrlKey && event.shiftKey && event.key.toLowerCase() === "q") {
        event.preventDefault();
        setOpen((prev) => !prev);
      }
      if (event.key === "Escape") {
        setOpen(false);
      }
    };

    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const brokenCount = useMemo(() => links.filter((item) => item.status >= 400 || item.status === 0).length, [links]);

  const runLinkScan = async (): Promise<void> => {
    setScanning(true);
    const result = await scanInternalLinks();
    setLinks(result);
    setScanning(false);
  };

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        data-testid="qa-overlay-toggle"
        className="haptic-tap fixed bottom-[calc(5.5rem+var(--tg-safe-area-bottom,0px))] left-3 z-[260] rounded-full border border-cyan-300/60 bg-cyan-500/90 px-3 py-2 font-mono text-[11px] font-bold uppercase tracking-[0.14em] text-white shadow-xl"
        aria-label="Открыть QA overlay"
      >
        QA
      </button>

      <AnimatePresence>
        {open ? (
          <motion.aside
            data-testid="qa-overlay-panel"
            initial={{ opacity: 0, y: 14, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 14, scale: 0.96 }}
            transition={{ duration: 0.2, ease: PANEL_EASE }}
            className="fixed bottom-[calc(8.5rem+var(--tg-safe-area-bottom,0px))] left-3 z-[260] w-[min(92vw,360px)] rounded-2xl border border-cyan-300/40 bg-slate-950/92 p-4 text-cyan-100 shadow-2xl backdrop-blur-xl"
          >
            <div className="mb-3 flex items-center justify-between">
              <div>
                <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-cyan-300">qa overlay</p>
                <p className="text-xs text-cyan-100/80">{pathname}</p>
              </div>
              <button
                type="button"
                onClick={() => setOpen(false)}
                className="haptic-tap rounded-lg border border-cyan-200/15 bg-cyan-50/10 px-2 py-1 text-xs text-cyan-50"
                aria-label="Закрыть QA overlay"
              >
                close
              </button>
            </div>

            <div className="grid grid-cols-3 gap-2 text-[11px]">
              <div data-testid="qa-metric-interactive" className="rounded-lg border border-cyan-200/10 bg-cyan-50/10 p-2 text-cyan-50">
                UI: {metrics.interactive}
              </div>
              <div data-testid="qa-metric-links" className="rounded-lg border border-cyan-200/10 bg-cyan-50/10 p-2 text-cyan-50">
                Links: {metrics.links}
              </div>
              <div data-testid="qa-metric-buttons" className="rounded-lg border border-cyan-200/10 bg-cyan-50/10 p-2 text-cyan-50">
                Btns: {metrics.buttons}
              </div>
              <div data-testid="qa-metric-inputs" className="rounded-lg border border-cyan-200/10 bg-cyan-50/10 p-2 text-cyan-50">
                Inputs: {metrics.inputs}
              </div>
              <div data-testid="qa-metric-disabled" className="rounded-lg border border-cyan-200/10 bg-cyan-50/10 p-2 text-cyan-50">
                Disabled: {metrics.disabled}
              </div>
              <div data-testid="qa-metric-icon-only" className="rounded-lg border border-cyan-200/10 bg-cyan-50/10 p-2 text-cyan-50">
                Icon-only: {metrics.iconOnlyButtons}
              </div>
            </div>

            <div className="mt-3 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => setMetrics(collectMetrics())}
                data-testid="qa-overlay-refresh"
                className="haptic-tap rounded-lg border border-cyan-200/15 bg-cyan-50/10 px-2.5 py-1.5 text-[11px] text-cyan-50"
              >
                Обновить
              </button>
              <button
                type="button"
                onClick={() => setHitbox((prev) => !prev)}
                data-testid="qa-overlay-hitbox"
                className={`haptic-tap rounded-lg border px-2.5 py-1.5 text-[11px] ${hitbox ? "border-cyan-300/35 bg-cyan-500/85 text-white" : "border-cyan-200/15 bg-cyan-50/10 text-cyan-50"}`}
              >
                Hitbox {hitbox ? "ON" : "OFF"}
              </button>
              <button
                type="button"
                onClick={runLinkScan}
                disabled={scanning}
                data-testid="qa-overlay-link-scan"
                className="haptic-tap rounded-lg border border-cyan-200/15 bg-cyan-50/10 px-2.5 py-1.5 text-[11px] text-cyan-50 disabled:opacity-50"
              >
                {scanning ? "Сканируем..." : "Проверить ссылки"}
              </button>
            </div>

            {links.length > 0 ? (
              <div data-testid="qa-overlay-link-results" className="mt-3 rounded-xl border border-cyan-200/10 bg-cyan-50/10 p-2.5">
                <p data-testid="qa-overlay-broken-count" className="text-[11px] text-cyan-100/85">
                  Broken: {brokenCount}
                </p>
                <div className="mt-2 max-h-24 space-y-1 overflow-y-auto pr-1 text-[10px]">
                  {links.map((item) => (
                    <div key={item.href} className="flex items-center justify-between gap-2">
                      <span className="truncate text-cyan-50/90">{item.href}</span>
                      <span className={item.status >= 400 || item.status === 0 ? "text-rose-300" : "text-emerald-300"}>
                        {item.status || "ERR"}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}

            <p className="mt-3 text-[10px] text-cyan-100/65">Ctrl+Shift+Q • Esc</p>
          </motion.aside>
        ) : null}
      </AnimatePresence>
    </>
  );
}
