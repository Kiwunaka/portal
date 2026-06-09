import Link from "next/link";

import JsonLd from "../../components/json-ld";
import { MarketingBrandLogo } from "../../components/marketing-brand-logo";
import { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND, getCopyText, getPokrovPublicConfig } from "../../lib/pokrov";

const config = getPokrovPublicConfig(process.env as Record<string, string | undefined>);

function firstNonEmpty(...values: Array<string | undefined>): string {
  return values.find((value) => Boolean(String(value || "").trim()))?.trim() || "";
}

function buildHelpHref(): string {
  return firstNonEmpty(config.docsUrl, config.supportTelegramUrl, config.webappUrl, "/");
}

function buildCabinetDownloadsHref(platform: "android" | "windows"): string {
  const url = new URL(config.webappUrl);
  url.pathname = "/downloads/";
  url.searchParams.set("platform", platform);
  return url.toString();
}

export const metadata = buildMarketingMetadata(
  getCopyText("marketing.install.meta.title", "Установка и помощь | POKROV"),
  getCopyText(
    "marketing.install.meta.description",
    "Как скачать приложение для Android и Windows, что делать если файл недоступен, и куда перейти за помощью.",
  ),
  {
    path: "/install/",
    noIndex: true,
    keywords: ["установка pokrov", "apk pokrov", "windows pokrov", "инструкция pokrov", "install help"],
  },
);

export default function InstallPage() {
  const helpHref = buildHelpHref();
  const androidHref = buildCabinetDownloadsHref("android");
  const windowsHref = buildCabinetDownloadsHref("windows");
  const androidHasArtifact = Boolean(String(config.androidApkUrl || "").trim());
  const windowsHasArtifact = Boolean(String(config.windowsExeUrl || "").trim());

  return (
    <>
      <JsonLd
        data={buildBreadcrumbJsonLd([
          { name: CANONICAL_PLATFORM_BRAND, path: "/" },
          { name: "Установка и помощь", path: "/install/" },
        ])}
      />
      <div className="lp-route-shell lp-route-shell--install">
        <header className="lp-nav">
          <div className="lp-nav-shell">
            <Link href="/" className="lp-brand">
              <MarketingBrandLogo className="lp-brand-logo" priority />
              <span>{CANONICAL_PLATFORM_BRAND}</span>
            </Link>
            <nav className="lp-menu" aria-label="Главная навигация">
              <div className="lp-nav-links">
                <Link href="/">Главная</Link>
                <Link href={MARKETING_CANONICAL_PATHS.devices}>Устройства</Link>
                <Link href={MARKETING_CANONICAL_PATHS.mobile}>На телефон</Link>
              </div>
              <div className="lp-nav-actions">
                <a href={config.webappUrl} target="_blank" rel="noreferrer" className="lp-chip">
                  Открыть кабинет
                </a>
                <a href={config.supportTelegramUrl} target="_blank" rel="noreferrer" className="lp-chip lp-chip--primary">
                  Поддержка
                </a>
              </div>
            </nav>
          </div>
        </header>

        <main id="main-content" className="lp-main lp-route-main lp-route-main--install">
          <section className="lp-hero">
            <div className="lp-hero-copy">
              <div className="lp-kicker">{getCopyText("marketing.install.kicker", "Установка POKROV")}</div>
              <p className="lp-overline">Android, Windows, кабинет и поддержка на одной странице.</p>
              <h1>{getCopyText("marketing.install.title", "Скачать POKROV или получить помощь")}</h1>
              <p className="lp-hero-lead">
                {getCopyText(
                  "marketing.install.subtitle",
                  "Файлы установки открываются через кабинет. Если файл недоступен вашему аккаунту, рядом остаётся инструкция и поддержка.",
                )}
              </p>
              <div className="lp-hero-actions">
                <a href={config.webappUrl} target="_blank" rel="noreferrer" className="lp-btn lp-btn--primary">
                  {getCopyText("marketing.install.primary_cta", "Открыть кабинет")}
                </a>
                <a href={config.supportTelegramUrl} target="_blank" rel="noreferrer" className="lp-btn lp-btn--ghost">
                  {getCopyText("marketing.install.secondary_cta", "Написать в поддержку")}
                </a>
              </div>
            </div>

            <div className="lp-hero-stage">
              <article className="lp-stage-card lp-stage-card--primary">
                <div className="lp-stage-label">Сначала кабинет, потом файл</div>
                <h2>Откройте кабинет и скачайте нужную версию.</h2>
                <p>
                  Если версия уже доступна вашему аккаунту, кабинет покажет актуальный файл. Если нет, рядом будет инструкция и канал помощи.
                </p>
                <ol className="lp-stage-steps">
                  <li>
                    <span>01</span>
                    <div>
                      <strong>Android</strong>
                      <p>APK открывается в кабинете для аккаунтов, которым доступна Android-версия.</p>
                    </div>
                  </li>
                  <li>
                    <span>02</span>
                    <div>
                      <strong>Windows</strong>
                      <p>Windows может показать предупреждение перед установкой, пока приложение не подписано.</p>
                    </div>
                  </li>
                  <li>
                    <span>03</span>
                    <div>
                      <strong>Поддержка</strong>
                      <p>Если что-то не сходится, откройте кабинет или напишите в Telegram.</p>
                    </div>
                  </li>
                </ol>
              </article>

              <article className="lp-stage-card">
                <div className="lp-stage-label">Если доступа к файлу нет</div>
                <p>
                  Если файл ещё не выдан вашему аккаунту, откройте инструкцию или напишите в поддержку.
                </p>
                <div className="lp-stage-links">
                  <a href={helpHref}>Открыть инструкцию</a>
                  <a href={config.webappUrl} target="_blank" rel="noreferrer">
                    Кабинет
                  </a>
                  <a href={config.supportTelegramUrl} target="_blank" rel="noreferrer">
                    Поддержка
                  </a>
                </div>
              </article>
            </div>
          </section>

          <section className="lp-section">
            <div className="lp-section-head">
              <span>Файлы установки</span>
              <h2>{getCopyText("marketing.install.downloads.title", "Откройте кабинет для файлов установки")}</h2>
              <p>
                {getCopyText(
                  "marketing.install.downloads.subtitle",
                  "Если версия доступна вашему аккаунту, она откроется в кабинете. Если нет, рядом остаётся помощь.",
                )}
              </p>
            </div>

            <div className="lp-download-grid">
              <article className="lp-platform-card lp-platform-card--featured">
                <div className="lp-stage-label">
                  <span aria-hidden="true">●</span>
                  {getCopyText("marketing.install.android.status", androidHasArtifact ? "Android доступен в кабинете" : "Проверьте Android в кабинете")}
                </div>
                <h3>{getCopyText("marketing.install.android.title", "Приложение для Android")}</h3>
                <p>
                  {getCopyText(
                    "marketing.install.android.desc",
                    "Android-файл для текущей беты открывается через кабинет. Не используйте случайные зеркала и стор-ссылки.",
                  )}
                </p>
                {androidHasArtifact ? (
                  <a href={androidHref} target="_blank" rel="noreferrer" className="lp-btn lp-btn--primary">
                    {getCopyText("marketing.download.android.cta", "Скачать в кабинете")}
                  </a>
                ) : (
                  <a href={helpHref} className="lp-btn lp-btn--primary">
                    {getCopyText("marketing.install.help_cta", "Открыть инструкцию")}
                  </a>
                )}
              </article>

              <article className="lp-platform-card">
                <div className="lp-stage-label">
                  <span aria-hidden="true">■</span>
                  {getCopyText("marketing.install.windows.status", windowsHasArtifact ? "Windows доступен в кабинете" : "Проверьте Windows в кабинете")}
                </div>
                <h3>{getCopyText("marketing.install.windows.title", "Приложение для Windows")}</h3>
                <p>
                  {getCopyText(
                    "marketing.install.windows.desc",
                    "Windows-файл для текущей беты открывается через кабинет. Система может показать предупреждение о неизвестном издателе.",
                  )}
                </p>
                {windowsHasArtifact ? (
                  <a href={windowsHref} target="_blank" rel="noreferrer" className="lp-btn lp-btn--primary">
                    {getCopyText("marketing.download.windows.cta", "Скачать в кабинете")}
                  </a>
                ) : (
                  <a href={helpHref} className="lp-btn lp-btn--primary">
                    {getCopyText("marketing.install.help_cta", "Открыть инструкцию")}
                  </a>
                )}
              </article>
            </div>
          </section>

          <section className="lp-section lp-info-band">
            <div className="lp-info-band__grid">
              <article className="lp-info-card">
                <span className="lp-info-card__eyebrow">Если файла пока нет в кабинете</span>
                <h3>Откройте инструкцию или поддержку</h3>
                <p>Если файл ещё не доступен аккаунту, мы покажем рабочий вариант: кабинет, инструкцию или Telegram-поддержку.</p>
              </article>
              <article className="lp-info-card">
                <span className="lp-info-card__eyebrow">Если нужен доступ</span>
                <h3>Кабинет показывает срок, устройства и продление</h3>
                <p>Там видно состояние доступа, связанные устройства и доступные действия без ручных профилей.</p>
              </article>
              <article className="lp-info-card">
                <span className="lp-info-card__eyebrow">Если нужен человек</span>
                <h3>Поддержка отвечает по делу</h3>
                <p>Telegram и почта помогают с установкой, доступом, оплатой и восстановлением.</p>
              </article>
            </div>
          </section>

          <section className="lp-section">
            <div className="lp-footer-cta">
              <div className="lp-footer-copy">
                <span>{getCopyText("marketing.install.help_eyebrow", "Если файл не открылся")}</span>
                <h2>{getCopyText("marketing.install.help_title", "Кабинет, Telegram и помощь остаются рядом")}</h2>
                <p>
                  {getCopyText(
                    "marketing.install.help_body",
                    "Если файла нет в кабинете, откройте инструкцию или напишите в поддержку. Мы подскажем, что делать дальше.",
                  )}
                </p>
              </div>
              <div className="lp-footer-actions">
                <a href={config.webappUrl} target="_blank" rel="noreferrer" className="lp-btn lp-btn--primary">
                  {getCopyText("marketing.install.primary_cta", "Открыть кабинет")}
                </a>
                <a href={config.supportTelegramUrl} target="_blank" rel="noreferrer" className="lp-btn lp-btn--ghost">
                  {getCopyText("marketing.install.secondary_cta", "Написать в поддержку")}
                </a>
                <Link href="/" className="lp-btn lp-btn--ghost">
                  {getCopyText("marketing.install.home_cta", "Вернуться на главную")}
                </Link>
              </div>
            </div>
          </section>
        </main>
      </div>
    </>
  );
}
