import Link from "next/link";

import JsonLd from "../../components/json-ld";
import { PlatformTabs, type InstallPlatform } from "../../components/install/platform-tabs";
import { PageShell } from "../../components/layout/page-shell";
import { Reveal } from "../../components/motion/reveal";
import { Accordion, type AccordionItem } from "../../components/ui/accordion";
import { Button } from "../../components/ui/button";
import { Chip } from "../../components/ui/chip";
import { SectionHeading } from "../../components/ui/section-heading";
import {
  buildBreadcrumbJsonLd,
  buildFaqJsonLd,
  buildHowToJsonLd,
  buildMarketingMetadata,
  buildWebPageJsonLd,
} from "../../lib/marketing-site";
import {
  CANONICAL_PLATFORM_BRAND,
  getCopyText,
  getPokrovPublicConfig,
  getSharedProductFacts,
} from "../../lib/pokrov";
import { getSeoPage, SEO_PAGE_PATHS } from "../../lib/seo-pages";

const config = getPokrovPublicConfig(process.env as Record<string, string | undefined>);
const SEO_PAGE = getSeoPage("/install/");

function buildCabinetDownloadsHref(platform: "android" | "windows"): string {
  const url = new URL(config.webappUrl);
  url.pathname = "/downloads/";
  url.searchParams.set("platform", platform);
  return url.toString();
}

export const metadata = buildMarketingMetadata(
  SEO_PAGE.title,
  SEO_PAGE.description,
  {
    path: "/install/",
  },
);

export default function InstallPage() {
  const facts = getSharedProductFacts();
  const androidHref = buildCabinetDownloadsHref("android");
  const windowsHref = buildCabinetDownloadsHref("windows");

  const platforms: InstallPlatform[] = [
    {
      id: "android",
      label: getCopyText("marketing.install.tabs.android", "Android"),
      note: getCopyText(
        "marketing.install.android.note",
        "Для большинства телефонов подходит основной файл (arm64). Для старых устройств в кабинете есть отдельная legacy-версия.",
      ),
      steps: [
        {
          variant: "download",
          title: getCopyText("marketing.install.android.step1.title", "Скачайте файл"),
          text: getCopyText(
            "marketing.install.android.step1.text",
            "Откройте кабинет. Он выдаст актуальный APK для вашего аккаунта.",
          ),
        },
        {
          variant: "android-permission",
          title: getCopyText("marketing.install.android.step2.title", "Разрешите установку"),
          text: getCopyText(
            "marketing.install.android.step2.text",
            "Android спросит разрешение на установку из этого источника. Нажмите «Разрешить». Так система относится к любым файлам вне магазина.",
          ),
        },
        {
          variant: "connect",
          title: getCopyText("marketing.install.android.step3.title", "Нажмите «Подключить»"),
          text: getCopyText(
            "marketing.install.android.step3.text",
            `Откройте приложение и нажмите кнопку. ${facts.trial.days} бесплатных дней стартуют сами, карта не нужна.`,
          ),
        },
      ],
    },
    {
      id: "windows",
      label: getCopyText("marketing.install.tabs.windows", "Windows"),
      note: getCopyText(
        "marketing.install.windows.note",
        "Приложение пока распространяется вне магазина и без подписи издателя, поэтому предупреждение SmartScreen ожидаемо.",
      ),
      steps: [
        {
          variant: "download",
          title: getCopyText("marketing.install.windows.step1.title", "Скачайте установщик"),
          text: getCopyText(
            "marketing.install.windows.step1.text",
            "Откройте кабинет. Он выдаст актуальный EXE-файл для вашего аккаунта.",
          ),
        },
        {
          variant: "windows-smartscreen",
          title: getCopyText("marketing.install.windows.step2.title", "Пройдите SmartScreen"),
          text: getCopyText(
            "marketing.install.windows.step2.text",
            "Если Windows покажет предупреждение, нажмите «Подробнее» → «Выполнить в любом случае». Подписи издателя пока нет, поэтому скачивайте файл только через официальный кабинет.",
          ),
        },
        {
          variant: "connect",
          title: getCopyText("marketing.install.windows.step3.title", "Нажмите «Подключить»"),
          text: getCopyText(
            "marketing.install.windows.step3.text",
            `Запустите приложение и нажмите кнопку. ${facts.trial.days} бесплатных дней стартуют сами.`,
          ),
        },
      ],
    },
  ];

  const faqItems: AccordionItem[] = [
    {
      question: getCopyText("marketing.install.faq.file.q", "Почему файл выдаётся через кабинет?"),
      answer: getCopyText(
        "marketing.install.faq.file.a",
        "Кабинет всегда показывает актуальную версию для вашего аккаунта и не даёт скачать подделку с чужого «зеркала». Сами релизы открыто лежат на GitHub Releases.",
      ),
    },
    {
      question: getCopyText("marketing.install.faq.smartscreen.q", "Windows ругается на файл, это нормально?"),
      answer: getCopyText(
        "marketing.install.faq.smartscreen.a",
        "Да. Пока приложение распространяется вне магазина и без подписи издателя, SmartScreen показывает стандартное предупреждение. Нажмите «Подробнее» → «Выполнить в любом случае».",
      ),
    },
    {
      question: getCopyText("marketing.install.faq.apk.q", "Какой APK выбрать на Android?"),
      answer: getCopyText(
        "marketing.install.faq.apk.a",
        "Основной файл (arm64) подходит почти всем современным телефонам. Если телефон старый и файл не ставится, возьмите в кабинете legacy-версию (armeabi).",
      ),
    },
    {
      question: getCopyText("marketing.install.faq.stuck.q", "Не получается, куда идти?"),
      answer: getCopyText(
        "marketing.install.faq.stuck.a",
        "Напишите в Telegram-поддержку: подскажем по шагам от установки до первого подключения. Живой человек, не бот-заглушка.",
      ),
    },
  ];

  return (
    <PageShell>
      <JsonLd
        data={buildBreadcrumbJsonLd([
          { name: CANONICAL_PLATFORM_BRAND, path: "/" },
          { name: "Установка", path: "/install/" },
        ])}
      />
      <JsonLd data={buildFaqJsonLd(faqItems.map((item) => ({ question: item.question, answer: String(item.answer) })))} />
      <JsonLd data={buildWebPageJsonLd(SEO_PAGE)} />
      {SEO_PAGE.steps?.length ? <JsonLd data={buildHowToJsonLd(SEO_PAGE)} /> : null}

      <section className="mx-auto flex max-w-3xl flex-col items-center gap-6 px-4 pt-12 pb-10 text-center sm:px-6 sm:pt-16">
        <Chip>
          <span className="size-1.5 rounded-full bg-status-green" />
          {getCopyText("marketing.install.kicker", "Одна минута до первого подключения")}
        </Chip>
        <h1 className="font-display text-[2.25rem] leading-[1.1] font-extrabold tracking-[-0.01em] text-ink sm:text-[2.75rem]">
          {getCopyText("marketing.install.title", "Скачайте POKROV. Подключитесь одной кнопкой.")}
        </h1>
        <p className="max-w-xl text-lg leading-relaxed text-ink-soft">
          {getCopyText(
            "marketing.install.subtitle",
            "Выберите Android или Windows, скачайте официальный файл и нажмите «Подключить». После установки получите 5 дней бесплатно — карта не нужна.",
          )}
        </p>
        <div className="flex flex-wrap items-center justify-center gap-3">
          <Button href={androidHref} size="lg" target="_blank" rel="noreferrer">
            {getCopyText("marketing.install.cta.android", "Скачать POKROV на Android")}
          </Button>
          <Button href={windowsHref} size="lg" variant="secondary" target="_blank" rel="noreferrer">
            {getCopyText("marketing.install.cta.windows", "Скачать POKROV на Windows")}
          </Button>
        </div>
        <div className="flex flex-col items-center gap-1">
          <p className="m-0 text-[0.8125rem] text-ink-soft">
            {getCopyText("marketing.install.cta.note", "Файл выдаст кабинет — откроется в новой вкладке.")}
          </p>
          <Link
            href={SEO_PAGE_PATHS.trustGithubReleases}
            className="text-[0.8125rem] font-medium text-brand no-underline hover:text-brand-strong focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
          >
            {getCopyText("marketing.install.cta.releases_link", "Файлы и checksums — на GitHub Releases")}
          </Link>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 pb-16 sm:px-6 sm:pb-20">
        <Reveal>
          <PlatformTabs platforms={platforms} />
        </Reveal>
      </section>

      <section className="border-t border-line bg-canvas-alt">
        <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 sm:py-20">
          <Reveal>
            <SectionHeading
              kicker={getCopyText("marketing.install.faq.kicker", "Частые вопросы")}
              title={getCopyText("marketing.install.faq.title", "Ответы перед установкой")}
            />
          </Reveal>
          <Reveal>
            <Accordion items={faqItems} />
          </Reveal>
          <Reveal className="mt-8 flex flex-wrap items-center justify-center gap-4">
            <Button href={SEO_PAGE_PATHS.installAndroid} variant="secondary">
              Android-гайд
            </Button>
            <Button href={SEO_PAGE_PATHS.installWindows} variant="secondary">
              Windows-гайд
            </Button>
            <Button href={config.supportTelegramUrl} variant="secondary" target="_blank" rel="noreferrer">
              {getCopyText("marketing.install.secondary_cta", "Помогите установить")}
            </Button>
            <Button href={config.webappUrl} variant="ghost" target="_blank" rel="noreferrer">
              {getCopyText("marketing.install.primary_cta", "Скачать актуальную версию")}
            </Button>
          </Reveal>
        </div>
      </section>
    </PageShell>
  );
}
