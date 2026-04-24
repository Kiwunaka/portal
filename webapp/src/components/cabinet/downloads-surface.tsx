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
          title: "Android через Google Play",
          body: "Самый прямой путь, если нужен обычный старт без ручной настройки.",
          badge: "Рекомендуем",
          tone: "success",
          href: androidPlay,
          action: externalAction(androidPlay, "Открыть Google Play"),
        }
      : null,
    androidApk
      ? {
          key: "android-apk",
          title: "Android через APK",
          body: "Подходит, если Play недоступен или удобнее поставить файл вручную.",
          badge: "Дополнительная ссылка",
          tone: "neutral",
          href: androidApk,
          action: externalAction(androidApk, "Скачать APK"),
        }
      : null,
    androidMirror
      ? {
          key: "android-mirror",
          title: "Резервная ссылка для Android",
          body: "Оставили на случай, если основные ссылки сегодня ведут себя неровно.",
          badge: "На всякий случай",
          tone: "info",
          href: androidMirror,
          action: externalAction(androidMirror, "Скачать APK (зеркало)"),
        }
      : null,
    windowsExe
      ? {
          key: "windows-exe",
          title: "Windows",
          body: "Обычная установка для Windows без лишних шагов в кабинете.",
          badge: "Основная ссылка",
          tone: "success",
          href: windowsExe,
          action: externalAction(windowsExe, "Скачать Windows"),
        }
      : null,
    windowsMirror
      ? {
          key: "windows-mirror",
          title: "Резервная ссылка для Windows",
          body: "Нужна только если обычная загрузка временно не открывается.",
          badge: "Дополнительная ссылка",
          tone: "info",
          href: windowsMirror,
          action: externalAction(windowsMirror, "Скачать Windows (зеркало)"),
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
          action: externalAction(docsUrl, "Открыть инструкцию"),
        }
      : null,
    {
      key: "apple-soon",
      title: "Apple",
      body: "Версия для Apple готовится. Сейчас основной путь — Android и Windows.",
      badge: "Готовится",
      tone: "neutral",
    },
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
      } catch {
        if (!cancelled) {
          setError("Не удалось обновить ссылки автоматически.");
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
  const hasInstallable = hasAndroid || hasWindows;
  const primaryInstall = cards.find((item) => item.key === "android-play" || item.key === "android-apk" || item.key === "windows-exe");

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
      description="Только рабочие ссылки и короткие подсказки. Без лишнего текста и ручной настройки на первом шаге."
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
          value: hasAndroid ? "Можно установить" : "Ссылки появятся позже",
          hint: "Play для обычного старта, APK как дополнительная ссылка.",
          tone: hasAndroid ? "success" : "neutral",
        },
        {
          label: "Windows",
          value: hasWindows ? "Можно установить" : "Ссылка появится позже",
          hint: "Обычная установка без ручной сборки профиля.",
          tone: hasWindows ? "success" : "neutral",
        },
        {
          label: "Apple",
          value: "Готовится",
          hint: "Apple-платформы сейчас только в подготовке, без публичной установки.",
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
        badge={hasInstallable ? "Можно ставить приложение" : "Ссылки подтягиваются"}
        badgeTone={hasInstallable ? "success" : "info"}
        title={hasInstallable ? "Сначала загрузка, потом вход" : "Установочные ссылки подтянем позже"}
        description={
          hasInstallable
            ? "Для нового экрана обычно хватает двух шагов: открыть нужную загрузку и войти в тот же аккаунт. Всё остальное уже догружается само."
            : "Кабинет продолжает работать. Если нужной ссылки нет прямо сейчас, лучше открыть поддержку."
        }
        actions={
          <>
            {primaryInstall?.href ? (
              <a href={primaryInstall.href} target="_blank" rel="noreferrer" className="btn-primary rounded-full px-5 py-3 text-sm font-semibold">
                {primaryInstall.key === "android-play" ? "Открыть Google Play" : primaryInstall.key === "android-apk" ? "Скачать APK" : "Скачать Windows"}
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
            value: hasAndroid ? "Android через Play или APK" : hasWindows ? "Установщик Windows" : "Поддержка",
            hint: "Берите обычный путь первым. Дополнительные ссылки нужны редко.",
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
            value: "Открыть поддержку",
            hint: "Быстрее сразу продолжить один кейс в поддержке.",
            tone: error ? "warning" : "neutral",
          },
        ]}
      />

      <div className="grid gap-6 xl:grid-cols-[1.06fr_0.94fr]">
        <CabinetSection
          eyebrow="Платформы"
          title="Куда можно перейти сейчас"
          description="Оставили только то, что реально помогает поставить приложение без шума."
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
