import catalog from "./trust-and-guides.json";

export type GuideVisualDevice = "phone" | "desktop" | "browser";

export type GuideVisualHotspot = {
  left: number;
  top: number;
  width: number;
  height: number;
  label?: string;
};

export type GuideVisualScreenshot = {
  imageSrc: string;
  imageAlt: string;
  imageWidth: number;
  imageHeight: number;
  title: string;
  instruction: string;
  hotspot?: GuideVisualHotspot;
};

export type GuideVisualSource = {
  href: string;
  label: string;
};

export type GuideVisualSpec = {
  kind: "simulation" | "screenshot";
  client: string;
  platform: string;
  screen: string;
  device: GuideVisualDevice;
  path: readonly [string, string, string];
  note?: string;
  imageSrc?: string;
  imageAlt?: string;
  imageWidth?: number;
  imageHeight?: number;
  hotspot?: GuideVisualHotspot;
  screenshots?: readonly GuideVisualScreenshot[];
  sourceHref?: string;
  sourceLabel?: string;
  sources?: readonly GuideVisualSource[];
};

function app(
  platform: string,
  screen: string,
  before: string,
  target: string,
  result: string,
  device: GuideVisualDevice = platform === "Windows" ? "desktop" : "phone",
): GuideVisualSpec {
  return {
    kind: "simulation",
    client: "POKROV",
    platform,
    screen,
    device,
    path: [before, target, result],
  };
}

function cabinet(
  screen: string,
  before: string,
  target: string,
  result: string,
): GuideVisualSpec {
  return {
    kind: "simulation",
    client: "Кабинет POKROV",
    platform: "Браузер",
    screen,
    device: "browser",
    path: [before, target, result],
  };
}

function site(
  screen: string,
  before: string,
  target: string,
  result: string,
): GuideVisualSpec {
  return {
    kind: "simulation",
    client: "Сайт POKROV",
    platform: "Браузер",
    screen,
    device: "browser",
    path: [before, target, result],
  };
}

export const GUIDE_VISUALS: Record<string, GuideVisualSpec> = {
  "start-android": app("Android", "Страница загрузки", "Скачать POKROV", "Открыть APK", "Установить"),
  "start-windows": app("Windows", "Страница загрузки", "Скачать POKROV", "Открыть установщик", "Запустить POKROV", "desktop"),
  trial: app("Android / Windows", "Первый запуск", "Войти или создать аккаунт", "Начать 5 дней", "Доступ активен"),
  connect: app("Android / Windows", "Главная", "Статус: не подключено", "Подключить", "Статус: защищено"),
  repair: app("Android / Windows", "Центр защиты", "Проверка соединения", "Восстановить", "Проверить ещё раз"),
  locations: app("Android / Windows", "Локации", "Найти страну или город", "Выбрать локацию", "Переподключить"),
  favorites: app("Android / Windows", "Локации", "Найти нужный город", "Нажать звезду", "Открыть «Избранное»"),
  "route-smart": app("Android / Windows", "Правила", "Режим подключения", "Умный режим", "Проверить маршрут"),
  "route-full": app("Android / Windows", "Правила", "Режим подключения", "Весь трафик", "Переподключить"),
  "route-apps": app("Android / Windows", "Правила", "Только выбранные", "Выбрать приложение", "Сохранить список"),
  "route-purpose": app("Android / Windows", "Готовые маршруты", "Выбрать задачу", "Видео / AI / соцсети / игры", "Проверить приложение"),
  "route-custom": app("Android / Windows", "Свои правила", "Открыть список", "Добавить правило", "Сохранить домен или IP"),
  dns: app("Android / Windows", "DNS и локальная сеть", "Открыть DNS", "Выбрать DNS-over-HTTPS", "Переподключить"),
  lan: app("Android / Windows", "DNS и локальная сеть", "Найти «Локальная сеть»", "Переключить доступ", "Проверить локальное устройство"),
  "always-on": app("Android", "Системные настройки VPN", "POKROV", "Постоянная VPN", "Блокировать без VPN"),
  notifications: app("Android / Windows", "Профиль · Уведомления", "Открыть inbox", "Нажать уведомление", "Отметить прочитанным"),
  devices: cabinet("Устройства", "Сверить платформу и время", "Отозвать устройство", "Обновить список"),
  "fallback-hiddify": {
    kind: "screenshot",
    client: "Hiddify",
    platform: "Android / Windows / TV",
    screen: "Добавление профиля",
    device: "desktop",
    path: ["Скопировать личную ссылку в POKROV", "Add from clipboard", "Обновить профиль и подключиться"],
    imageSrc: "/guides/hiddify-add-from-clipboard.png",
    imageAlt: "Экран Hiddify с вариантами Add from clipboard и Add manually",
    imageWidth: 1738,
    imageHeight: 1420,
    hotspot: { left: 16.2, top: 55.8, width: 33.2, height: 40.8, label: "Add from clipboard" },
    note: "Скрин из официальной инструкции Hiddify. В новой версии подписи или расположение могут немного отличаться.",
    sourceHref: "https://hiddify.com/app/How-to-use-Hiddify-app/",
    sourceLabel: "Официальная инструкция Hiddify",
  },
  "fallback-happ": {
    kind: "screenshot",
    client: "Happ",
    platform: "Android / iOS",
    screen: "Главная · меню «+»",
    device: "desktop",
    path: ["Нажать «+» в правом верхнем углу", "Добавить подписку", "Вставить ссылку ?format=happ"],
    imageSrc: "/guides/happ-add-subscription.png",
    imageAlt: "Меню добавления профиля в Happ 3.26.3",
    imageWidth: 1600,
    imageHeight: 900,
    hotspot: { left: 75.4, top: 12.9, width: 23.1, height: 8, label: "Добавить подписку" },
    note: "Реальный экран Happ 3.26.3, снятый на чистом LDPlayer без профиля и личной ссылки.",
    sourceHref: "https://github.com/Happ-proxy/happ-android",
    sourceLabel: "Официальный репозиторий Happ Android",
  },
  "fallback-v2rayn": {
    kind: "screenshot",
    client: "v2rayN",
    platform: "Windows",
    screen: "Subscription group",
    device: "desktop",
    path: ["Скопировать личную subscription URL", "Add subscription group", "Update subscription"],
    screenshots: [
      {
        imageSrc: "/guides/v2rayn-subscription-group.jpg",
        imageAlt: "Открытое меню Subscription Group в v2rayN 7.15.7",
        imageWidth: 886,
        imageHeight: 693,
        title: "Открыть настройки группы",
        instruction: "Subscription Group → Subscription group settings.",
        hotspot: {
          left: 17.1,
          top: 11.4,
          width: 33.6,
          height: 7.5,
          label: "Subscription group settings",
        },
      },
      {
        imageSrc: "/guides/v2rayn-subscription-settings-add.png",
        imageAlt: "Форма добавления группы подписки v2rayN с безопасным примером URL",
        imageWidth: 2536,
        imageHeight: 1542,
        title: "Добавить POKROV",
        instruction: "Нажать Add, задать имя POKROV и вставить личную ссылку в поле Url.",
      },
    ],
    note: "Первый экран — v2rayN 7.15.7 на английском, второй — та же форма на китайской локали с безопасным примером URL. Названия и порядок сверены с официальной wiki; язык зависит от настроек клиента.",
    sources: [
      {
        href: "https://en.v2rayn.org/start/",
        label: "Источник экрана v2rayN 7.15.7",
      },
      {
        href: "https://unblockium.com/guides/setup/v2rayn",
        label: "Источник формы добавления",
      },
      {
        href: "https://github.com/2dust/v2rayN/wiki/Description-of-subscription",
        label: "Официальная wiki v2rayN",
      },
    ],
  },
  "fallback-v2rayng": {
    kind: "screenshot",
    client: "v2rayNG",
    platform: "Android",
    screen: "Subscription group setting",
    device: "phone",
    path: ["Меню", "Subscription group setting", "Update subscription"],
    screenshots: [
      {
        imageSrc: "/guides/v2rayng-menu-subscription.png",
        imageAlt: "Меню v2rayNG с выделенным пунктом Subscription group setting",
        imageWidth: 364,
        imageHeight: 677,
        title: "Открыть группы",
        instruction: "Меню ☰ → Subscription group setting.",
      },
      {
        imageSrc: "/guides/v2rayng-add-group.png",
        imageAlt: "Экран групп подписки v2rayNG с выделенной кнопкой плюс",
        imageWidth: 366,
        imageHeight: 721,
        title: "Создать группу",
        instruction: "Нажать «+» в правом верхнем углу.",
      },
      {
        imageSrc: "/guides/v2rayng-edit-group.png",
        imageAlt: "Форма группы подписки v2rayNG с полями remarks, URL и enable update",
        imageWidth: 363,
        imageHeight: 716,
        title: "Вставить ссылку",
        instruction: "Имя POKROV → личная URL → enable update → галочка ✓.",
      },
      {
        imageSrc: "/guides/v2rayng-update-subscription.png",
        imageAlt: "Меню v2rayNG с выделенным пунктом Update subscription",
        imageWidth: 359,
        imageHeight: 675,
        title: "Получить профили",
        instruction: "Вернуться на главный экран → меню ⋮ → Update subscription.",
      },
    ],
    note: "Реальные экраны из инструкции Hiddify; названия полей сверены с текущими ресурсами официального v2rayNG. Импорт выдачи POKROV остаётся best effort до контрольного полевого теста.",
    sources: [
      {
        href: "https://hiddify.com/manager/client-software-on-android/Tutorial-for-V2rayNG-app/",
        label: "Пошаговые экраны v2rayNG",
      },
      {
        href: "https://github.com/2dust/v2rayNG",
        label: "Официальный репозиторий v2rayNG",
      },
    ],
  },
  "fallback-streisand": {
    kind: "screenshot",
    client: "Streisand",
    platform: "iOS / iPadOS",
    screen: "Добавление профиля",
    device: "phone",
    path: ["Главная · «+»", "Import subscription / Clipboard", "Выбрать профиль и включить VPN"],
    screenshots: [
      {
        imageSrc: "/guides/streisand-add-from-clipboard.jpg",
        imageAlt: "Меню Streisand с кнопкой плюс и пунктом Import from Clipboard",
        imageWidth: 369,
        imageHeight: 724,
        title: "Импортировать ссылку",
        instruction: "Нажать «+» → Import from Clipboard.",
      },
      {
        imageSrc: "/guides/streisand-subscription-menu.jpg",
        imageAlt: "Меню подписки Streisand с командами Update, Edit и Delete",
        imageWidth: 1125,
        imageHeight: 2237,
        title: "Обновить подписку",
        instruction: "Удержать строку Subscription → Update.",
        hotspot: {
          left: 14.8,
          top: 43.4,
          width: 62,
          height: 5.5,
          label: "Update",
        },
      },
      {
        imageSrc: "/guides/streisand-update-on-open.png",
        imageAlt: "Настройка Update On Open в разделе Subscription приложения Streisand",
        imageWidth: 1125,
        imageHeight: 2242,
        title: "Включить автообновление",
        instruction: "Settings → Subscription → Update On Open.",
        hotspot: {
          left: 71.3,
          top: 11.1,
          width: 13.7,
          height: 4.1,
          label: "Update On Open",
        },
      },
    ],
    note: "Реальные экраны iOS из актуальной инструкции Hiddify. Подписи и доступность приложения могут отличаться по версии, языку и региону App Store.",
    sources: [
      {
        href: "https://hiddify.com/manager/client-software-on-ios/Tutorial-for-Streisand/",
        label: "Пошаговые экраны Streisand",
      },
      {
        href: "https://apps.apple.com/us/app/streisand/id6450534064",
        label: "Официальная карточка Streisand",
      },
    ],
  },
  "fallback-v2box": {
    kind: "screenshot",
    client: "V2Box",
    platform: "iOS / iPadOS / macOS",
    screen: "Subscriptions",
    device: "phone",
    path: ["Subscriptions", "Add / Import subscription URL", "Update · выбрать узел · Connect"],
    screenshots: [
      {
        imageSrc: "/guides/v2box-configs-add.png",
        imageAlt: "Меню Configs в V2Box с пунктом Add Subscription",
        imageWidth: 591,
        imageHeight: 1168,
        title: "Добавить подписку",
        instruction: "Configs → «+» → Add Subscription.",
      },
      {
        imageSrc: "/guides/v2box-update-all.jpg",
        imageAlt: "Меню V2Box с пунктом Update All Subscriptions",
        imageWidth: 591,
        imageHeight: 574,
        title: "Обновить профили",
        instruction: "Configs → «+» → Update All Subscriptions.",
      },
      {
        imageSrc: "/guides/v2box-auto-update.jpg",
        imageAlt: "Настройки V2Box с включённым Auto Update",
        imageWidth: 591,
        imageHeight: 1173,
        title: "Включить Auto Update",
        instruction: "Меню списка Configs → Subscription → Auto Update → Confirm.",
      },
      {
        imageSrc: "/guides/v2box-connect.jpg",
        imageAlt: "Главный экран V2Box со слайдером Slide to Connect",
        imageWidth: 591,
        imageHeight: 1167,
        title: "Подключиться",
        instruction: "Home → сдвинуть Slide to Connect вправо.",
      },
    ],
    note: "Реальные экраны из инструкции Hiddify. www.yahoo.com в кадре — тестовые записи автора инструкции, не сервер POKROV; добавлять их не нужно.",
    sources: [
      {
        href: "https://hiddify.com/manager/client-software-on-ios/Tutorial-for-V2Box-app/",
        label: "Пошаговые экраны V2Box",
      },
      {
        href: "https://apps.apple.com/us/app/v2box-v2ray-client/id6446814690",
        label: "Официальная карточка V2Box",
      },
    ],
  },
  "fallback-shadowrocket": {
    kind: "screenshot",
    client: "Shadowrocket",
    platform: "iOS / iPadOS / macOS / Apple TV",
    screen: "Subscribe / Subscription",
    device: "phone",
    path: ["Главная · «+»", "Type: Subscribe · вставить URL", "Update · Proxy mode · VPN"],
    screenshots: [
      {
        imageSrc: "/guides/shadowrocket-hiddify-plus.jpg",
        imageAlt: "Главный экран Shadowrocket с отмеченными Settings и кнопкой плюс",
        imageWidth: 591,
        imageHeight: 1168,
        title: "Открыть добавление",
        instruction: "Для добавления нажать метку 2 — «+». Метка 1 открывает Settings.",
      },
      {
        imageSrc: "/guides/shadowrocket-hiddify-subscribe.jpg",
        imageAlt: "Форма Add Server в Shadowrocket с типом Subscribe и полем URL",
        imageWidth: 591,
        imageHeight: 1164,
        title: "Выбрать Subscribe",
        instruction: "Метка 3 = Type: Subscribe; метка 4 = личная URL. Затем Save сверху.",
      },
      {
        imageSrc: "/guides/shadowrocket-update-on-open.jpg",
        imageAlt: "Раздел Subscribe в Shadowrocket с Update On Open и Auto Background Update",
        imageWidth: 653,
        imageHeight: 1280,
        title: "Настроить обновление",
        instruction: "Settings → Subscribe → Update On Open; фоновое обновление — по желанию.",
      },
    ],
    note: "Платный продвинутый клиент. Реальные экраны взяты из инструкции Hiddify; для первого теста не нужны чужие rules, modules, scripts или HTTPS decryption.",
    sources: [
      {
        href: "https://hiddify.com/manager/client-software-on-ios/Tutorial-for-ShadowRocket-app/",
        label: "Пошаговые экраны Shadowrocket",
      },
      {
        href: "https://apps.apple.com/us/app/shadowrocket/id932747118",
        label: "Официальная карточка Shadowrocket",
      },
    ],
  },
  "android-tv": app("Android TV", "Установка на телевизоре", "Устройства · выдать код", "Ввести код или открыть QR", "Подключиться", "desktop"),
  payment: cabinet("Подписка", "Выбрать срок", "Перейти к оплате", "Дождаться подтверждения"),
  redeem: cabinet("Активация кода", "Ввести код", "Активировать", "Проверить новый срок"),
  support: app("Приложение / кабинет / сайт", "Поддержка", "Описать проблему", "Отправить обращение", "Сохранить номер"),
  "apple-account": {
    kind: "simulation",
    client: "App Store / поддержка POKROV",
    platform: "iOS / iPadOS",
    screen: "Аварийная установка клиента",
    device: "phone",
    path: [
      "Сначала проверить смену региона своего аккаунта",
      "Если не подходит — выбрать отдельный или временный аккаунт",
      "Войти только через App Store, установить клиент и вернуть свой аккаунт",
    ],
    note: "Смена региона или отдельный личный Apple Account — основной путь. POKROV не копирует и не проксирует чужие реквизиты: временные данные остаются на текущей странице источника.",
    sources: [
      {
        href: "https://support.apple.com/ru-ru/108647",
        label: "Apple: создать свой Apple Account",
      },
      {
        href: "https://support.apple.com/ru-ru/118283",
        label: "Apple: изменить страну или регион",
      },
      {
        href: "https://familypro.io/shared-apple-id",
        label: "FamilyPro: бесплатный общий Apple ID",
      },
      {
        href: "https://vanyavpn.app/ios",
        label: "VanyaVPN: временный US App Store-аккаунт",
      },
      {
        href: "https://izakstore.ru/",
        label: "iZakStore: бесплатные записи и платная подписка",
      },
      {
        href: "https://happplus.com/",
        label: "Happ Доступ: платная помощь с установкой Happ",
      },
      {
        href: "https://appstops.ru/catalog",
        label: "AppStops: платный каталог приложений",
      },
      {
        href: "https://wokerhome.com/shop/products/55",
        label: "WokerHome: отдельный US Apple Account",
      },
    ],
  },
  "protection-center": app("Android / Windows", "Главная", "Нажать строку состояния", "Открыть центр защиты", "Проверить Tunnel / DNS / HTTPS"),
  "offline-cache": app("Android / Windows", "Локации или уведомления", "Открыть без сети", "Проверить отметку cache", "Обновить после возврата сети"),
  "route-explain": app("Android / Windows", "Куда пойдёт адрес?", "Ввести домен или IP", "Нажать стрелку", "Прочитать маршрут и причину"),
  "trusted-wifi": app("Android / Windows", "Доверенный Wi‑Fi", "Добавить или определить сеть", "Включить паузу", "Проверить текущую сеть"),
  "quick-settings": app("Android", "Редактор быстрых настроек", "Найти плитку POKROV", "Перетащить плитку", "Нажать для подключения"),
  "windows-tray": app("Windows", "Системный трей", "Открыть значок POKROV", "Подключить / отключить", "Сверить состояние окна", "desktop"),
  pairing: cabinet("Добавить устройство", "Выпустить одноразовый код", "Ввести код на новом устройстве", "Отменить неиспользованный код"),
  "referral-center": cabinet("Награды", "Скопировать личную ссылку", "Открыть этапы приглашений", "Проверить начисление"),
  "wheel-discount": app("Приложение / кабинет", "Колесо", "Дождаться доступного вращения", "Крутить", "Проверить скидку при продлении"),
  "incident-compensation": app("Приложение / кабинет", "Уведомление об инциденте", "Открыть подтверждённый инцидент", "Проверить компенсацию", "Сверить историю доступа"),
  "privacy-fields": site("Приватность", "Выбрать поле данных", "Открыть цель и срок хранения", "Проверить границы"),
  "responsibility-map": site("Карта ответственности", "Выбрать вопрос", "Открыть ответственного", "Перейти в нужный канал"),
  "status-preauth": site("Статус", "Открыть без входа", "Проверить активное сообщение", "Следовать восстановлению"),
  "competitor-switch": cabinet("Программы", "Выбрать «Переход»", "Заполнить заявку", "Отправить на проверку"),
  "research-program": cabinet("Программы", "Выбрать «Исследование»", "Описать воспроизводимые шаги", "Отправить на проверку"),
  "gifts-team": cabinet("Программы", "Выбрать «Команда»", "Указать число устройств", "Отправить заявку"),
  "profile-refresh": app("Android / Windows", "Центр защиты", "Открыть восстановление", "Обновить профиль", "Переподключиться"),
};

export const GUIDE_VISUAL_COVERAGE = catalog.guides.map((guide) => ({
  id: guide.id,
  covered: Boolean(GUIDE_VISUALS[guide.id]),
}));

const missingGuideVisuals = GUIDE_VISUAL_COVERAGE.filter(
  (entry) => !entry.covered,
);
if (missingGuideVisuals.length > 0) {
  throw new Error(
    `Guide visuals are missing for: ${missingGuideVisuals
      .map((entry) => entry.id)
      .join(", ")}`,
  );
}
