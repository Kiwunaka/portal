import Link from "next/link";

import { MarketingBrandLogo } from "../marketing-brand-logo";
import {
  CANONICAL_BOT_URL,
  CANONICAL_GITHUB_RELEASES_URL,
  CANONICAL_NEWS_CHANNEL_URL,
  CANONICAL_PLATFORM_BRAND,
  CANONICAL_SUPPORT_BOT_URL,
  CANONICAL_WEBAPP_URL,
  getCopyText,
} from "../../lib/pokrov";
import { MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";

type FooterLink = { external?: boolean; href: string; label: string };

function FooterColumn({ links, title }: { links: FooterLink[]; title: string }) {
  return (
    <div className="flex flex-col gap-3">
      <span className="text-[0.8125rem] font-semibold tracking-[0.08em] text-ink-muted uppercase">{title}</span>
      <ul className="m-0 flex list-none flex-col gap-2.5 p-0">
        {links.map((link) => (
          <li key={link.href}>
            {link.external ? (
              <a
                href={link.href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-[0.9375rem] text-ink-soft no-underline transition-colors duration-200 hover:text-ink"
              >
                {link.label}
              </a>
            ) : (
              <Link
                href={link.href}
                className="text-[0.9375rem] text-ink-soft no-underline transition-colors duration-200 hover:text-ink"
              >
                {link.label}
              </Link>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

export function Footer() {
  const productLinks: FooterLink[] = [
    { href: "/#features", label: getCopyText("marketing.footer.link.features", "Возможности") },
    { href: "/#pricing", label: getCopyText("marketing.footer.link.pricing", "Цены") },
    { href: MARKETING_CANONICAL_PATHS.install, label: getCopyText("marketing.footer.link.install", "Установка") },
    { href: CANONICAL_WEBAPP_URL, label: getCopyText("marketing.footer.link.cabinet", "Кабинет"), external: true },
  ];

  const supportLinks: FooterLink[] = [
    { href: CANONICAL_SUPPORT_BOT_URL, label: getCopyText("marketing.footer.link.support", "Поддержка в Telegram"), external: true },
    { href: CANONICAL_NEWS_CHANNEL_URL, label: getCopyText("marketing.footer.link.channel", "Канал с новостями"), external: true },
    { href: CANONICAL_BOT_URL, label: getCopyText("marketing.footer.link.bot", "Бот POKROV"), external: true },
    { href: CANONICAL_GITHUB_RELEASES_URL, label: getCopyText("marketing.footer.link.releases", "Файлы на GitHub"), external: true },
  ];

  const legalLinks: FooterLink[] = [
    { href: MARKETING_CANONICAL_PATHS.offer, label: getCopyText("marketing.footer.link.offer", "Публичная оферта") },
    { href: MARKETING_CANONICAL_PATHS.privacy, label: getCopyText("marketing.footer.link.privacy", "Конфиденциальность") },
  ];

  return (
    <footer className="border-t border-line bg-canvas-alt">
      <div className="mx-auto grid max-w-6xl gap-10 px-4 py-14 sm:px-6 md:grid-cols-[1.4fr_1fr_1fr_1fr]">
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-2.5">
            <MarketingBrandLogo width={32} height={32} />
            <span className="font-display text-[1.0625rem] font-bold text-ink">{CANONICAL_PLATFORM_BRAND}</span>
          </div>
          <p className="max-w-xs text-[0.9375rem] leading-relaxed text-ink-soft">
            {getCopyText(
              "marketing.footer.tagline",
              "Приложение для Android и Windows: одна кнопка — и любимые сервисы снова работают.",
            )}
          </p>
        </div>
        <FooterColumn title={getCopyText("marketing.footer.column.product", "Продукт")} links={productLinks} />
        <FooterColumn title={getCopyText("marketing.footer.column.support", "Помощь")} links={supportLinks} />
        <FooterColumn title={getCopyText("marketing.footer.column.legal", "Документы")} links={legalLinks} />
      </div>
      <div className="border-t border-line">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2 px-4 py-5 sm:px-6">
          <span className="text-[0.8125rem] text-ink-muted">
            © {new Date().getFullYear()} {CANONICAL_PLATFORM_BRAND}
          </span>
          <span className="text-[0.8125rem] text-ink-muted">
            {getCopyText("marketing.footer.beta_note", "Android и Windows, публичная бета")}
          </span>
        </div>
      </div>
    </footer>
  );
}
