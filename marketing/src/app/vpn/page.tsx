import Link from "next/link";

import JsonLd from "../../components/json-ld";
import { MarketingBrandLogo } from "../../components/marketing-brand-logo";
import { buildMarketingMetadata } from "../../components/marketing-landing";
import {
  buildBreadcrumbJsonLd,
  buildFaqJsonLd,
  buildMarketingUrl,
  MARKETING_CANONICAL_PATHS,
} from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND, getPokrovPublicConfig } from "../../lib/pokrov";

const config = getPokrovPublicConfig(process.env as Record<string, string | undefined>);

const VPN_FAQ = [
  {
    question: "Можно ли скачать VPN бесплатно?",
    answer:
      "Да. В POKROV можно начать с 5 дней бесплатно без карты: установите приложение для Android или Windows, проверьте подключение и только потом решайте, нужен ли платный срок.",
  },
  {
    question: "POKROV подходит, если я ищу лучший ВПН?",
    answer:
      "Мы не обещаем быть лучшими для всех. POKROV стоит попробовать, если вам нужен понятный VPN для Android и Windows: приложение, пробный период, кабинет, Telegram-бонус и поддержка без ручной настройки на первом шаге.",
  },
  {
    question: "Нужно ли вручную настраивать VPN-профиль?",
    answer:
      "В обычном сценарии нет. Пользователь скачивает приложение, запускает бесплатный период и подключается внутри POKROV. Ручные варианты остаются для совместимости и восстановления, когда они действительно нужны.",
  },
  {
    question: "Какие устройства поддерживаются?",
    answer:
      "Текущая публичная бета POKROV рассчитана на Android и Windows. iOS и macOS не входят в публичное обещание этой волны.",
  },
  {
    question: "Это полностью бесплатный VPN навсегда?",
    answer:
      "Нет. Есть бесплатный старт на 5 дней без карты и базовый бесплатный режим после пробного периода. Для регулярного использования предусмотрены платные сроки с понятной оплатой через официальную страницу оплаты.",
  },
];

function buildArticleJsonLd() {
  return {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: "VPN скачать бесплатно: POKROV для Android и Windows",
    inLanguage: "ru-RU",
    dateModified: "2026-06-01",
    author: {
      "@type": "Organization",
      name: CANONICAL_PLATFORM_BRAND,
    },
    publisher: {
      "@type": "Organization",
      name: CANONICAL_PLATFORM_BRAND,
      logo: {
        "@type": "ImageObject",
        url: buildMarketingUrl("/pokrov-logo.svg"),
      },
    },
    mainEntityOfPage: buildMarketingUrl(MARKETING_CANONICAL_PATHS.vpn),
    description:
      "POKROV помогает скачать VPN для Android и Windows, начать с 5 дней бесплатно без карты и проверить подключение до оплаты.",
  };
}

export const metadata = buildMarketingMetadata(
  "VPN скачать бесплатно | POKROV для Android и Windows",
  "POKROV - VPN для Android и Windows с 5 днями бесплатно без карты. Скачайте приложение, проверьте подключение и продлите срок только если все подходит.",
  {
    path: MARKETING_CANONICAL_PATHS.vpn,
    keywords: [
      "vpn",
      "впн",
      "vpn скачать",
      "впн скачать",
      "vpn скачать бесплатно",
      "впн скачать бесплатно",
      "лучший vpn",
      "лучший впн",
      "vpn android",
      "vpn windows",
      "pokrov vpn",
    ],
  },
);

export default function VpnSeoPage() {
  return (
    <>
      <JsonLd
        data={buildBreadcrumbJsonLd([
          { name: CANONICAL_PLATFORM_BRAND, path: MARKETING_CANONICAL_PATHS.home },
          { name: "VPN для Android и Windows", path: MARKETING_CANONICAL_PATHS.vpn },
        ])}
      />
      <JsonLd data={buildArticleJsonLd()} />
      <JsonLd data={buildFaqJsonLd(VPN_FAQ)} />

      <div className="lp-route-shell lp-route-shell--intent lp-route-shell--vpn">
        <header className="lp-nav">
          <div className="lp-nav-shell">
            <Link href="/" className="lp-brand">
              <MarketingBrandLogo className="lp-brand-logo" priority />
              <span>{CANONICAL_PLATFORM_BRAND}</span>
            </Link>
            <nav className="lp-menu" aria-label="Главная навигация">
              <div className="lp-nav-links">
                <Link href="/">Главная</Link>
                <Link href={MARKETING_CANONICAL_PATHS.install}>Скачать</Link>
                <Link href={MARKETING_CANONICAL_PATHS.devices}>Android и Windows</Link>
                <Link href={MARKETING_CANONICAL_PATHS.youtube}>YouTube</Link>
                <Link href={MARKETING_CANONICAL_PATHS.telegram}>Telegram</Link>
              </div>
              <div className="lp-nav-actions">
                <a href={config.webappUrl} target="_blank" rel="noreferrer" className="lp-chip">
                  Кабинет
                </a>
                <a href={config.supportTelegramUrl} target="_blank" rel="noreferrer" className="lp-chip lp-chip--primary">
                  Поддержка
                </a>
              </div>
            </nav>
          </div>
        </header>

        <main id="main-content" className="lp-main lp-route-main">
          <section className="lp-hero">
            <div className="lp-hero-copy">
              <div className="lp-kicker">VPN / ВПН / скачать бесплатно</div>
              <p className="lp-overline">Android и Windows. 5 дней бесплатно. Без карты на старте.</p>
              <h1>POKROV VPN для Android и Windows</h1>
              <p className="lp-hero-lead">
                Скачайте приложение, включите 5 дней бесплатно и проверьте связь на своих устройствах. Без длинной
                ручной настройки, случайных зеркал и оплаты до первого теста.
              </p>
              <div className="lp-hero-actions">
                <Link href={MARKETING_CANONICAL_PATHS.install} className="lp-btn lp-btn--primary">
                  Скачать POKROV
                </Link>
                <Link href={MARKETING_CANONICAL_PATHS.checkout} className="lp-btn lp-btn--ghost">
                  Посмотреть тарифы
                </Link>
              </div>
            </div>

            <div className="lp-hero-stage">
              <article className="lp-stage-card lp-stage-card--primary">
                <div className="lp-stage-label">Короткий путь</div>
                <h2>Сначала тест. Потом решение.</h2>
                <ol className="lp-stage-steps">
                  <li>
                    <span>01</span>
                    <div>
                      <strong>Скачайте приложение</strong>
                      <p>Официальная установка для Android и Windows открывается с сайта, кабинета или поддержки.</p>
                    </div>
                  </li>
                  <li>
                    <span>02</span>
                    <div>
                      <strong>Запустите 5 дней бесплатно</strong>
                      <p>Карта не нужна. Достаточно аккаунта и приложения.</p>
                    </div>
                  </li>
                  <li>
                    <span>03</span>
                    <div>
                      <strong>Проверьте привычные сервисы</strong>
                      <p>YouTube, TikTok, Telegram, браузер, домашний Wi-Fi и мобильную сеть.</p>
                    </div>
                  </li>
                </ol>
              </article>
            </div>
          </section>

          <section className="lp-section lp-longform">
            <div className="lp-section-head">
              <span>Почему POKROV</span>
              <h2>Не просто “скачать ВПН”, а получить понятный рабочий сценарий</h2>
              <p>
                Когда человек ищет “VPN скачать бесплатно”, ему обычно не нужна лекция о протоколах. Ему нужно быстро
                поставить приложение, понять, работает ли связь, и не попасть на мутный файл из случайного архива.
              </p>
            </div>

            <div className="lp-longform-grid">
              <article className="lp-longform-article">
                <h2>POKROV начинается с приложения, а не с инструкции на полчаса</h2>
                <p>
                  Многие VPN-страницы обещают “лучший ВПН”, “анонимность без ограничений” и “бесплатно навсегда”.
                  На практике пользователю все равно приходится искать правильный файл, разбираться с профилем, читать
                  чужие советы и угадывать, что делать, если подключение не поднялось.
                </p>
                <p>
                  POKROV держит первый шаг проще: приложение для Android или Windows, бесплатный период на 5 дней,
                  кабинет для срока и устройств, поддержка в Telegram. Это не громкое обещание для всех случаев жизни,
                  а нормальный способ проверить VPN на своем устройстве до оплаты.
                </p>

                <h2>“Лучший VPN” - это тот, который работает именно у вас</h2>
                <p>
                  В поиске слово “лучший” понятно: хочется не сравнивать десятки сервисов, а сразу выбрать надежный
                  вариант. Но честнее смотреть на признаки, которые можно проверить: есть ли официальный источник
                  скачивания, понятен ли бесплатный старт, есть ли поддержка, не заставляют ли платить до первого теста.
                </p>
                <p>
                  Поэтому POKROV не строит страницу вокруг крика “мы лучшие”. Мы даем сценарий проверки: скачать VPN,
                  включить 5 дней бесплатно, открыть нужные сервисы, посмотреть поведение на Android или Windows, а уже
                  потом принимать решение о продлении.
                </p>

                <h2>Чем POKROV отличается от типичной бесплатной VPN-страницы</h2>
                <p>
                  Здесь нет обещания “бесплатно навсегда без условий”. Бесплатный старт нужен, чтобы спокойно проверить
                  качество связи. После пробного периода можно выбрать платный срок или остаться на базовом режиме с
                  месячным лимитом.
                </p>
                <p>
                  Мы используем обычный язык, которым люди ищут приложение: “VPN”, “ВПН”, “скачать” и “бесплатно”.
                  Но за этими словами должен быть понятный ответ: где скачать, что именно бесплатно, какие устройства
                  поддерживаются и когда писать в поддержку.
                </p>

                <h2>Как скачать VPN безопасно</h2>
                <p>
                  Скачивайте POKROV только через официальные поверхности: сайт, кабинет, основной бот или поддержку.
                  Не используйте случайные APK, пересланные архивы и “обновленные версии” из подборок. Для VPN это
                  особенно важно: приложение получает сетевой доступ, поэтому источник файла должен быть понятным.
                </p>
                <p>
                  Текущая публичная бета рассчитана на Android и Windows. Для Windows файл может показать предупреждение
                  о неизвестном издателе. Скачивайте POKROV только через официальный сайт, кабинет, бот или поддержку.
                </p>

                <h2>Что проверить в первые 5 дней</h2>
                <p>
                  Проверьте не только сам факт подключения, а свои обычные сценарии: браузер, YouTube, TikTok, Telegram,
                  работу на домашнем Wi-Fi и мобильной сети, поведение после перезапуска устройства. Если что-то не
                  работает, напишите в поддержку до оплаты, а не пытайтесь менять настройки вслепую.
                </p>
                <p>
                  Если POKROV подходит для повседневных задач, продление идет через тот же аккаунт, кабинет и официальный
                  раздел оплаты. Telegram-бонус дает +10 дней за подписку на канал, а платные планы могут включать несколько
                  устройств в зависимости от выбранного срока.
                </p>
              </article>

              <aside className="lp-longform-aside" aria-label="Короткая сводка">
                <div className="lp-info-card">
                  <span className="lp-info-card__eyebrow">На старте</span>
                  <h3>5 дней бесплатно</h3>
                  <p>Без карты. Сначала установка и проверка, потом решение о продлении.</p>
                </div>
                <div className="lp-info-card">
                  <span className="lp-info-card__eyebrow">Устройства</span>
                  <h3>Android и Windows</h3>
                  <p>Публичная бета сфокусирована на двух основных платформах этой волны.</p>
                </div>
                <div className="lp-info-card">
                  <span className="lp-info-card__eyebrow">Где скачать</span>
                  <h3>Только официальный путь</h3>
                  <p>Откройте страницу установки и проверьте доступность файла для аккаунта.</p>
                  <Link href={MARKETING_CANONICAL_PATHS.install} className="lp-btn lp-btn--primary">
                    Открыть установку
                  </Link>
                </div>
                <div className="lp-info-card">
                  <span className="lp-info-card__eyebrow">Сценарии</span>
                  <h3>YouTube, TikTok, Telegram</h3>
                  <p>Для популярных задач есть отдельные страницы с более точным описанием.</p>
                  <div className="lp-stage-links">
                    <Link href={MARKETING_CANONICAL_PATHS.youtube}>YouTube</Link>
                    <Link href={MARKETING_CANONICAL_PATHS.tiktok}>TikTok</Link>
                    <Link href={MARKETING_CANONICAL_PATHS.telegram}>Telegram</Link>
                  </div>
                </div>
              </aside>
            </div>
          </section>

          <section className="lp-section">
            <div className="lp-section-head">
              <span>FAQ</span>
              <h2>Короткие ответы по VPN и POKROV</h2>
              <p>Самое важное перед установкой: бесплатный старт, устройства, ручная настройка и честные ограничения.</p>
            </div>
            <div className="lp-faq-list">
              {VPN_FAQ.map((item) => (
                <details key={item.question} className="lp-faq-item">
                  <summary className="lp-faq-q">
                    <span>{item.question}</span>
                    <span className="lp-faq-icon" aria-hidden="true">
                      +
                    </span>
                  </summary>
                  <p className="lp-faq-a">{item.answer}</p>
                </details>
              ))}
            </div>
          </section>

          <section className="lp-section">
            <div className="lp-footer-cta">
              <div className="lp-footer-copy">
                <span>Следующий шаг</span>
                <h2>Скачайте POKROV и проверьте VPN бесплатно 5 дней.</h2>
                <p>
                  Начните с установки. Если уже проверили связь, откройте тарифы или кабинет для продления.
                </p>
              </div>
              <div className="lp-footer-actions">
                <Link href={MARKETING_CANONICAL_PATHS.install} className="lp-btn lp-btn--primary">
                  Скачать POKROV
                </Link>
                <Link href={MARKETING_CANONICAL_PATHS.checkout} className="lp-btn lp-btn--ghost">
                  Тарифы
                </Link>
                <a href={config.webappUrl} target="_blank" rel="noreferrer" className="lp-btn lp-btn--ghost">
                  Кабинет
                </a>
              </div>
            </div>
          </section>
        </main>
      </div>
    </>
  );
}
