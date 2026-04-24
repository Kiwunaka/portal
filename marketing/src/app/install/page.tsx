import Link from "next/link";

import JsonLd from "../../components/json-ld";
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

function buildArtifactHref(primary: string, fallback: string): string {
  return firstNonEmpty(primary, fallback);
}

export const metadata = buildMarketingMetadata(
  getCopyText("marketing.install.meta.title", "Установка и помощь | POKROV"),
  getCopyText(
    "marketing.install.meta.description",
    "Как установить POKROV на Android и Windows, что делать если файл недоступен, и куда обратиться за помощью.",
  ),
  {
    path: "/install/",
    noIndex: true,
    keywords: ["установка pokrov", "apk pokrov", "windows pokrov", "инструкция pokrov", "install help"],
  },
);

export default function InstallPage() {
  const helpHref = buildHelpHref();
  const androidHref = buildArtifactHref(config.androidApkUrl, helpHref);
  const windowsHref = buildArtifactHref(config.windowsExeUrl, helpHref);
  const appleHref = buildHelpHref();
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
              <img src="/pokrov-logo.svg" alt={CANONICAL_PLATFORM_BRAND} className="lp-brand-logo" />
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
                  Служба заботы
                </a>
              </div>
            </nav>
          </div>
        </header>

        <main id="main-content" className="lp-main lp-route-main lp-route-main--install">
          <section className="lp-hero">
            <div className="lp-hero-copy">
              <div className="lp-kicker">{getCopyText("marketing.install.kicker", "Установка POKROV")}</div>
              <p className="lp-overline">Android и Windows ведут к приложению, 5 дням проверки и понятному продолжению.</p>
              <h1>{getCopyText("marketing.install.title", "Скачайте приложение POKROV")}</h1>
              <p className="lp-hero-lead">
                {getCopyText(
                  "marketing.install.subtitle",
                  "Начните с приложения: так проще включить доступ, получить 5 дней проверки и подключиться без лишних шагов. Если нужной платформы пока нет, мы честно покажем текущий статус.",
                )}
              </p>
              <div className="lp-hero-actions">
                <a href="#downloads" className="lp-btn lp-btn--primary">
                  {getCopyText("marketing.install.primary_cta", "Попробовать 5 дней")}
                </a>
                <a href={config.supportTelegramUrl} target="_blank" rel="noreferrer" className="lp-btn lp-btn--ghost">
                  {getCopyText("marketing.install.secondary_cta", "Написать в поддержку")}
                </a>
              </div>
            </div>

            <div className="lp-hero-stage">
              <article className="lp-stage-card lp-stage-card--primary">
                <div className="lp-stage-label">Сначала приложение, потом проверка</div>
                <h2>Скачайте приложение, проверьте 5 дней и продолжайте через ключ доступа.</h2>
                <p>
                  Если файл уже опубликован, скачивание откроется сразу. Если релизный файл ещё готовится,
                  рядом остаются инструкция, кабинет и поддержка.
                </p>
                <ol className="lp-stage-steps">
                  <li>
                    <span>01</span>
                    <div>
                      <strong>Android</strong>
                      <p>Скачайте приложение, а если файла нет, откройте инструкцию и поддержку.</p>
                    </div>
                  </li>
                  <li>
                    <span>02</span>
                    <div>
                      <strong>Windows</strong>
                      <p>Скачайте приложение или откройте короткую инструкцию.</p>
                    </div>
                  </li>
                  <li>
                    <span>03</span>
                    <div>
                      <strong>Поддержка</strong>
                      <p>Если что-то не сходится, кабинет и Telegram остаются рядом без лишних переходов.</p>
                    </div>
                  </li>
                </ol>
              </article>

              <article className="lp-stage-card">
                <div className="lp-stage-label">Если файл ещё готовится</div>
                <p>
                  Откройте инструкцию, кабинет или поддержку. Так вы сохраните следующий шаг без пустого ожидания
                  и сможете вернуться к установке, когда файл будет доступен.
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

          <section id="downloads" className="lp-section">
            <div className="lp-section-head">
              <span>Приложение</span>
              <h2>{getCopyText("marketing.install.downloads.title", "Скачайте приложение или откройте инструкцию")}</h2>
              <p>
                {getCopyText(
                  "marketing.install.downloads.subtitle",
                  "Карточки ведут к актуальному файлу для Android или Windows. Если файл ещё не опубликован, рядом остаётся понятная инструкция.",
                )}
              </p>
            </div>

            <div className="lp-download-grid">
              <article className="lp-platform-card lp-platform-card--featured">
                <div className="lp-stage-label">
                  <span aria-hidden="true">●</span>
                  {getCopyText("marketing.install.android.status", "Android")}
                </div>
                <h3>{getCopyText("marketing.install.android.title", "APK для Android")}</h3>
                <p>
                  {getCopyText(
                    "marketing.install.android.desc",
                    "Скачайте приложение для Android или откройте инструкцию, если релизный файл ещё не опубликован.",
                  )}
                </p>
                {androidHasArtifact ? (
                  <a href={androidHref} target="_blank" rel="noreferrer" className="lp-btn lp-btn--primary">
                    {getCopyText("marketing.download.android.cta", "Скачать приложение")}
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
                  {getCopyText("marketing.install.windows.status", "Windows")}
                </div>
                <h3>{getCopyText("marketing.install.windows.title", "Установщик для Windows")}</h3>
                <p>
                  {getCopyText(
                    "marketing.install.windows.desc",
                    "Скачайте приложение для Windows или откройте инструкцию, если релизный файл ещё не опубликован.",
                  )}
                </p>
                {windowsHasArtifact ? (
                  <a href={windowsHref} target="_blank" rel="noreferrer" className="lp-btn lp-btn--primary">
                    {getCopyText("marketing.download.windows.cta", "Скачать приложение")}
                  </a>
                ) : (
                  <a href={helpHref} className="lp-btn lp-btn--primary">
                    {getCopyText("marketing.install.help_cta", "Открыть инструкцию")}
                  </a>
                )}
              </article>

              <article className="lp-platform-card">
                <div className="lp-stage-label">
                  <span aria-hidden="true">◎</span>
                  {getCopyText("marketing.install.apple.status", "Готовится")}
                </div>
                <h3>{getCopyText("marketing.install.apple.title", "iPhone и Mac")}</h3>
                <p>
                  {getCopyText(
                    "marketing.install.apple.desc",
                    "Apple-линейка пока готовится. Сейчас можно открыть кабинет или поддержку, чтобы уточнить статус.",
                  )}
                </p>
                <a href={appleHref} target="_blank" rel="noreferrer" className="lp-btn lp-btn--ghost">
                  {getCopyText("marketing.download.apple.cta", "Что готовится")}
                </a>
              </article>
            </div>
          </section>

          <section className="lp-section lp-info-band">
            <div className="lp-info-band__grid">
              <article className="lp-info-card">
                <span className="lp-info-card__eyebrow">Если файла пока нет</span>
                <h3>Инструкция остаётся рядом</h3>
                <p>Откройте короткие шаги установки и вернитесь к скачиванию, когда релизный файл будет доступен.</p>
              </article>
              <article className="lp-info-card">
                <span className="lp-info-card__eyebrow">Если нужен доступ</span>
                <h3>Кабинет остаётся точкой продолжения</h3>
                <p>Там можно проверить доступ и вернуться к оплате только тогда, когда это действительно нужно.</p>
              </article>
              <article className="lp-info-card">
                <span className="lp-info-card__eyebrow">Если нужен человек</span>
                <h3>Служба заботы отвечает без лишнего формализма</h3>
                <p>Telegram и почта остаются рядом для вопросов по установке, доступу или восстановлению.</p>
              </article>
            </div>
          </section>

          <section className="lp-section">
            <div className="lp-footer-cta">
              <div className="lp-footer-copy">
                <span>{getCopyText("marketing.install.help_eyebrow", "Если нужна помощь человека")}</span>
                <h2>{getCopyText("marketing.install.help_title", "Кабинет, Telegram и помощь остаются рядом")}</h2>
                <p>
                  {getCopyText(
                    "marketing.install.help_body",
                    "Если файл не находится, откройте кабинет или напишите в поддержку. Мы подскажем следующий шаг по установке, доступу или восстановлению.",
                  )}
                </p>
              </div>
              <div className="lp-footer-actions">
                <a href="#downloads" className="lp-btn lp-btn--primary">
                  {getCopyText("marketing.install.primary_cta", "Попробовать 5 дней")}
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
