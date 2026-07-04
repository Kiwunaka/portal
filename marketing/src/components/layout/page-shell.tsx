import type { ReactNode } from "react";

import { Footer } from "./footer";
import { Topbar, type TopbarLabels } from "./topbar";
import { CANONICAL_PLATFORM_BRAND, CANONICAL_WEBAPP_URL, getCopyText } from "../../lib/pokrov";
import { MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";

/** Server shell: resolves copy for the client Topbar, wraps content, appends Footer. */
export function PageShell({ children }: { children: ReactNode }) {
  const labels: TopbarLabels = {
    brand: CANONICAL_PLATFORM_BRAND,
    cabinet: getCopyText("marketing.topbar.cabinet", "Кабинет"),
    cabinetHref: CANONICAL_WEBAPP_URL,
    download: getCopyText("marketing.topbar.download", "Скачать"),
    downloadHref: MARKETING_CANONICAL_PATHS.install,
    menuClose: getCopyText("marketing.topbar.menu_close", "Закрыть меню"),
    menuOpen: getCopyText("marketing.topbar.menu_open", "Открыть меню"),
    nav: [
      { href: "/#features", label: getCopyText("marketing.topbar.nav.features", "Возможности") },
      { href: "/#how-it-works", label: getCopyText("marketing.topbar.nav.how", "Как это работает") },
      { href: "/#pricing", label: getCopyText("marketing.topbar.nav.pricing", "Цены") },
      { href: "/#faq", label: getCopyText("marketing.topbar.nav.faq", "FAQ") },
    ],
  };

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
