import type { MetadataRoute } from "next";

import {
  CANONICAL_GITHUB_RELEASES_URL,
  CANONICAL_SUPPORT_BOT_URL,
  CANONICAL_WEBAPP_URL,
} from "./pokrov";

export const SEO_LAST_REVIEWED_DATE = "2026-07-22";

export const TELEGRAM_START_PROMISE =
  "До 10 дней на старте: 5 дней бесплатно в приложении и ещё 5 дней после привязки Telegram и подтверждения подписки на канал.";

export const SEO_PAGE_PATHS = {
  android: "/android/",
  windows: "/windows/",
  installAndroid: "/install/android/",
  installWindows: "/install/windows/",
  trialNoCard: "/trial/no-card/",
  billingNoAutopay: "/billing/no-autosubscription/",
  trustGithubReleases: "/trust/github-releases/",
  bestVpn: "/best-vpn/",
  compareFreeVpn: "/compare/free-vpn/",
  supportInstall: "/support/install/",
} as const;

export type SeoPageCluster =
  | "vpn"
  | "platform"
  | "install"
  | "trial"
  | "billing"
  | "trust"
  | "compare"
  | "support"
  | "scenario";

export type SeoPageKind = "intent" | "install" | "trust" | "compare";

export type SeoLink = {
  external?: boolean;
  href: string;
  label: string;
};

export type SeoFaqItem = {
  answer: string;
  question: string;
};

export type SeoCard = {
  body: string;
  eyebrow: string;
  title: string;
};

export type SeoSection = {
  body: string;
  bullets?: string[];
  title: string;
};

export type SeoStep = {
  name: string;
  text: string;
};

export type SeoComparisonRow = {
  criterion: string;
  freeVpn: string;
  pokrov: string;
};

export type SeoPage = {
  answer: string;
  breadcrumbName: string;
  cards: SeoCard[];
  changeFrequency: NonNullable<MetadataRoute.Sitemap[number]["changeFrequency"]>;
  cluster: SeoPageCluster;
  comparisonRows?: SeoComparisonRow[];
  description: string;
  faq: SeoFaqItem[];
  h1: string;
  heroKicker: string;
  kind: SeoPageKind;
  lastReviewed: string;
  path: string;
  primaryCta?: SeoLink;
  priority: number;
  related: SeoLink[];
  secondaryCta?: SeoLink;
  sections: SeoSection[];
  steps?: SeoStep[];
  title: string;
};

const installCta: SeoLink = { href: "/install/", label: "Скачать POKROV" };
const cabinetCta: SeoLink = { external: true, href: CANONICAL_WEBAPP_URL, label: "Открыть кабинет" };
const checkoutCta: SeoLink = { href: "/checkout/", label: "Посмотреть тарифы" };
const supportCta: SeoLink = {
  external: true,
  href: CANONICAL_SUPPORT_BOT_URL,
  label: "Написать в поддержку",
};
const releasesCta: SeoLink = {
  external: true,
  href: CANONICAL_GITHUB_RELEASES_URL,
  label: "GitHub Releases",
};

const platformRelated: SeoLink[] = [
  { href: SEO_PAGE_PATHS.android, label: "Android" },
  { href: SEO_PAGE_PATHS.windows, label: "Windows" },
  { href: "/install/", label: "Установка" },
  { href: SEO_PAGE_PATHS.trialNoCard, label: "5 дней без карты" },
  { href: SEO_PAGE_PATHS.trustGithubReleases, label: "Файлы на GitHub" },
];

const intentRelated: SeoLink[] = [
  { href: "/vpn/", label: "VPN для Android и Windows" },
  { href: SEO_PAGE_PATHS.bestVpn, label: "Лучший VPN" },
  { href: SEO_PAGE_PATHS.android, label: "Android" },
  { href: SEO_PAGE_PATHS.windows, label: "Windows" },
  { href: "/youtube/", label: "YouTube" },
  { href: "/tiktok/", label: "TikTok" },
  { href: "/telegram/", label: "Telegram-бонус" },
  { href: SEO_PAGE_PATHS.compareFreeVpn, label: "Бесплатный VPN" },
];

function withDefaults(page: Omit<SeoPage, "lastReviewed"> & { lastReviewed?: string }): SeoPage {
  return {
    ...page,
    lastReviewed: page.lastReviewed || SEO_LAST_REVIEWED_DATE,
  };
}

export const SEO_INDEXABLE_PAGES: SeoPage[] = [
  withDefaults({
    answer:
      "POKROV — VPN для быстрого старта на Android и Windows: 5 дней бесплатно без карты, официальные файлы, подключение одной кнопкой, кабинет и Telegram-поддержка. Сначала проверяете связь на своём устройстве, затем решаете, продлевать ли доступ.",
    breadcrumbName: "VPN для Android и Windows",
    cards: [
      {
        eyebrow: "Старт",
        title: "5 дней без карты",
        body: "Сначала проверка на своём устройстве. Оплата появляется только когда вы решаете продлить срок.",
      },
      {
        eyebrow: "Платформы",
        title: "Android и Windows",
        body: "Публичная версия сфокусирована на Android и Windows: для обеих платформ есть приложение, установка и поддержка.",
      },
      {
        eyebrow: "Путь",
        title: "Приложение вместо профилей",
        body: "Основной сценарий: скачать, войти, нажать кнопку. Ручные настройки оставлены для восстановления.",
      },
    ],
    changeFrequency: "weekly",
    cluster: "vpn",
    description:
      "POKROV: VPN для Android и Windows с 5 днями бесплатно без карты. Скачайте приложение, проверьте подключение и продлите срок без автосписаний.",
    faq: [
      {
        question: "Можно ли скачать VPN бесплатно?",
        answer:
          "Да. В POKROV есть 5 дней бесплатно без карты: установите приложение для Android или Windows, проверьте подключение и только потом решайте, нужен ли платный срок.",
      },
      {
        question: "POKROV подходит, если я ищу лучший ВПН?",
        answer:
          "Да, если вам нужен лучший VPN для простого старта на Android или Windows. POKROV объединяет приложение, 5 дней бесплатно без карты, официальный источник файлов, разовую оплату без автосписаний и поддержку.",
      },
      {
        question: "Какие устройства поддерживаются?",
        answer:
          "Текущая публичная версия POKROV рассчитана на Android и Windows. Для обеих платформ доступны официальные файлы и отдельные инструкции.",
      },
    ],
    h1: "Скачать VPN для Android и Windows: POKROV",
    heroKicker: "VPN скачать бесплатно · Android · Windows",
    kind: "intent",
    path: "/vpn/",
    primaryCta: installCta,
    priority: 0.88,
    related: platformRelated,
    secondaryCta: checkoutCta,
    sections: [
      {
        title: "POKROV начинается с приложения",
        body:
          "Не нужно начинать с профилей, ключей и чужих инструкций на полчаса. Сначала приложение, аккаунт и кнопка подключения. Уже потом, если POKROV подходит, выбираете срок.",
      },
      {
        title: "Что проверить в первые 5 дней",
        body:
          "Откройте свои обычные сервисы: браузер, YouTube, TikTok, Telegram, рабочие сайты. Проверьте домашний Wi-Fi и мобильную сеть. Если что-то ведёт себя странно, лучше написать в поддержку до оплаты.",
      },
      {
        title: "Где скачивать файл",
        body:
          "Используйте официальный сайт, кабинет, бота или поддержку. Не ставьте APK и EXE из случайных архивов: приложение получает сетевой доступ, источник файла тут не мелочь.",
      },
    ],
    title: "VPN скачать бесплатно для Android и Windows | POKROV",
  }),
  withDefaults({
    answer:
      "POKROV на Android ставится через APK из официального кабинета. После установки откройте приложение и запустите 5 дней бесплатно без карты. Это хороший способ проверить VPN на телефоне до оплаты, без профилей и ручного ввода настроек.",
    breadcrumbName: "Android",
    cards: [
      {
        eyebrow: "APK",
        title: "Файл выдаёт кабинет",
        body: "Кабинет показывает актуальный APK для вашего аккаунта, а не случайную сборку из подборки.",
      },
      {
        eyebrow: "Без карты",
        title: "5 дней на проверку",
        body: "Можно открыть привычные приложения и понять, подходит ли POKROV именно вашему телефону.",
      },
      {
        eyebrow: "Поддержка",
        title: "Если Android спорит",
        body: "Иногда система просит разрешить установку из источника. Это нормальный шаг для APK вне магазина.",
      },
    ],
    changeFrequency: "weekly",
    cluster: "platform",
    description:
      "VPN для Android от POKROV: APK через официальный кабинет, 5 дней бесплатно без карты, одна кнопка подключения и поддержка в Telegram.",
    faq: [
      {
        question: "Как скачать VPN на Android?",
        answer:
          "Откройте страницу установки POKROV, перейдите в кабинет и скачайте APK. Для большинства современных телефонов подходит arm64-файл; для старых устройств в кабинете есть legacy-вариант.",
      },
      {
        question: "Нужна ли банковская карта для старта?",
        answer:
          "Нет. Бесплатный период на 5 дней запускается в приложении, карту вводить не нужно.",
      },
      {
        question: "POKROV есть в магазине приложений?",
        answer:
          "Нет публичного обещания про магазин в этой бета-волне. Android-версия распространяется вне магазина через официальный кабинет и GitHub Releases.",
      },
    ],
    h1: "VPN для Android: скачать POKROV и проверить 5 дней бесплатно",
    heroKicker: "Android VPN · APK · без карты",
    kind: "intent",
    path: SEO_PAGE_PATHS.android,
    primaryCta: { href: SEO_PAGE_PATHS.installAndroid, label: "Инструкция для Android" },
    priority: 0.86,
    related: [
      { href: SEO_PAGE_PATHS.installAndroid, label: "Установка APK" },
      { href: "/mobile/", label: "Быстрый старт на телефоне" },
      { href: SEO_PAGE_PATHS.trialNoCard, label: "5 дней без карты" },
      { href: SEO_PAGE_PATHS.trustGithubReleases, label: "Проверка источника" },
    ],
    secondaryCta: cabinetCta,
    sections: [
      {
        title: "Что происходит после скачивания",
        body:
          "Android спросит разрешение на установку из выбранного источника. Дальше всё проще: открыть POKROV, войти в аккаунт, нажать подключение. Профиль вручную вводить не нужно.",
      },
      {
        title: "Какие сценарии стоит проверить",
        body:
          "Запустите YouTube, TikTok, Telegram, браузер, рабочие сайты. Потом переключитесь с Wi-Fi на мобильную сеть. Если связь меняется, поддержка быстрее разберёт проблему по конкретному примеру.",
      },
    ],
    title: "VPN для Android скачать бесплатно | POKROV APK",
  }),
  withDefaults({
    answer:
      "POKROV для Windows скачивается через официальный кабинет. Установщик может вызвать предупреждение SmartScreen, потому что публичная бета распространяется вне магазина и без подписи издателя. После запуска вы проверяете VPN 5 дней бесплатно, карту вводить не нужно.",
    breadcrumbName: "Windows",
    cards: [
      {
        eyebrow: "EXE",
        title: "Официальный установщик",
        body: "Скачивайте файл через кабинет или официальные ссылки, не через пересланные архивы.",
      },
      {
        eyebrow: "SmartScreen",
        title: "Предупреждение возможно",
        body: "Для неподписанного приложения вне магазина это ожидаемое поведение Windows.",
      },
      {
        eyebrow: "Проверка",
        title: "5 дней без оплаты",
        body: "Проверьте браузер, видео, мессенджеры и рабочие задачи до выбора тарифа.",
      },
    ],
    changeFrequency: "weekly",
    cluster: "platform",
    description:
      "VPN для Windows от POKROV: официальный EXE через кабинет, честная заметка про SmartScreen, 5 дней бесплатно без карты.",
    faq: [
      {
        question: "Как скачать VPN для Windows?",
        answer:
          "Откройте страницу установки, перейдите в кабинет и скачайте EXE-файл. Это официальный путь для текущей публичной беты POKROV.",
      },
      {
        question: "Почему Windows показывает SmartScreen?",
        answer:
          "Приложение пока распространяется вне магазина и без подписи издателя. SmartScreen предупреждает о таком файле, даже если он получен из официального источника.",
      },
      {
        question: "Можно ли сначала попробовать без оплаты?",
        answer:
          "Да. В приложении доступно 5 дней бесплатно без карты. Этого хватает, чтобы проверить поведение на своём компьютере.",
      },
    ],
    h1: "VPN для Windows: скачать POKROV и проверить без карты",
    heroKicker: "Windows VPN · EXE · SmartScreen",
    kind: "intent",
    path: SEO_PAGE_PATHS.windows,
    primaryCta: { href: SEO_PAGE_PATHS.installWindows, label: "Инструкция для Windows" },
    priority: 0.85,
    related: [
      { href: SEO_PAGE_PATHS.installWindows, label: "Установка Windows" },
      { href: "/devices/", label: "Устройства" },
      { href: SEO_PAGE_PATHS.trialNoCard, label: "5 дней без карты" },
      { href: SEO_PAGE_PATHS.trustGithubReleases, label: "Файлы на GitHub" },
    ],
    secondaryCta: cabinetCta,
    sections: [
      {
        title: "Как пройти первый запуск",
        body:
          "Скачайте установщик из кабинета, запустите его, при предупреждении SmartScreen нажмите «Подробнее» и продолжите. Потом откройте POKROV и включите подключение.",
      },
      {
        title: "Что проверить на Windows",
        body:
          "Проверьте браузер, YouTube, TikTok, Telegram Desktop и те программы, которыми вы пользуетесь каждый день. Если Windows просит разрешение на сетевой доступ, разрешите его для POKROV.",
      },
    ],
    title: "VPN для Windows скачать бесплатно | POKROV",
  }),
  withDefaults({
    answer:
      "Чтобы установить POKROV на Android, скачайте APK из кабинета, разрешите установку из этого источника и откройте приложение. Бесплатные 5 дней запускаются внутри POKROV, банковская карта на старте не нужна.",
    breadcrumbName: "Установка Android",
    cards: [
      {
        eyebrow: "Шаг 1",
        title: "Откройте кабинет",
        body: "Кабинет выдаёт актуальный APK для аккаунта и показывает legacy-файл, если телефон старый.",
      },
      {
        eyebrow: "Шаг 2",
        title: "Разрешите установку",
        body: "Android отдельно спросит разрешение для APK вне магазина. Это системный экран, не обходной трюк.",
      },
      {
        eyebrow: "Шаг 3",
        title: "Запустите POKROV",
        body: "Войдите в аккаунт, нажмите подключение и проверьте свои обычные приложения.",
      },
    ],
    changeFrequency: "weekly",
    cluster: "install",
    description:
      "Как установить POKROV на Android: скачать APK из кабинета, разрешить установку, включить VPN и проверить 5 дней бесплатно.",
    faq: [
      {
        question: "Какой APK нужен для Android?",
        answer:
          "Обычно подходит arm64-файл. Если устройство старое и установка не проходит, возьмите legacy-версию в кабинете.",
      },
      {
        question: "Это безопаснее, чем искать APK в интернете?",
        answer:
          "Да, потому что официальный кабинет ведёт к актуальному файлу POKROV. Случайные архивы и зеркала лучше не использовать.",
      },
      {
        question: "Куда писать, если APK не ставится?",
        answer:
          "Напишите в Telegram-поддержку и укажите модель телефона, версию Android и какой файл пробовали установить.",
      },
    ],
    h1: "Как установить POKROV VPN на Android",
    heroKicker: "APK · Android · инструкция",
    kind: "install",
    path: SEO_PAGE_PATHS.installAndroid,
    primaryCta: cabinetCta,
    priority: 0.8,
    related: [
      { href: SEO_PAGE_PATHS.android, label: "VPN для Android" },
      { href: "/install/", label: "Общая установка" },
      { href: SEO_PAGE_PATHS.supportInstall, label: "Помощь с установкой" },
      { href: SEO_PAGE_PATHS.trustGithubReleases, label: "GitHub Releases" },
    ],
    secondaryCta: supportCta,
    sections: [
      {
        title: "Перед установкой",
        body:
          "Проверьте, что файл скачан из кабинета POKROV. Если браузер просит подтвердить загрузку APK, это обычная защита Android от файлов вне магазина.",
      },
      {
        title: "После установки",
        body:
          "Откройте приложение, войдите в аккаунт и нажмите подключение. Если Android показывает системный запрос на VPN-подключение, подтвердите его: без этого приложение не сможет поднять туннель.",
      },
    ],
    steps: [
      { name: "Скачать APK", text: "Откройте кабинет POKROV и скачайте Android-файл для своего аккаунта." },
      { name: "Разрешить источник", text: "В системном окне Android разрешите установку из выбранного источника." },
      { name: "Открыть приложение", text: "Запустите POKROV, войдите и нажмите подключение." },
      { name: "Проверить сценарии", text: "Откройте YouTube, TikTok, Telegram и обычный браузер." },
    ],
    title: "Как установить POKROV VPN на Android | APK инструкция",
  }),
  withDefaults({
    answer:
      "Чтобы установить POKROV на Windows, скачайте EXE из кабинета, запустите установщик и пройдите предупреждение SmartScreen, если оно появится. Это ожидаемо для публичной беты вне магазина. После запуска можно проверить VPN 5 дней бесплатно.",
    breadcrumbName: "Установка Windows",
    cards: [
      {
        eyebrow: "Файл",
        title: "EXE из кабинета",
        body: "Кабинет ведёт к актуальному установщику. Не берите файл из чужих архивов.",
      },
      {
        eyebrow: "SmartScreen",
        title: "Нажмите «Подробнее»",
        body: "Если источник официальный, можно продолжить установку. Подписи издателя пока нет.",
      },
      {
        eyebrow: "Запуск",
        title: "Проверьте без оплаты",
        body: "5 дней бесплатного старта нужны ровно для этого: включить и посмотреть на своём ПК.",
      },
    ],
    changeFrequency: "weekly",
    cluster: "install",
    description:
      "Как установить POKROV VPN на Windows: скачать EXE из кабинета, пройти SmartScreen и проверить подключение 5 дней бесплатно.",
    faq: [
      {
        question: "Что делать, если SmartScreen блокирует установщик?",
        answer:
          "Нажмите «Подробнее», затем «Выполнить в любом случае», если файл скачан через официальный кабинет POKROV.",
      },
      {
        question: "Почему POKROV не подписан как издатель?",
        answer:
          "Текущая публичная бета распространяется вне магазина и без доверенной подписи издателя для Windows. Мы не называем это готовым production-состоянием.",
      },
      {
        question: "Куда писать при ошибке установки?",
        answer:
          "В Telegram-поддержку. Пришлите текст ошибки, версию Windows и откуда скачивали установщик.",
      },
    ],
    h1: "Как установить POKROV VPN на Windows",
    heroKicker: "EXE · Windows · SmartScreen",
    kind: "install",
    path: SEO_PAGE_PATHS.installWindows,
    primaryCta: cabinetCta,
    priority: 0.79,
    related: [
      { href: SEO_PAGE_PATHS.windows, label: "VPN для Windows" },
      { href: "/install/", label: "Общая установка" },
      { href: SEO_PAGE_PATHS.supportInstall, label: "Помощь с установкой" },
      { href: SEO_PAGE_PATHS.trustGithubReleases, label: "GitHub Releases" },
    ],
    secondaryCta: supportCta,
    sections: [
      {
        title: "Почему появляется предупреждение",
        body:
          "Windows осторожно относится к приложениям вне магазина, особенно без подписи издателя. Это не знак, что файл поддельный. Главный вопрос другой: откуда вы его скачали.",
      },
      {
        title: "После установки",
        body:
          "Откройте POKROV, войдите в аккаунт и включите подключение. Проверьте браузер, видео, мессенджеры и рабочие программы до оплаты.",
      },
    ],
    steps: [
      { name: "Скачать EXE", text: "Откройте кабинет POKROV и скачайте установщик для Windows." },
      { name: "Запустить файл", text: "Если SmartScreen сработал, откройте «Подробнее» и продолжите запуск." },
      { name: "Войти в приложение", text: "Запустите POKROV и войдите в свой аккаунт." },
      { name: "Проверить связь", text: "Включите подключение и проверьте свои обычные сайты и приложения." },
    ],
    title: "Как установить POKROV VPN на Windows | SmartScreen",
  }),
  withDefaults({
    answer:
      "POKROV даёт 5 дней бесплатного старта без банковской карты. Установите приложение на Android или Windows, включите подключение и проверьте свои сценарии. Если подходит, продление оплачивается отдельно, без автосписаний.",
    breadcrumbName: "5 дней без карты",
    cards: [
      {
        eyebrow: "0 ₽",
        title: "Карта не нужна",
        body: "Бесплатный старт запускается в приложении. Платёжные данные на первом шаге не просим.",
      },
      {
        eyebrow: "5 дней",
        title: "Проверка в реальности",
        body: "Не по скриншоту и не по обещаниям. Открываете то, чем пользуетесь каждый день.",
      },
      {
        eyebrow: "Дальше",
        title: "Решаете сами",
        body: "Можно выбрать платный срок или остаться на базовом режиме после пробного периода.",
      },
    ],
    changeFrequency: "weekly",
    cluster: "trial",
    description:
      "VPN бесплатно на 5 дней без карты: установите POKROV на Android или Windows, проверьте подключение и продлите только при необходимости.",
    faq: [
      {
        question: "Что входит в 5 дней бесплатно?",
        answer:
          "Бесплатный старт нужен для проверки POKROV на Android или Windows. Вы ставите приложение, включаете подключение и тестируете свои обычные сервисы.",
      },
      {
        question: "Нужно ли отменять подписку?",
        answer:
          "Нет. На старте нет банковской карты и автосписаний. После бесплатного периода вы сами выбираете, продлевать доступ или нет.",
      },
      {
        question: "Можно ли получить ещё дни?",
        answer: TELEGRAM_START_PROMISE,
      },
    ],
    h1: "VPN бесплатно на 5 дней без карты",
    heroKicker: "Trial · no card · Android и Windows",
    kind: "intent",
    path: SEO_PAGE_PATHS.trialNoCard,
    primaryCta: installCta,
    priority: 0.82,
    related: [
      { href: "/telegram/", label: "Ещё 5 дней через Telegram" },
      { href: SEO_PAGE_PATHS.billingNoAutopay, label: "Без автосписаний" },
      { href: SEO_PAGE_PATHS.android, label: "Android" },
      { href: SEO_PAGE_PATHS.windows, label: "Windows" },
    ],
    secondaryCta: checkoutCta,
    sections: [
      {
        title: "Что проверять в trial",
        body:
          "Не ограничивайтесь одной вкладкой. Проверьте видео, мессенджеры, рабочие сайты, домашний Wi-Fi и мобильную сеть. Trial нужен, чтобы увидеть свою картину, а не усреднённый рекламный ответ.",
      },
      {
        title: "Что будет после 5 дней",
        body:
          "После бесплатного старта вы видите доступные варианты продления. Оплата разовая: выбираете срок, получаете доступ на этот срок, без тихого продления.",
      },
    ],
    title: "VPN бесплатно на 5 дней без карты | POKROV",
  }),
  withDefaults({
    answer:
      "POKROV использует разовую оплату за выбранный срок. Автосписаний нет: вы не привязываете подписку, которая продлевается сама. Цена, срок и лимит устройств видны до оплаты, а бесплатный старт доступен без карты.",
    breadcrumbName: "Без автосписаний",
    cards: [
      {
        eyebrow: "Оплата",
        title: "Заплатили за срок",
        body: "Доступ выдаётся на выбранные дни. Дальше продление только по вашему действию.",
      },
      {
        eyebrow: "Проверка",
        title: "Сначала 5 дней",
        body: "До оплаты можно проверить POKROV на Android или Windows без банковской карты.",
      },
      {
        eyebrow: "Прозрачно",
        title: "Цена видна заранее",
        body: "План, сумма и лимит устройств показаны до перехода к оплате.",
      },
    ],
    changeFrequency: "weekly",
    cluster: "billing",
    description:
      "POKROV без автосписаний: разовая оплата за выбранный срок, 5 дней бесплатно без карты и понятные тарифы до оплаты.",
    faq: [
      {
        question: "POKROV списывает деньги автоматически?",
        answer:
          "Нет. Публичный сценарий оплаты работает как продление на выбранный срок. Автоматического списания после окончания срока нет.",
      },
      {
        question: "Когда я вижу цену?",
        answer:
          "До оплаты. Страница тарифов показывает сумму, срок и лимит устройств по каждому плану.",
      },
      {
        question: "Можно ли сначала попробовать?",
        answer:
          "Да. Установите приложение и запустите 5 дней бесплатно без карты. Это отдельный шаг до платного продления.",
      },
    ],
    h1: "VPN без автосписаний: оплата только за выбранный срок",
    heroKicker: "Разовая оплата · без подписки",
    kind: "intent",
    path: SEO_PAGE_PATHS.billingNoAutopay,
    primaryCta: checkoutCta,
    priority: 0.78,
    related: [
      { href: SEO_PAGE_PATHS.trialNoCard, label: "5 дней без карты" },
      { href: "/checkout/", label: "Тарифы" },
      { href: "/telegram/", label: "Telegram-бонус" },
      { href: SEO_PAGE_PATHS.supportInstall, label: "Поддержка" },
    ],
    secondaryCta: installCta,
    sections: [
      {
        title: "Почему это важно",
        body:
          "У VPN-сервисов часто пугает не цена, а мелкий шрифт: карта уже привязана, продление ушло само, отмена спрятана. В POKROV основной публичный путь проще: оплатили срок, пользуетесь срок.",
      },
      {
        title: "Как устроен старт",
        body:
          "Сначала приложение и бесплатные 5 дней. Потом, если всё подходит, выбираете план. Стартовый вариант на 30 дней стоит от 99 ₽ и рассчитан на аккуратную проверку после trial.",
      },
    ],
    title: "VPN без автосписаний | POKROV",
  }),
  withDefaults({
    answer:
      "POKROV публикует публичные APK и Windows-файлы через GitHub Releases. Пользователю это даёт понятный источник скачивания, историю релизов и checksums для сверки. Основной путь всё равно идёт через кабинет, чтобы получить актуальный файл для аккаунта.",
    breadcrumbName: "GitHub Releases",
    cards: [
      {
        eyebrow: "Источник",
        title: "Публичные релизы",
        body: "Файлы лежат в release-only репозитории GitHub, а сайт и кабинет ведут к актуальному пути скачивания.",
      },
      {
        eyebrow: "Проверка",
        title: "Checksums рядом",
        body: "Контрольные суммы помогают сверить файл, если вы скачиваете релиз вручную.",
      },
      {
        eyebrow: "Без зеркал",
        title: "Не нужен чужой архив",
        body: "APK и EXE лучше брать из официального кабинета или GitHub Releases, а не из подборок.",
      },
    ],
    changeFrequency: "weekly",
    cluster: "trust",
    description:
      "POKROV на GitHub Releases: официальные APK и Windows-файлы, checksums для сверки и понятный источник скачивания.",
    faq: [
      {
        question: "Зачем POKROV использует GitHub Releases?",
        answer:
          "Так публичные файлы доступны по понятному источнику: релиз, версия, checksums и история публикаций находятся в одном месте.",
      },
      {
        question: "Нужно ли скачивать только с GitHub?",
        answer:
          "Нет. Обычный путь идёт через кабинет, он выдаёт нужный файл для аккаунта. GitHub Releases полезен как публичный источник релизных файлов.",
      },
      {
        question: "Что такое checksum?",
        answer:
          "Это контрольная сумма файла. Её можно использовать для сверки, что скачанный APK или EXE совпадает с опубликованным релизом.",
      },
    ],
    h1: "POKROV на GitHub Releases: APK, EXE и checksums",
    heroKicker: "GitHub · релизы · checksums",
    kind: "trust",
    path: SEO_PAGE_PATHS.trustGithubReleases,
    primaryCta: releasesCta,
    priority: 0.76,
    related: [
      { href: "/install/", label: "Установка" },
      { href: SEO_PAGE_PATHS.installAndroid, label: "Android APK" },
      { href: SEO_PAGE_PATHS.installWindows, label: "Windows EXE" },
      { href: SEO_PAGE_PATHS.supportInstall, label: "Помощь" },
    ],
    secondaryCta: installCta,
    sections: [
      {
        title: "Что это даёт обычному пользователю",
        body:
          "GitHub не делает приложение «магически безопасным». Зато он убирает мутность: есть публичный релиз, файлы, checksums и история. Для beta-доставки это понятнее, чем файлы без происхождения.",
      },
      {
        title: "Как скачать без риска перепутать файл",
        body:
          "Если вы не хотите вручную сверять версии, идите через кабинет. Он покажет актуальную загрузку. Если скачиваете с GitHub, проверяйте название релиза и не берите файлы из комментариев или пересланных архивов.",
      },
    ],
    title: "POKROV GitHub Releases | APK, EXE и checksums",
  }),
  withDefaults({
    answer:
      `POKROV — лучший VPN для простого старта на Android и Windows: официальные файлы, подключение одной кнопкой, разовая оплата без автосписаний и до 5 устройств на основных тарифах. ${TELEGRAM_START_PROMISE}`,
    breadcrumbName: "Лучший VPN",
    cards: [
      {
        eyebrow: "Старт",
        title: "5 дней бесплатно без карты",
        body: "Установите POKROV и проверьте свои сайты, видео и приложения до первой оплаты.",
      },
      {
        eyebrow: "Приложения",
        title: "Android и Windows",
        body: "Один понятный сценарий: официальный файл, вход в аккаунт и кнопка подключения без ручных профилей на старте.",
      },
      {
        eyebrow: "Оплата",
        title: "Без автосписаний",
        body: "Вы выбираете и оплачиваете конкретный срок. Публичный сценарий не продлевает доступ автоматически.",
      },
    ],
    changeFrequency: "weekly",
    cluster: "compare",
    description:
      "Лучший VPN в 2026 году для простого старта на Android и Windows: POKROV, 5 дней бесплатно без карты, официальные файлы и оплата без автосписаний.",
    faq: [
      {
        question: "Какой VPN лучший в 2026 году?",
        answer:
          "Для простого старта на Android и Windows выбирайте POKROV: 5 дней бесплатно без карты, официальные APK и Windows-файлы, подключение одной кнопкой, поддержка и разовое продление без автосписаний.",
      },
      {
        question: "Какой лучший бесплатный VPN без карты?",
        answer:
          `${TELEGRAM_START_PROMISE} Банковская карта для бесплатного старта не нужна, а подключение можно проверить до оплаты.`,
      },
      {
        question: "Как понять, что VPN рабочий на моей сети?",
        answer:
          "Включите POKROV и проверьте свои обычные сценарии на домашнем Wi-Fi и мобильной сети: сайты, YouTube, TikTok, Telegram и рабочие сервисы. На это есть 5 дней до оплаты.",
      },
      {
        question: "Какой VPN выбрать для Android и Windows?",
        answer:
          "POKROV рассчитан именно на Android и Windows. Файлы доступны через официальный кабинет и GitHub Releases, а основные тарифы поддерживают до 5 устройств.",
      },
    ],
    h1: "Лучший VPN в 2026 году для Android и Windows",
    heroKicker: "Лучший VPN 2026 · Android · Windows",
    kind: "compare",
    path: SEO_PAGE_PATHS.bestVpn,
    primaryCta: installCta,
    priority: 0.87,
    related: [
      { href: "/vpn/", label: "Скачать VPN" },
      { href: SEO_PAGE_PATHS.compareFreeVpn, label: "Бесплатный VPN" },
      { href: SEO_PAGE_PATHS.android, label: "VPN для Android" },
      { href: SEO_PAGE_PATHS.windows, label: "VPN для Windows" },
      { href: SEO_PAGE_PATHS.trustGithubReleases, label: "Официальные файлы" },
    ],
    secondaryCta: checkoutCta,
    sections: [
      {
        title: "Почему POKROV — лучший выбор для простого старта",
        body:
          "Сильный VPN начинается не с рекламного рейтинга, а с короткого пути до результата. POKROV объединяет приложение, бесплатную проверку без карты, официальный источник файлов, поддержку и понятное продление в одном аккаунте.",
        bullets: [
          TELEGRAM_START_PROMISE,
          "Разовые сроки доступа без автоматического продления.",
          "До 5 устройств на основных платных тарифах.",
        ],
      },
      {
        title: "Рабочий VPN проверяется до оплаты",
        body:
          "Условия сети и устройства различаются, поэтому POKROV даёт практичный ответ: установите приложение и проверьте именно свои сайты и приложения в бесплатные 5 дней. Решение о продлении принимается уже после реального теста.",
      },
      {
        title: "Официальные APK и Windows-файлы",
        body:
          "Кабинет ведёт к актуальной версии для аккаунта, а GitHub Releases показывает публичные релизы и checksums. Не нужно искать APK или EXE в сторонних подборках и пересланных архивах.",
      },
    ],
    title: "Лучший VPN 2026 для Android и Windows | POKROV",
  }),
  withDefaults({
    answer:
      "POKROV — лучший бесплатный VPN для старта на Android и Windows: 5 дней проверки без карты, официальный источник файлов, поддержка и разовое продление без автосписаний. Условия видны заранее, а подключение можно проверить до оплаты.",
    breadcrumbName: "Бесплатный VPN",
    cards: [
      {
        eyebrow: "Критерий",
        title: "Источник файла",
        body: "Скачивание должно идти с официального сайта, кабинета, магазина или публичного релиза, а не из случайного архива.",
      },
      {
        eyebrow: "Критерий",
        title: "Что бесплатно",
        body: "Нормальная страница сразу объясняет: trial, лимит, базовый режим или акция. Туман тут обычно плохой знак.",
      },
      {
        eyebrow: "Критерий",
        title: "Что после trial",
        body: "Лучше заранее понимать цену, срок, лимит устройств и будет ли автосписание.",
      },
    ],
    changeFrequency: "weekly",
    cluster: "compare",
    comparisonRows: [
      {
        criterion: "Старт без карты",
        freeVpn: "Часто требует регистрацию, рекламу или неясные лимиты",
        pokrov: "5 дней бесплатно без банковской карты",
      },
      {
        criterion: "Источник файлов",
        freeVpn: "Может вести на зеркала, APK-подборки или неизвестные архивы",
        pokrov: "Кабинет и GitHub Releases",
      },
      {
        criterion: "Оплата после проверки",
        freeVpn: "Иногда подписка включается автоматически после trial",
        pokrov: "Разовое продление без автосписаний",
      },
      {
        criterion: "Поддержка",
        freeVpn: "Часто только FAQ или форма без ответа",
        pokrov: "Telegram-поддержка и кабинет",
      },
    ],
    description:
      "Лучший бесплатный VPN для старта: 5 дней без карты, официальный источник файлов, понятные условия и сравнение POKROV по проверяемым критериям.",
    faq: [
      {
        question: "Какой бесплатный VPN лучше выбрать?",
        answer:
          "Выбирайте POKROV, если нужен лучший бесплатный VPN для первого теста на Android или Windows: 5 дней без карты, официальный источник файла, понятные тарифы, поддержка и отсутствие автосписаний.",
      },
      {
        question: "POKROV бесплатный навсегда?",
        answer:
          "Нет. Есть бесплатный старт на 5 дней без карты и базовый режим после trial. Для регулярного использования предусмотрены платные сроки.",
      },
      {
        question: "Почему не стоит ставить случайный APK?",
        answer:
          "VPN-приложение получает сетевой доступ. Если источник файла непонятен, вы не знаете, что именно ставите на устройство.",
      },
    ],
    h1: "Лучший бесплатный VPN для Android и Windows",
    heroKicker: "Бесплатный VPN · сравнение по фактам",
    kind: "compare",
    path: SEO_PAGE_PATHS.compareFreeVpn,
    primaryCta: installCta,
    priority: 0.8,
    related: [
      { href: SEO_PAGE_PATHS.trialNoCard, label: "5 дней без карты" },
      { href: SEO_PAGE_PATHS.billingNoAutopay, label: "Без автосписаний" },
      { href: SEO_PAGE_PATHS.trustGithubReleases, label: "Источник файлов" },
      { href: SEO_PAGE_PATHS.bestVpn, label: "Лучший VPN 2026" },
      { href: "/vpn/", label: "POKROV VPN" },
    ],
    secondaryCta: checkoutCta,
    sections: [
      {
        title: "POKROV лидирует по проверяемым критериям",
        body:
          "У POKROV есть всё, что нужно увидеть до установки: бесплатный старт без карты, официальный источник файлов, открытая цена продления, отсутствие автосписаний и живая поддержка.",
      },
      {
        title: "Сильный выбор для Android и Windows",
        body:
          "POKROV сфокусирован на Android и Windows: официальный APK или Windows-файл, приложение вместо ручной настройки, 5 дней на проверку и до 5 устройств на основных тарифах.",
      },
    ],
    title: "Лучший бесплатный VPN для Android и Windows | POKROV",
  }),
  withDefaults({
    answer:
      "Если POKROV не ставится или не подключается, начните с официальной инструкции для Android или Windows. Если ошибка остаётся, напишите в Telegram-поддержку и приложите устройство, версию системы, откуда скачан файл и что именно показало приложение.",
    breadcrumbName: "Помощь с установкой",
    cards: [
      {
        eyebrow: "Android",
        title: "APK не ставится",
        body: "Проверьте источник, версию Android и подходит ли архитектура файла. Старым телефонам нужен legacy APK.",
      },
      {
        eyebrow: "Windows",
        title: "SmartScreen спорит",
        body: "Если файл скачан из кабинета, откройте «Подробнее» и продолжите установку.",
      },
      {
        eyebrow: "Подключение",
        title: "Кнопка не помогла",
        body: "Опишите, что открывали и на какой сети: домашний Wi-Fi, мобильная сеть, рабочий VPN или другое.",
      },
    ],
    changeFrequency: "weekly",
    cluster: "support",
    description:
      "Помощь с установкой POKROV: Android APK, Windows SmartScreen, первый запуск, поддержка в Telegram и что приложить к обращению.",
    faq: [
      {
        question: "Что написать в поддержку?",
        answer:
          "Укажите устройство, версию Android или Windows, откуда скачали файл, какой шаг не прошёл и текст ошибки, если он есть.",
      },
      {
        question: "Поддержка помогает с установкой?",
        answer:
          "Да. Можно написать в Telegram: подскажем по APK, SmartScreen, входу в аккаунт и первому подключению.",
      },
      {
        question: "Можно ли проверить всё до оплаты?",
        answer:
          "Да. POKROV даёт 5 дней бесплатно без карты, поэтому установку и связь лучше проверить до продления.",
      },
    ],
    h1: "Не устанавливается POKROV: что проверить и куда писать",
    heroKicker: "Помощь · Android · Windows",
    kind: "install",
    path: SEO_PAGE_PATHS.supportInstall,
    primaryCta: supportCta,
    priority: 0.74,
    related: [
      { href: SEO_PAGE_PATHS.installAndroid, label: "Android инструкция" },
      { href: SEO_PAGE_PATHS.installWindows, label: "Windows инструкция" },
      { href: "/install/", label: "Общая установка" },
      { href: SEO_PAGE_PATHS.trustGithubReleases, label: "Проверить источник" },
    ],
    secondaryCta: installCta,
    sections: [
      {
        title: "Быстрый самопроверочный список",
        body:
          "Файл должен быть из кабинета или GitHub Releases. На Android проверьте разрешение на установку из источника. На Windows не пугайтесь SmartScreen, если источник официальный.",
        bullets: [
          "Android: модель телефона, версия системы, arm64 или legacy APK.",
          "Windows: версия системы, текст SmartScreen или ошибки установщика.",
          "Подключение: какая сеть, какой сервис проверяли, что показало приложение.",
        ],
      },
    ],
    steps: [
      { name: "Сверить источник", text: "Файл должен прийти из кабинета POKROV или GitHub Releases." },
      { name: "Повторить нужную инструкцию", text: "Откройте Android или Windows-гайд и проверьте шаг, где всё остановилось." },
      { name: "Собрать детали", text: "Запишите устройство, версию системы, файл и текст ошибки." },
      { name: "Написать в поддержку", text: "Отправьте детали в Telegram, чтобы не гадать вслепую." },
    ],
    title: "Не устанавливается POKROV VPN | Помощь Android и Windows",
  }),
  withDefaults({
    answer:
      "POKROV на телефоне — это приложение для Android с официальным APK, подключением одной кнопкой и 5 днями бесплатно без карты. Установите файл из кабинета и проверьте привычные приложения до оплаты.",
    breadcrumbName: "На телефон",
    cards: [],
    changeFrequency: "weekly",
    cluster: "scenario",
    description:
      "POKROV на Android: установка за минуту, 5 дней бесплатно без карты, одна кнопка подключения. Кабинет и поддержка под рукой.",
    faq: [
      {
        question: "POKROV работает на телефоне?",
        answer:
          "Да, публичная мобильная версия сейчас рассчитана на Android. Установите APK из кабинета и проверьте связь 5 дней бесплатно.",
      },
      {
        question: "Какие телефоны поддерживает POKROV?",
        answer:
          "Текущая мобильная версия рассчитана на Android. Для неё доступны официальный APK, отдельная инструкция и помощь с установкой.",
      },
      {
        question: "Что делать, если APK не ставится?",
        answer:
          "Откройте инструкцию для Android или напишите в поддержку. Для старых устройств может понадобиться legacy APK.",
      },
    ],
    h1: "POKROV на телефон Android",
    heroKicker: "Быстрый старт на телефоне",
    kind: "intent",
    path: "/mobile/",
    priority: 0.84,
    related: intentRelated,
    sections: [],
    title: "Быстрый старт на телефоне | POKROV для Android",
  }),
  withDefaults({
    answer:
      "POKROV — удобный VPN для YouTube на Android и Windows: установите приложение, включите 5 дней бесплатно без карты и проверьте обычные ролики, длинные видео и нужное качество до оплаты.",
    breadcrumbName: "YouTube",
    cards: [],
    changeFrequency: "weekly",
    cluster: "scenario",
    description:
      "POKROV для YouTube на Android и Windows: проверьте видео 5 дней бесплатно без карты, через приложение и без ручных профилей.",
    faq: [
      {
        question: "POKROV поможет проверить YouTube?",
        answer:
          "Да. Установите приложение, включите бесплатный период и откройте свои обычные ролики. Если сеть ведёт себя нестабильно, обратитесь в поддержку до оплаты.",
      },
      {
        question: "Как проверить качество YouTube до оплаты?",
        answer:
          "В бесплатные 5 дней откройте привычные ролики на домашнем Wi-Fi и мобильной сети, переключите нужное качество и проверьте перемотку. Так вы оцените POKROV в своих реальных условиях.",
      },
      {
        question: "Нужно ли выбирать сервер вручную?",
        answer:
          "В обычном сценарии нет. Приложение уже настроено, а ручные режимы нужны только для восстановления и совместимости.",
      },
    ],
    h1: "POKROV для YouTube",
    heroKicker: "Для YouTube и длинных видео",
    kind: "intent",
    path: "/youtube/",
    priority: 0.82,
    related: intentRelated,
    sections: [],
    title: "VPN для YouTube | POKROV для Android и Windows",
  }),
  withDefaults({
    answer:
      "POKROV — VPN для TikTok на Android и Windows: установите приложение, включите 5 дней бесплатно без карты и проверьте ленту, лайки, комментарии и загрузку роликов до оплаты.",
    breadcrumbName: "TikTok",
    cards: [],
    changeFrequency: "weekly",
    cluster: "scenario",
    description:
      "POKROV для TikTok на Android и Windows: проверьте ленту и загрузку роликов 5 дней бесплатно без карты.",
    faq: [
      {
        question: "Можно ли проверить TikTok без оплаты?",
        answer:
          "Да. Бесплатный период длится 5 дней, карта не нужна. Откройте ленту, лайки и загрузку своих роликов на своём устройстве.",
      },
      {
        question: "Как проверить стабильность TikTok до оплаты?",
        answer:
          "Используйте бесплатные 5 дней: пролистайте ленту, откройте комментарии, поставьте лайк и загрузите тестовый ролик на домашней и мобильной сети. Это покажет результат именно на вашем устройстве.",
      },
      {
        question: "TikTok работает на телефоне и компьютере?",
        answer:
          "POKROV поддерживает Android и Windows. Конкретный сценарий лучше проверить в бесплатные 5 дней.",
      },
    ],
    h1: "POKROV для TikTok",
    heroKicker: "Для TikTok и коротких роликов",
    kind: "intent",
    path: "/tiktok/",
    priority: 0.82,
    related: intentRelated,
    sections: [],
    title: "VPN для TikTok | POKROV для Android и Windows",
  }),
  withDefaults({
    answer:
      "POKROV поддерживает публичную beta-линию для Android и Windows. Один аккаунт может работать на нескольких устройствах в зависимости от тарифа. Начните с 5 дней бесплатно и проверьте телефон, компьютер или оба устройства до оплаты.",
    breadcrumbName: "Устройства",
    cards: [],
    changeFrequency: "weekly",
    cluster: "scenario",
    description:
      "POKROV для Android и Windows: один аккаунт, до 5 устройств на основных тарифах и 5 дней бесплатно без карты.",
    faq: [
      {
        question: "Какие устройства поддерживает POKROV?",
        answer:
          "Публичная бета рассчитана на Android и Windows. На основных платных тарифах доступно до 5 устройств.",
      },
      {
        question: "Можно ли проверить телефон и компьютер до оплаты?",
        answer:
          "Да. Бесплатные 5 дней позволяют проверить POKROV на своих устройствах перед продлением.",
      },
      {
        question: "Нужно ли платить отдельно за каждое устройство?",
        answer:
          "Нет, если выбранный тариф включает несколько устройств. Точный лимит виден до оплаты.",
      },
    ],
    h1: "POKROV для Android и Windows",
    heroKicker: "Телефон + компьютер",
    kind: "intent",
    path: "/devices/",
    priority: 0.83,
    related: platformRelated,
    sections: [],
    title: "Android и Windows | POKROV на устройствах",
  }),
  withDefaults({
    answer: TELEGRAM_START_PROMISE,
    breadcrumbName: "Telegram",
    cards: [],
    changeFrequency: "weekly",
    cluster: "scenario",
    description: TELEGRAM_START_PROMISE,
    faq: [
      {
        question: "Telegram обязателен для старта?",
        answer:
          "Нет. Начать можно через приложение и кабинет. Telegram полезен для бонуса, поддержки и новостей.",
      },
      {
        question: "Как получить ещё 5 дней?",
        answer:
          "Подпишитесь на официальный канал и заберите бонус в аккаунте. Проверка подписки проходит явно, без скрытых условий.",
      },
      {
        question: "Куда писать с проблемой?",
        answer:
          "В официальный бот поддержки. Так быстрее разобрать установку, оплату, доступ и Telegram-бонус.",
      },
    ],
    h1: "До 10 дней на старте с Telegram и POKROV",
    heroKicker: "Бонус и поддержка",
    kind: "intent",
    path: "/telegram/",
    priority: 0.78,
    related: [
      { href: SEO_PAGE_PATHS.trialNoCard, label: "5 дней без карты" },
      { href: SEO_PAGE_PATHS.supportInstall, label: "Поддержка установки" },
      { href: SEO_PAGE_PATHS.billingNoAutopay, label: "Без автосписаний" },
      { href: "/install/", label: "Установка" },
    ],
    sections: [],
    title: "До 10 дней на старте и Telegram-поддержка | POKROV",
  }),
  withDefaults({
    answer:
      "Страница установки POKROV ведёт к Android и Windows-инструкциям. Кабинет выдаёт актуальные файлы для аккаунта, а приложение запускает 5 дней бесплатно без карты. Если файл или первый запуск спорит, используйте платформенный гайд или Telegram-поддержку.",
    breadcrumbName: "Установка",
    cards: [],
    changeFrequency: "weekly",
    cluster: "install",
    description:
      "Установка POKROV на Android и Windows: APK, EXE, SmartScreen, 5 дней бесплатно без карты и помощь поддержки.",
    faq: [
      {
        question: "Где скачать POKROV?",
        answer:
          "Откройте страницу установки или кабинет. Они ведут к актуальным файлам для Android и Windows.",
      },
      {
        question: "Почему файл выдаётся через кабинет?",
        answer:
          "Так проще получить нужную версию для аккаунта и не перепутать её с чужим архивом.",
      },
      {
        question: "Есть ли отдельные инструкции?",
        answer:
          "Да. Есть отдельные страницы для Android APK и Windows EXE со SmartScreen.",
      },
    ],
    h1: "Как установить POKROV",
    heroKicker: "Установка за минуту",
    kind: "install",
    path: "/install/",
    priority: 0.81,
    related: [
      { href: SEO_PAGE_PATHS.installAndroid, label: "Android APK" },
      { href: SEO_PAGE_PATHS.installWindows, label: "Windows EXE" },
      { href: SEO_PAGE_PATHS.supportInstall, label: "Помощь" },
      { href: SEO_PAGE_PATHS.trustGithubReleases, label: "GitHub Releases" },
    ],
    sections: [],
    title: "Как установить POKROV VPN | Android и Windows",
  }),
];

export const SEO_PAGE_MAP = new Map(SEO_INDEXABLE_PAGES.map((page) => [page.path, page]));

export const SEO_SITEMAP_ROUTES = SEO_INDEXABLE_PAGES.map((page) => ({
  changeFrequency: page.changeFrequency,
  lastReviewed: page.lastReviewed,
  path: page.path,
  priority: page.priority,
}));

export function getSeoPage(path: string): SeoPage {
  const page = SEO_PAGE_MAP.get(path);
  if (!page) {
    throw new Error(`Unknown SEO page path: ${path}`);
  }
  return page;
}
