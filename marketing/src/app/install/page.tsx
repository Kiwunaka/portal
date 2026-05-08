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
              <img src="/pokrov-logo.svg" alt="" aria-hidden="true" className="lp-brand-logo" />
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
              <div className="lp-kicker">{getCopyText("marketing.install.kicker", "Установка и настройка POKROV")}</div>
              <p className="lp-overline">Спокойная страница помощи: без пустых кнопок, без ложной загрузки и без тупиков.</p>
              <h1>{getCopyText("marketing.install.title", "Установка без тупиков")}</h1>
              <p className="lp-hero-lead">
                {getCopyText(
                  "marketing.install.subtitle",
                  "Бета-сборки выдаются через кабинет или поддержку. Если файл пока не доступен вашему аккаунту, вы всё равно не теряете маршрут.",
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
                <h2>Каждый шаг здесь либо доступен, либо честно объяснён.</h2>
                <p>
                  Если бета-сборка уже доступна вашему аккаунту, кабинет покажет актуальный файл. Если нет, страница остаётся полезной:
                  показывает инструкцию, текущий статус и канал помощи.
                </p>
                <ol className="lp-stage-steps">
                  <li>
                    <span>01</span>
                    <div>
                      <strong>Android</strong>
                      <p>Внутренний APK доступен только для одобренных бета-пользователей через кабинет или поддержку.</p>
                    </div>
                  </li>
                  <li>
                    <span>02</span>
                    <div>
                      <strong>Windows</strong>
                      <p>Бета-сборка может быть неподписанной; предупреждение показывается до установки.</p>
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
                <div className="lp-stage-label">Что делать, если доступа к файлу нет</div>
                <p>
                  Эта страница не притворяется загрузкой. Если релиз ещё не выдан вашему аккаунту, мы показываем кабинет,
                  понятный следующий шаг и помощь человека там, где она действительно нужна.
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
              <span>Бета-сборки</span>
              <h2>{getCopyText("marketing.install.downloads.title", "Откройте кабинет для бета-файлов")}</h2>
              <p>
                {getCopyText(
                  "marketing.install.downloads.subtitle",
                  "Публичная страница не выдаёт прямые загрузки. Если сборка доступна вашему аккаунту, она откроется в кабинете; если нет, рядом остаётся помощь.",
                )}
              </p>
            </div>

            <div className="lp-download-grid">
              <article className="lp-platform-card lp-platform-card--featured">
                <div className="lp-stage-label">
                  <span aria-hidden="true">●</span>
                  {getCopyText("marketing.install.android.status", androidHasArtifact ? "Android beta в кабинете" : "Android beta не выдана")}
                </div>
                <h3>{getCopyText("marketing.install.android.title", "Внутренний APK для Android")}</h3>
                <p>
                  {getCopyText(
                    "marketing.install.android.desc",
                    "Android APK доступен только как внутренняя бета для одобренных пользователей. Публичная публикация остаётся заблокированной до доверенной подписи и физического аудита.",
                  )}
                </p>
                {androidHasArtifact ? (
                  <a href={androidHref} target="_blank" rel="noreferrer" className="lp-btn lp-btn--primary">
                    {getCopyText("marketing.download.android.cta", "Открыть кабинет")}
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
                  {getCopyText("marketing.install.windows.status", windowsHasArtifact ? "Windows beta в кабинете" : "Windows beta не выдана")}
                </div>
                <h3>{getCopyText("marketing.install.windows.title", "Бета-сборка для Windows")}</h3>
                <p>
                  {getCopyText(
                    "marketing.install.windows.desc",
                    "Windows-сборка для беты может быть неподписанной. Перед установкой пользователь должен увидеть предупреждение о неизвестном издателе.",
                  )}
                </p>
                {windowsHasArtifact ? (
                  <a href={windowsHref} target="_blank" rel="noreferrer" className="lp-btn lp-btn--primary">
                    {getCopyText("marketing.download.windows.cta", "Открыть кабинет")}
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
                  {getCopyText("marketing.install.apple.status", "Apple readiness")}
                </div>
                <h3>{getCopyText("marketing.install.apple.title", "iPhone и Mac")}</h3>
                <p>
                  {getCopyText(
                    "marketing.install.apple.desc",
                    "Apple-линейка пока остаётся в readiness-режиме. Здесь нет ложной загрузки, только честная инструкция и актуальный статус.",
                  )}
                </p>
                <a href={appleHref} target="_blank" rel="noreferrer" className="lp-btn lp-btn--ghost">
                  {getCopyText("marketing.download.apple.cta", "Открыть инструкцию")}
                </a>
              </article>
            </div>
          </section>

          <section className="lp-section lp-info-band">
            <div className="lp-info-band__grid">
              <article className="lp-info-card">
                <span className="lp-info-card__eyebrow">Если файла пока нет в кабинете</span>
                <h3>Переходите к инструкции, а не в пустоту</h3>
                <p>Мы оставляем рядом понятный help-сценарий, чтобы вы не теряли следующий шаг и не гадали, что делать дальше.</p>
              </article>
              <article className="lp-info-card">
                <span className="lp-info-card__eyebrow">Если нужен доступ</span>
                <h3>Кабинет остаётся спокойной точкой продолжения</h3>
                <p>Там можно продолжить маршрут, проверить доступ и вернуться к оплате только тогда, когда это действительно нужно.</p>
              </article>
              <article className="lp-info-card">
                <span className="lp-info-card__eyebrow">Если нужен человек</span>
                <h3>Служба заботы отвечает без лишнего формализма</h3>
                <p>Telegram и почта остаются рядом, чтобы быстро закрыть вопрос по установке, доступу или восстановлению.</p>
              </article>
            </div>
          </section>

          <section className="lp-section">
            <div className="lp-footer-cta">
              <div className="lp-footer-copy">
                <span>{getCopyText("marketing.install.help_eyebrow", "Если нужен живой маршрут")}</span>
                <h2>{getCopyText("marketing.install.help_title", "Кабинет, Telegram и помощь остаются рядом")}</h2>
                <p>
                  {getCopyText(
                    "marketing.install.help_body",
                    "Если файл не находится, откройте кабинет или напишите в поддержку. Мы не оставляем вас на пустой странице и не прячем следующий шаг.",
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
