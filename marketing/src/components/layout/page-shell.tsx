import Link from "next/link";
import type { ReactNode } from "react";

import { MarketingBrandLogo } from "../marketing-brand-logo";
import { Footer } from "./footer";
import { Topbar, type TopbarLabels } from "./topbar";
import { CANONICAL_PLATFORM_BRAND, CANONICAL_WEBAPP_URL, getCopyText } from "../../lib/pokrov";
import { MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";

/** Server shell: resolves copy for the client Topbar, wraps content, appends Footer. */
export function PageShell({ children, checkout = false }: { children: ReactNode; checkout?: boolean }) {
  const labels: TopbarLabels = {
    brand: CANONICAL_PLATFORM_BRAND,
    cabinet: getCopyText("marketing.topbar.cabinet", "Кабинет"),
    cabinetHref: CANONICAL_WEBAPP_URL,
    download: getCopyText("marketing.topbar.download", "Попробовать бесплатно"),
    downloadHref: MARKETING_CANONICAL_PATHS.install,
    menuClose: getCopyText("marketing.topbar.menu_close", "Закрыть меню"),
    menuOpen: getCopyText("marketing.topbar.menu_open", "Открыть меню"),
    nav: [
      { href: "/#features", label: getCopyText("marketing.topbar.nav.features", "Что откроется") },
      { href: "/#how-it-works", label: getCopyText("marketing.topbar.nav.how", "3 шага") },
      { href: "/#pricing", label: getCopyText("marketing.topbar.nav.pricing", "Тарифы от 99 ₽") },
      { href: "/#faq", label: getCopyText("marketing.topbar.nav.faq", "FAQ") },
    ],
  };

  if (checkout) {
    return (
      <>
        <header className="fixed inset-x-0 top-0 z-50 border-b border-line bg-canvas">
          <div className="mx-auto flex h-16 max-w-5xl items-center justify-between gap-4 px-4 sm:px-6">
            <Link href="/" className="flex min-h-11 items-center gap-2.5 no-underline" aria-label={labels.brand}>
              <MarketingBrandLogo width={32} height={32} priority />
              <span className="font-display text-[1.0625rem] font-bold tracking-[0.01em] text-ink">{labels.brand}</span>
            </Link>
            <span className="hidden text-[0.8125rem] font-medium text-ink-soft sm:inline">Разовая оплата · без подписки</span>
          </div>
        </header>
        <main id="main-content" className="pt-16">
          {children}
        </main>
        <Footer />
      </>
    );
  }

  return (
    <>
      <Topbar labels={labels} />
      <main id="main-content" className="pt-16">
        {children}
      </main>
      <Footer />
    </>
  );
}
