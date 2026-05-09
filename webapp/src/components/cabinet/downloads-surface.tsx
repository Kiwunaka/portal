"use client";

import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";

import AppRouteLink from "@/components/app-route-link";
import { CabinetCardGrid, CabinetHero, CabinetRoute, CabinetSection, type CabinetListItem } from "@/components/cabinet/surface";
import { fetchClientApps, type ClientAppsPayload } from "@/lib/api";
import { getPortalPublicConfig } from "@/lib/portal";
import { userFacingErrorMessage } from "@/lib/public-error-messages";

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);

type DownloadCard = CabinetListItem & {
  href?: string;
};

type DownloadPlatform = "android" | "windows" | null;

function normalizeDownloadPlatform(value?: string | null): DownloadPlatform {
  const normalized = String(value || "").trim().toLowerCase();
  if (normalized === "android" || normalized === "apk") return "android";
  if (normalized === "windows" || normalized === "win" || normalized === "exe") return "windows";
  return null;
}

function cardPlatform(card: DownloadCard): DownloadPlatform {
  if (card.key.startsWith("android")) return "android";
  if (card.key.startsWith("windows")) return "windows";
  return null;
}

function prioritizeCards(cards: DownloadCard[], platform: DownloadPlatform): DownloadCard[] {
  if (!platform) return cards;
  return [...cards].sort((left, right) => {
    const leftMatches = cardPlatform(left) === platform;
    const rightMatches = cardPlatform(right) === platform;
    if (leftMatches === rightMatches) return 0;
    return leftMatches ? -1 : 1;
  });
}

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
  const androidApk = payload?.android?.apk_url || "";
  const androidMirror = payload?.android?.mirror_url || "";
  const windowsExe = payload?.windows?.exe_url || "";
  const windowsMirror = payload?.windows?.mirror_url || "";
  const docsUrl = payload?.docs_url || config.docsUrl;

  return [
    androidApk
      ? {
          key: "android-apk",
          title: "Android бета через APK",
          body: "Внутренний бета-файл для тестеров. Не публикуем его как массовый путь до доверенной подписи и физической проверки сборки.",
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
          body: "Резерв той же бета-сборки. Если обычная ссылка не открывается, лучше написать в поддержку, а не искать обходной путь.",
          badge: "Резерв беты",
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
          body: "Резерв той же бета-сборки. Если Windows предупреждает о неподписанном файле, это известное ограничение публичной беты.",
          badge: "Резерв беты",
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
  const [preferredPlatform, setPreferredPlatform] = useState<DownloadPlatform>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    setPreferredPlatform(normalizeDownloadPlatform(params.get("platform")));
  }, []);

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
          setError(userFacingErrorMessage(nextError, "Не удалось обновить ссылки загрузки, показываем сохраненные варианты."));
        }
      }
    };

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const cards = useMemo(() => prioritizeCards(buildCards(payload), preferredPlatform), [payload, preferredPlatform]);
  const hasAndroid = cards.some((item) => item.key.startsWith("android"));
  const hasWindows = cards.some((item) => item.key.startsWith("windows"));
  const hasDocs = cards.some((item) => item.key === "docs");
  const hasDownloadLinks = hasAndroid || hasWindows;
  const firstDownload = cards.find((item) => cardPlatform(item));

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
      title={hasDownloadLinks ? "Все нужные загрузки под рукой" : "Загрузки появятся после финального разрешения"}
      description={
        hasDownloadLinks
          ? "Бета-доступ открыт только из кабинета. Показываем реальные рабочие ссылки или честно говорим, что их нет."
          : "APK и EXE пока не включены в runtime-ссылки. Это нормальный закрытый статус до явного GO на публикацию загрузок."
      }
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
          hint: "Android остается закрыт до доверенной подписи и физической проверки сборки.",
          tone: hasAndroid ? "warning" : "neutral",
        },
        {
          label: "Windows",
          value: hasWindows ? "Ссылка готова" : "Подтянем позже",
          hint: "Бета-сборка может содержать неподписанный артефакт и вызвать системное предупреждение.",
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
        badge={hasDownloadLinks ? "Бета-доступ" : "Ссылки не включены"}
        badgeTone={hasDownloadLinks ? "success" : "info"}
        title={hasDownloadLinks ? "Сначала загрузка, потом вход" : "Часть ссылок подтянем позже"}
        description={
          hasDownloadLinks
            ? "Для нового экрана обычно хватает двух шагов: открыть нужную бета-загрузку и войти в тот же аккаунт. Всё остальное уже догружается само."
            : "Кабинет продолжает работать. Если нужной ссылки нет прямо сейчас, лучше не искать обходной путь, а открыть поддержку."
        }
        actions={
          <>
            {firstDownload?.href ? (
              <a href={firstDownload.href} target="_blank" rel="noreferrer" className="btn-primary rounded-full px-5 py-3 text-sm font-semibold">
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
            value: hasAndroid ? "Android APK" : hasWindows ? "Установщик Windows" : "Поддержка",
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
          description={
            hasDownloadLinks
              ? "Оставили только реальные бета-ссылки и честные состояния артефактов."
              : "Пока доступны только инструкции и поддержка; публичные файлы не подменяем запасными ссылками."
          }
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
