import JsonLd from "../../components/json-ld";
import { DownloadActions } from "../../components/install/download-actions";
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

export const metadata = buildMarketingMetadata(
  SEO_PAGE.title,
  SEO_PAGE.description,
  {
    path: "/install/",
  },
);

export default function InstallPage() {
  const facts = getSharedProductFacts();

  const platforms: InstallPlatform[] = [
    {
      id: "android",
      label: getCopyText("marketing.install.tabs.android", "Android"),
      note: getCopyText(
        "marketing.install.android.note",
        "ARM64 подходит большинству телефонов. Старые и универсальные варианты спрятаны в кабинете — выбирать их обычно не нужно.",
      ),
      steps: [
        {
          variant: "download",
          title: getCopyText("marketing.install.android.step1.title", "Скачайте файл"),
          text: getCopyText(
            "marketing.install.android.step1.text",
            "Скачайте рекомендуемый ARM64 APK из официального POKROV Releases. Аккаунт понадобится уже после установки.",
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
            "Скачайте установщик из официального POKROV Releases. Portable-версия доступна в кабинете.",
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
      question: getCopyText("marketing.install.faq.file.q", "Откуда скачивается официальный файл?"),
      answer: getCopyText(
        "marketing.install.faq.file.a",
        "Android APK и Windows-установщик скачиваются из публичного POKROV Releases. Portable-версия Windows доступна в кабинете. Не используйте случайные зеркала и пересланные архивы.",
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
        "Берите ARM64 — он подходит большинству телефонов и заметно меньше universal. Если установка не проходит, откройте «Другие версии» в кабинете: там есть ARMv7 и universal.",
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
        <DownloadActions
          initialAndroidUrl={config.androidApkUrl}
          initialWindowsUrl={config.windowsExeUrl}
          releasesHelpHref={SEO_PAGE_PATHS.trustGithubReleases}
        />
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
