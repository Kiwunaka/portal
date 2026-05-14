"use client";

import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";

import AppRouteLink from "@/components/app-route-link";
import { CabinetCardGrid, CabinetHero, CabinetRoute, CabinetSection, type CabinetListItem } from "@/components/cabinet/surface";
import { fetchClientApps, type ClientAppsPayload } from "@/lib/api";
import { getPortalPublicConfig } from "@/lib/portal";

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);

type DownloadCard = CabinetListItem & {
  href?: string;
};

function formatDate(value?: string | null): string {
  if (!value) return "Обновим позже";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "Обновим позже";
  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "long",
    hour: "2-digit",
    minute: "2-digit",
  }).format(parsed);
}

function externalAction(href: string, label: string): ReactNode {
  return (
    <a href={href} target="_blank" rel="noreferrer" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
      {label}
    </a>
  );
}

function buildCards(payload: ClientAppsPayload | null): DownloadCard[] {
  const androidPlay = payload?.android?.play_url || config.androidPlayUrl;
  const androidApk = payload?.android?.apk_url || config.androidApkUrl;
  const androidMirror = payload?.android?.mirror_url || config.androidMirrorUrl;
  const windowsExe = payload?.windows?.exe_url || config.windowsExeUrl;
  const windowsMirror = payload?.windows?.mirror_url || config.windowsMirrorUrl;
  const docsUrl = payload?.docs_url || config.docsUrl;

  return [
    androidPlay
      ? {
          key: "android-play",
          title: "Android бета через Google Play",
          body: "Показываем только если ссылка реально пришла от backend. Публичный Android-релиз закрыт до production signing и физического аудита release-сборки.",
          badge: "Android бета",
          tone: "warning",
          href: androidPlay,
          action: externalAction(androidPlay, "Открыть"),
        }
      : null,
    androidApk
      ? {
          key: "android-apk",
          title: "Android бета через APK",
          body: "Внутренний beta-файл для тестеров. Не публикуем его как массовый путь до production signing и физического аудита release-сборки.",
          badge: "Внутренняя бета",
          tone: "warning",
          href: androidApk,
          action: externalAction(androidApk, "Скачать"),
        }
      : null,
    androidMirror
      ? {
          key: "android-mirror",
          title: "Резервная ссылка для Android",
          body: "Резерв той же beta-сборки. Если обычная ссылка не открывается, лучше написать в поддержку, а не искать обходной путь.",
          badge: "Резерв beta",
          tone: "warning",
          href: androidMirror,
          action: externalAction(androidMirror, "Открыть"),
        }
      : null,
    windowsExe
      ? {
          key: "windows-exe",
          title: "Windows бета",
          body: "Бета-сборка для Windows. Установщик может быть неподписанный, поэтому SmartScreen или системное предупреждение ожидаемы.",
          badge: "Бета-сборка",
          tone: "warning",
          href: windowsExe,
          action: externalAction(windowsExe, "Скачать"),
        }
      : null,
    windowsMirror
      ? {
          key: "windows-mirror",
          title: "Резервная ссылка для Windows",
          body: "Резерв той же beta-сборки. Если Windows предупреждает о неподписанном файле, это известное ограничение публичной беты.",
          badge: "Резерв beta",
          tone: "warning",
          href: windowsMirror,
          action: externalAction(windowsMirror, "Открыть"),
        }
      : null,
    docsUrl
      ? {
          key: "docs",
          title: "Короткая инструкция",
          body: "Если нужен быстрый ориентир по установке и первым шагам, он здесь.",
          badge: "Подсказка",
          tone: "neutral",
          href: docsUrl,
          action: externalAction(docsUrl, "Открыть"),
        }
      : null,
  ].filter(Boolean) as DownloadCard[];
}

export function CabinetDownloadsSurface() {
  const [payload, setPayload] = useState<ClientAppsPayload | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const next = await fetchClientApps();
        if (!cancelled) {
          setPayload(next);
          setError("");
        }
      } catch (nextError) {
        if (!cancelled) {
          setError(String((nextError as { message?: string })?.message || nextError || ""));
        }
      }
    };

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const cards = useMemo(() => buildCards(payload), [payload]);
  const hasAndroid = cards.some((item) => item.key.startsWith("android"));
  const hasWindows = cards.some((item) => item.key.startsWith("windows"));
  const hasDocs = cards.some((item) => item.key === "docs");

  const helperCards: CabinetListItem[] = [
    {
      key: "step-install",
      title: "Поставьте приложение на нужный экран",
      body: "Сначала просто откройте нужную ссылку. Кабинет не должен мешать этому шагу.",
      badge: "Шаг 1",
      tone: "neutral",
      action: hasAndroid || hasWindows ? null : (
        <span className="text-sm font-semibold text-slate-500 dark:text-slate-400">Ссылки появятся</span>
      ),
    },
    {
      key: "step-login",
      title: "Войдите в тот же аккаунт",
      body: "Профиль подтянется сам. Ключи и скрытые настройки вручную искать не нужно.",
      badge: "Шаг 2",
      tone: "neutral",
    },
    {
      key: "step-help",
      title: "Если что-то не пошло, продолжите один кейс",
      body: "Так быстрее и для вас, и для поддержки: весь контекст уже будет рядом.",
      badge: "Шаг 3",
      tone: "neutral",
      action: (
        <AppRouteLink href="/support/" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
          Поддержка
        </AppRouteLink>
      ),
    },
  ];

  return (
    <CabinetRoute
      eyebrow="Загрузки"
      title="Все нужные загрузки под рукой"
      description="Бета-доступ открыт только из кабинета. Показываем реальные ссылки из backend или честно говорим, что их нет."
      actions={
        <>
          <AppRouteLink href="/devices/" className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
            Устройства
          </AppRouteLink>
          <AppRouteLink href="/support/" className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
            Поддержка
          </AppRouteLink>
        </>
      }
      metrics={[
        {
          label: "Android",
          value: hasAndroid ? "Ссылки готовы" : "Подтянем позже",
          hint: "Android остается закрыт до production signing и физического release-build audit.",
          tone: hasAndroid ? "warning" : "neutral",
        },
        {
          label: "Windows",
          value: hasWindows ? "Ссылка готова" : "Подтянем позже",
          hint: "Beta-сборка может содержать неподписанный артефакт и вызвать системное предупреждение.",
          tone: hasWindows ? "warning" : "neutral",
        },
        {
          label: "Инструкция",
          value: hasDocs ? "Под рукой" : "Не обязательна",
          hint: "Короткий ориентир, если нужен спокойный старт.",
          tone: "neutral",
        },
        {
          label: "Обновлено",
          value: formatDate(payload?.updated_at),
          hint: "Если ссылка ведет себя странно, лучше сразу открыть поддержку.",
          tone: error ? "warning" : "neutral",
        },
      ]}
    >
      <CabinetHero
        eyebrow="Что делать сейчас"
        badge={cards.length ? "Бета-доступ" : "Ссылки подтягиваются"}
        badgeTone={cards.length ? "success" : "info"}
        title={cards.length ? "Сначала загрузка, потом вход" : "Часть ссылок подтянем позже"}
        description={
          cards.length
            ? "Для нового экрана обычно хватает двух шагов: открыть нужную бета-загрузку и войти в тот же аккаунт. Всё остальное уже догружается само."
            : "Кабинет продолжает работать. Если нужной ссылки нет прямо сейчас, лучше не искать обходной путь, а открыть поддержку."
        }
        actions={
          <>
            {cards[0]?.href ? (
              <a href={cards[0].href} target="_blank" rel="noreferrer" className="btn-primary rounded-full px-5 py-3 text-sm font-semibold">
                Открыть первую ссылку
              </a>
            ) : null}
            <AppRouteLink href="/support/" className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
              Если нужна помощь
            </AppRouteLink>
          </>
        }
        details={[
          {
            label: "Лучший путь",
            value: hasAndroid ? "Android через Play" : hasWindows ? "Установщик Windows" : "Поддержка",
            hint: "Берите обычный путь первым. Запасные ссылки нужны редко.",
            tone: "neutral",
          },
          {
            label: "После установки",
            value: "Войти в тот же аккаунт",
            hint: "Профиль, режим и история подтянутся сами.",
            tone: "neutral",
          },
          {
            label: "Если что-то не открылось",
            value: "Не искать обходы",
            hint: "Быстрее сразу продолжить один кейс в поддержке.",
            tone: error ? "warning" : "neutral",
          },
        ]}
      />

      <div className="grid gap-6 xl:grid-cols-[1.06fr_0.94fr]">
        <CabinetSection
          eyebrow="Платформы"
          title="Куда можно перейти сейчас"
          description="Оставили только реальные бета-ссылки и честные состояния артефактов."
        >
          <CabinetCardGrid items={cards} className="xl:grid-cols-2" />
          {error ? <p className="mt-4 text-sm text-amber-700 dark:text-amber-200">Часть ссылок не удалось обновить автоматически: {error}</p> : null}
        </CabinetSection>

        <CabinetSection
          eyebrow="Коротко"
          title="Что важно помнить"
          description="Этих трех заметок обычно хватает, чтобы спокойно довести установку до конца."
        >
          <CabinetCardGrid items={helperCards} className="xl:grid-cols-1" />
        </CabinetSection>
      </div>
    </CabinetRoute>
  );
}

export default CabinetDownloadsSurface;
