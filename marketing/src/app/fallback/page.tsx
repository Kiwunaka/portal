import {
  CircleCheck,
  Clock3,
  ExternalLink,
  Globe2,
  KeyRound,
  Layers3,
  ShieldAlert,
  ShoppingBag,
  Smartphone,
  UserRoundPlus,
} from "lucide-react";

import JsonLd from "../../components/json-ld";
import { PageShell } from "../../components/layout/page-shell";
import { Button } from "../../components/ui/button";
import { buildBreadcrumbJsonLd, buildMarketingMetadata } from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND } from "../../lib/pokrov";
import {
  FALLBACK_CLIENTS,
  TRUST_CATALOG_LAST_VERIFIED,
  TRUST_CATALOG_VERSION,
  USER_GUIDES,
} from "../../../../shared/trust-and-guides";

export const metadata = buildMarketingMetadata(
  "Запасные VPN-клиенты и платформы | POKROV",
  "Матрица POKROV, Hiddify, Happ, v2rayN, v2rayNG, Streisand, V2Box и Shadowrocket с честными уровнями поддержки и аварийной помощью для Apple.",
  { path: "/fallback/" },
);

const APPLE_ACCESS_OPTIONS = [
  {
    id: "apple-account",
    label: "Основной путь · бесплатно",
    name: "Свой Apple Account",
    description:
      "Создайте отдельный личный аккаунт нужного региона по инструкции Apple. Пароль, восстановление и последующие обновления остаются у вас.",
    href: "https://support.apple.com/ru-ru/108647",
    cta: "Открыть инструкцию Apple",
    icon: UserRoundPlus,
    primary: true,
    facts: [
      "Без чужого логина и общего доступа",
      "Регион выбирается при создании",
      "Может понадобиться подтверждение телефона",
    ],
  },
  {
    id: "vanya-vpn",
    label: "Бесплатно · примерно 15 минут",
    name: "VanyaVPN: временный аккаунт",
    description:
      "Официальная iOS-страница конкурента сейчас предлагает получить данные временного американского App Store-аккаунта. VanyaVPN меняет пароль после короткой сессии.",
    href: "https://vanyavpn.app/ios",
    cta: "Получить у VanyaVPN",
    icon: Clock3,
    primary: false,
    facts: [
      "Заявлен отдельный доступ примерно на 15 минут",
      "Разрешено скачивать и другие приложения",
      "POKROV не запрашивал данные и не проверял вход",
    ],
  },
  {
    id: "familypro",
    label: "Бесплатно · общий аккаунт",
    name: "FamilyPro",
    description:
      "Публичная страница общего американского аккаунта. Это быстрый вариант без гарантии: данные и доступность меняются на стороне источника.",
    href: "https://familypro.io/shared-apple-id",
    cta: "Открыть FamilyPro",
    icon: Globe2,
    primary: false,
    facts: [
      "Данные могут меняться без предупреждения",
      "Вход только через профиль App Store",
      "Срок работы и замена не гарантируются",
    ],
  },
  {
    id: "izakstore",
    label: "Бесплатные слоты + подписка",
    name: "iZakStore",
    description:
      "На главной есть обновляемый раздел бесплатных аккаунтов и платный каталог. POKROV не проверял вход и оплату — сначала смотрите наличие и отзывы.",
    href: "https://izakstore.ru/",
    cta: "Проверить iZakStore",
    icon: Layers3,
    primary: false,
    facts: [
      "Бесплатные записи появляются не постоянно",
      "Пробный тариф заявлен от 399 ₽ за 7 дней",
      "Перед оплатой проверьте выдачу в личном кабинете",
    ],
  },
  {
    id: "happ-access",
    label: "Именно Happ · 490 ₽",
    name: "Happ Доступ",
    description:
      "Независимый сервис продаёт инструкцию и сопровождение установки Happ на ваш Apple Account — без выдачи чужого логина.",
    href: "https://happplus.com/",
    cta: "Открыть Happ Доступ",
    icon: Smartphone,
    primary: false,
    facts: [
      "Ссылка и инструкция после оплаты",
      "Заявлен возврат при проблеме на стороне сервиса",
      "Это не официальный представитель Happ",
    ],
  },
  {
    id: "appstops-catalog",
    label: "Нужное приложение · платно",
    name: "AppStops: каталог",
    description:
      "Платный доступ к аккаунту с выбранным приложением. Это отдельный рабочий каталог, а не бесплатная раздача на странице /accounts/.",
    href: "https://appstops.ru/catalog",
    cta: "Открыть каталог AppStops",
    icon: ShoppingBag,
    primary: false,
    facts: [
      "Данные заявлены сразу после оплаты",
      "Срок доступа по этой покупке — 3 дня",
      "Для обновления может понадобиться новая покупка",
    ],
  },
  {
    id: "wokerhome",
    label: "Личный US аккаунт · 1 USDT",
    name: "WokerHome",
    description:
      "Продаёт отдельный американский Apple Account с передачей данных после оплаты. Подходит тем, кому удобна оплата в USDT.",
    href: "https://wokerhome.com/shop/products/55",
    cta: "Открыть WokerHome",
    icon: KeyRound,
    primary: false,
    facts: [
      "Заявлен отдельный, а не общий аккаунт",
      "Оплата в USDT, поддержка продавца — 48 часов",
      "POKROV не проверял покупку и выдачу",
    ],
  },
] as const;

const APPLE_REGION_STEPS = [
  {
    title: "Откройте регион",
    text: "App Store → аватарка в правом верхнем углу → Страна и регион.",
  },
  {
    title: "Выберите Казахстан",
    text: "Нажмите смену страны, выберите Казахстан, а в способах оплаты — None.",
  },
  {
    title: "Заполните поля",
    text: "Короткий пример заполнения из инструкции VanyaVPN:",
    details: [
      "Street — Астана",
      "City / Town — Астана",
      "Region — Pavlodar",
      "Postcode — 101000",
      "Phone — 999 9999999",
    ],
  },
  {
    title: "Нажмите «Готово»",
    text: "Откройте App Store ещё раз, найдите нужный VPN-клиент и установите его как обычное приложение.",
  },
] as const;

function statusLabel(value: string): string {
  if (value === "supported_fallback") return "Поддерживаемый fallback";
  if (value === "best_effort") return "Best effort";
  if (value === "advanced") return "Для опытных";
  if (value === "not_published") return "Не опубликовано";
  return "Бета";
}

export default function FallbackPage() {
  return (
    <PageShell>
      <JsonLd
        data={buildBreadcrumbJsonLd([
          { name: CANONICAL_PLATFORM_BRAND, path: "/" },
          { name: "Запасные клиенты", path: "/fallback/" },
        ])}
      />
      <section className="mx-auto flex max-w-5xl flex-col gap-4 px-4 pt-12 pb-10 sm:px-6 sm:pt-16">
        <span className="text-[0.8125rem] font-semibold tracking-[0.08em] text-brand uppercase">
          Матрица {TRUST_CATALOG_VERSION} · проверено {TRUST_CATALOG_LAST_VERIFIED}
        </span>
        <h1 className="font-display text-[2.25rem] leading-[1.1] font-extrabold tracking-[-0.01em] text-ink">
          Если приложение POKROV недоступно
        </h1>
        <p className="max-w-3xl text-base leading-relaxed text-ink-soft">
          Основной путь — POKROV на Android и Windows. Ниже не список всего, что
          когда-либо открывало VLESS, а практическая матрица популярных клиентов
          с форматом импорта, уровнем проверки и отдельной инструкцией.
        </p>
      </section>

      <section className="mx-auto flex max-w-5xl flex-col gap-4 px-4 pb-16 sm:px-6">
        <div className="overflow-hidden rounded-panel border border-line bg-surface">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[1020px] border-collapse text-left text-sm">
              <thead className="bg-canvas-alt text-ink">
                <tr>
                  <th className="px-4 py-3 font-semibold">Клиент</th>
                  <th className="px-4 py-3 font-semibold">Платформы</th>
                  <th className="px-4 py-3 font-semibold">Импорт</th>
                  <th className="px-4 py-3 font-semibold">Поддержка</th>
                  <th className="px-4 py-3 font-semibold">Аккаунт</th>
                  <th className="px-4 py-3 font-semibold">Гайд</th>
                </tr>
              </thead>
              <tbody>
                {FALLBACK_CLIENTS.map((client) => {
                  const guideId = `fallback-${client.id}`;
                  const hasGuide = USER_GUIDES.some(
                    (guide) => guide.id === guideId,
                  );
                  return (
                    <tr key={client.id} className="border-t border-line align-top">
                    <td className="px-4 py-3">
                      <p className="font-semibold text-ink">{client.title}</p>
                      <p className="mt-1 text-xs font-semibold text-brand">{statusLabel(client.status)}</p>
                    </td>
                    <td className="px-4 py-3 leading-relaxed text-ink-soft">{client.platforms.join(", ")}</td>
                    <td className="px-4 py-3 leading-relaxed text-ink-soft">{client.import}</td>
                    <td className="px-4 py-3 leading-relaxed text-ink-soft">{client.support_tier}</td>
                    <td className="px-4 py-3 leading-relaxed text-ink-soft">{client.account_rule}</td>
                    <td className="px-4 py-3">
                      {hasGuide ? (
                        <a
                          href={`/guides/#${guideId}`}
                          className="inline-flex min-h-11 items-center font-semibold text-brand underline decoration-brand/30 underline-offset-4 hover:decoration-brand"
                        >
                          Открыть
                        </a>
                      ) : (
                        <span className="text-ink-muted">Не требуется</span>
                      )}
                    </td>
                  </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        <div className="mt-6 flex flex-col gap-5">
          <div className="max-w-3xl">
            <h2 className="font-display text-2xl font-bold tracking-[-0.01em] text-ink">
              Как получить iOS-клиент сейчас
            </h2>
            <p className="mt-2 text-[0.9375rem] leading-relaxed text-ink-soft">
              Страницы и условия проверены 23 июля 2026 года. Мы не входили в чужие аккаунты и не проводили
              тестовые оплаты, поэтому отделяем доступную страницу от доказанно работающей выдачи.
            </p>
          </div>

          <section
            id="apple-region"
            className="scroll-mt-24 rounded-panel border border-brand/30 bg-brand-soft p-5 sm:p-6"
            aria-labelledby="apple-region-title"
          >
            <div className="grid gap-6 lg:grid-cols-[minmax(0,0.8fr)_minmax(0,1.45fr)] lg:items-start">
              <div>
                <p className="text-xs font-semibold tracking-[0.06em] text-brand uppercase">
                  Рекомендуем сначала
                </p>
                <h3
                  id="apple-region-title"
                  className="mt-2 font-display text-2xl font-bold tracking-[-0.01em] text-ink"
                >
                  Сменить регион App Store
                </h3>
                <p className="mt-3 text-sm leading-6 text-ink-soft">
                  Короткий сценарий VanyaVPN: подходит, если на балансе App Store нет рублей. Приложение останется на
                  вашем аккаунте и сможет обновляться.
                </p>
                <div className="mt-5 flex flex-col gap-3 sm:flex-row lg:flex-col">
                  <Button
                    href="https://support.apple.com/ru-ru/118283"
                    target="_blank"
                    rel="noreferrer"
                    className="w-full"
                  >
                    Открыть инструкцию Apple
                    <ExternalLink size={17} strokeWidth={1.8} aria-hidden="true" />
                  </Button>
                  <Button
                    href="https://vanyavpn.app/ios"
                    target="_blank"
                    rel="noreferrer"
                    variant="secondary"
                    className="w-full"
                  >
                    Посмотреть пример VanyaVPN
                    <ExternalLink size={17} strokeWidth={1.8} aria-hidden="true" />
                  </Button>
                </div>
              </div>

              <ol className="grid gap-3 sm:grid-cols-2">
                {APPLE_REGION_STEPS.map((step, index) => (
                  <li key={step.title} className="rounded-control border border-line bg-surface p-4">
                    <div className="flex items-start gap-3">
                      <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-brand text-sm font-bold text-white">
                        {index + 1}
                      </span>
                      <div>
                        <h4 className="font-display text-base font-bold text-ink">{step.title}</h4>
                        <p className="mt-1 text-sm leading-5 text-ink-soft">{step.text}</p>
                        {"details" in step ? (
                          <ul className="mt-3 grid gap-1.5 rounded-xl bg-canvas-alt p-3 font-mono text-xs leading-5 text-ink">
                            {step.details.map((detail) => (
                              <li key={detail}>{detail}</li>
                            ))}
                          </ul>
                        ) : null}
                      </div>
                    </div>
                  </li>
                ))}
              </ol>
            </div>

            <p className="mt-5 border-t border-brand/20 pt-4 text-sm leading-6 text-ink-soft">
              Если пункта None нет или смена не проходит, причиной обычно бывают остаток баланса, активная подписка,
              незавершённая покупка или семейный доступ. Apple также может запросить действительные платёжные данные.
            </p>
          </section>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {APPLE_ACCESS_OPTIONS.map((option) => {
              const Icon = option.icon;
              return (
                <article
                  key={option.id}
                  className="flex min-h-full flex-col overflow-hidden rounded-(--radius-card) border border-line border-t-[3px] border-t-brand bg-surface p-6 shadow-soft transition-[transform,box-shadow,border-color] duration-200 ease-(--ease-apple) hover:-translate-y-0.5 hover:border-line-strong hover:shadow-medium motion-reduce:transition-none motion-reduce:hover:translate-y-0"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="text-xs font-semibold tracking-[0.06em] text-brand uppercase">{option.label}</p>
                      <h3 className="mt-2 font-display text-[1.375rem] font-bold text-ink">{option.name}</h3>
                    </div>
                    <span className="flex size-11 shrink-0 items-center justify-center rounded-2xl bg-brand-soft text-brand">
                      <Icon size={21} strokeWidth={1.8} aria-hidden="true" />
                    </span>
                  </div>

                  <p className="mt-4 text-sm leading-6 text-ink-soft">{option.description}</p>

                  <ul className="mt-5 flex flex-col gap-3">
                    {option.facts.map((fact) => (
                      <li key={fact} className="flex items-start gap-2.5 text-sm leading-5 text-ink-soft">
                        <CircleCheck
                          size={17}
                          strokeWidth={1.9}
                          className="mt-0.5 shrink-0 text-brand"
                          aria-hidden="true"
                        />
                        <span>{fact}</span>
                      </li>
                    ))}
                  </ul>

                  <Button
                    href={option.href}
                    target="_blank"
                    rel="noreferrer"
                    variant={option.primary ? "primary" : "secondary"}
                    className="mt-6 w-full"
                  >
                    {option.cta}
                    <ExternalLink size={17} strokeWidth={1.8} aria-hidden="true" />
                  </Button>
                </article>
              );
            })}
          </div>

          <div className="flex flex-col gap-4 rounded-panel border border-line bg-canvas-alt p-5 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-start gap-3">
              <span className="flex size-10 shrink-0 items-center justify-center rounded-2xl bg-surface text-ink-muted">
                <Clock3 size={20} strokeWidth={1.8} aria-hidden="true" />
              </span>
              <div>
                <h3 className="font-display text-base font-bold text-ink">
                  Бесплатная раздача AppStops сейчас неактивна
                </h3>
                <p className="mt-1 text-sm leading-6 text-ink-soft">
                  На странице /accounts/ указано «Нет активного аккаунта» и предлагается ждать новую раздачу.
                  Поэтому мы не считаем её доступным источником — только монитором статуса.
                </p>
              </div>
            </div>
            <Button
              href="https://appstops.ru/accounts/"
              target="_blank"
              rel="noreferrer"
              variant="secondary"
              className="w-full shrink-0 sm:w-auto"
            >
              Проверить статус
              <ExternalLink size={17} strokeWidth={1.8} aria-hidden="true" />
            </Button>
          </div>

          <div className="flex items-start gap-3 rounded-panel border border-line bg-canvas-alt p-4 sm:p-5">
            <ShieldAlert size={20} strokeWidth={1.8} className="mt-0.5 shrink-0 text-brand" aria-hidden="true" />
            <p className="text-sm leading-6 text-ink-soft">
              POKROV не хранит логины и пароли внешних аккаунтов и не отвечает за стороннюю оплату. Общий аккаунт
              используйте только через профиль приложения App Store, не через системные настройки Apple
              Account/iCloud; не добавляйте оплату и выйдите сразу после установки. Доступ, восстановление,
              обновления и замена не гарантируются.
            </p>
          </div>
        </div>

        <div className="flex flex-col gap-2 sm:flex-row">
          <Button href="/guides/" className="w-full sm:w-auto">Открыть инструкции</Button>
          <Button href="/guides/#apple-account" variant="secondary" className="w-full sm:w-auto">
            Инструкция для Apple Account
          </Button>
          <Button href="/install/" variant="secondary" className="w-full sm:w-auto">Скачать POKROV</Button>
        </div>
      </section>
    </PageShell>
  );
}
