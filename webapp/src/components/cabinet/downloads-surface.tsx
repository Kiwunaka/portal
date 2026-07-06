"use client";

import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";
import {
  Archive,
  Download,
  FileText,
  Hourglass,
  LifeBuoy,
  LogIn,
  MonitorSmartphone,
  RefreshCw,
  Smartphone,
} from "lucide-react";

import { InstructionSteps } from "@/components/cabinet/instructions";
import { StatusHero } from "@/components/cabinet/status-hero";
import { Button } from "@/components/ui/button";
import { GroupedSection, Row } from "@/components/ui/grouped";
import { fetchClientApps, type ClientAppsPayload } from "@/lib/api";
import { getCopyText, getPortalPublicConfig } from "@/lib/portal";

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);

type DownloadRow = {
  key: string;
  icon: LucideIcon;
  platform?: "android" | "windows";
  label: string;
  hint: string;
  value: string;
  href?: string;
  action?: ReactNode;
};

function formatDate(value?: string | null): string {
  if (!value) return "обновим позже";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "обновим позже";
  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "long",
  }).format(parsed);
}

function externalAction(href: string, label: string): ReactNode {
  return (
    <a href={href} target="_blank" rel="noreferrer" className="text-sm font-semibold text-brand hover:text-brand-strong">
      {label}
    </a>
  );
}

function buildRows(payload: ClientAppsPayload | null): DownloadRow[] {
  const androidApk = payload?.android?.apk_url || "";
  const androidVariants = (payload?.android?.apk_variants || []).filter((item) => item.url);
  const androidMirror = payload?.android?.mirror_url || "";
  const windowsExe = payload?.windows?.exe_url || "";
  const windowsMirror = payload?.windows?.mirror_url || "";
  const docsUrl = payload?.docs_url || config.docsUrl;

  return [
    ...androidVariants.map((variant) => ({
      key: `android-${variant.abi || "apk"}`,
      icon: Smartphone,
      platform: "android" as const,
      label: variant.abi === "armeabi-v7a" ? "Android для старых устройств" : "Android для новых устройств",
      hint: variant.abi === "armeabi-v7a" ? "ARMv7 · если телефон очень старый" : "ARM64 · основной файл для большинства телефонов",
      value: "APK",
      href: variant.url,
      action: externalAction(variant.url, "Скачать"),
    })),
    !androidVariants.length && androidApk
      ? {
          key: "android-apk",
          icon: Smartphone,
          platform: "android" as const,
          label: "Приложение для Android",
          hint: "Публичная бета · скачивайте файл только отсюда",
          value: "APK",
          href: androidApk,
          action: externalAction(androidApk, "Скачать"),
        }
      : null,
    androidMirror
      ? {
          key: "android-mirror",
          icon: Archive,
          label: "Резерв Android",
          hint: "Если основная ссылка не открылась",
          value: "резерв",
          href: androidMirror,
          action: externalAction(androidMirror, "Открыть"),
        }
      : null,
    windowsExe
      ? {
          key: "windows-exe",
          icon: MonitorSmartphone,
          platform: "windows" as const,
          label: "Приложение для Windows",
          hint: "Windows может показать предупреждение о неизвестном издателе",
          value: "EXE",
          href: windowsExe,
          action: externalAction(windowsExe, "Скачать"),
        }
      : null,
    windowsMirror
      ? {
          key: "windows-mirror",
          icon: Archive,
          label: "Запасная ссылка для Windows",
          hint: "Если основной файл не скачался",
          value: "резерв",
          href: windowsMirror,
          action: externalAction(windowsMirror, "Открыть"),
        }
      : null,
    docsUrl
      ? {
          key: "docs",
          icon: FileText,
          label: "Короткая инструкция",
          hint: "Если нужна установка с первого раза",
          value: "гайд",
          href: docsUrl,
          action: externalAction(docsUrl, "Открыть"),
        }
      : null,
  ].filter(Boolean) as DownloadRow[];
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

  const rows = useMemo(() => buildRows(payload), [payload]);
  const hasAndroid = rows.some((item) => item.key.startsWith("android"));
  const hasWindows = rows.some((item) => item.key.startsWith("windows"));
  const primaryRows = rows.filter((item) => (item.key.startsWith("android-") && item.key !== "android-mirror") || item.key === "windows-exe");
  const secondaryRows = rows.filter((item) => !primaryRows.includes(item));
  const firstDownload = rows.find((item) => item.key === "android-apk") || rows.find((item) => item.key === "windows-exe") || rows[0] || null;

  return (
    <main className="mx-auto flex w-full max-w-[860px] flex-col gap-5">
      <StatusHero
        title={getCopyText("webapp.downloads.title", "Загрузки")}
        meta={rows.length ? "Публичная бета" : "Файлы подгружаются"}
        body={getCopyText("webapp.downloads.subtitle", "Скачайте приложение для Android или Windows отсюда, затем войдите в тот же аккаунт.")}
        tone={rows.length ? "success" : "neutral"}
        icon={Download}
        action={
          firstDownload?.href ? (
            <Button href={firstDownload.href} target="_blank" rel="noreferrer" className="w-full sm:w-auto">
              Скачать
            </Button>
          ) : (
            <Button href="/support/" className="w-full sm:w-auto">
              Поддержка
            </Button>
          )
        }
      />

      <section className="flex flex-col gap-2.5">
        <h2 className="px-1 text-xs font-bold tracking-[0.08em] text-ink-muted uppercase">Файлы</h2>
        {primaryRows.length ? (
          <div className="grid gap-3 sm:grid-cols-2">
            {primaryRows.map((item) => {
              const Icon = item.icon;
              return (
                <article key={item.key} className="flex flex-col gap-3 rounded-card border border-line bg-surface p-4 shadow-soft">
                  <div className="flex items-center justify-between">
                    <span className="grid size-11 place-items-center rounded-[12px] bg-brand-soft text-brand">
                      <Icon size={22} strokeWidth={1.9} aria-hidden="true" />
                    </span>
                    <span className="rounded-full bg-neutral-bg px-2.5 py-0.5 text-xs font-bold text-neutral-text uppercase">
                      {item.value}
                    </span>
                  </div>
                  <div className="flex-1">
                    <h3 className="text-sm font-semibold text-ink">{item.label}</h3>
                    <p className="mt-1 text-[13px] leading-5 text-ink-soft">{item.hint}</p>
                  </div>
                  {item.href ? (
                    <Button href={item.href} target="_blank" rel="noreferrer" block>
                      Скачать
                    </Button>
                  ) : null}
                </article>
              );
            })}
          </div>
        ) : (
          <GroupedSection>
            <Row icon={Hourglass} label="Файлы подгружаются" hint="Если срочно, откройте поддержку" href="/support/" />
          </GroupedSection>
        )}
        {secondaryRows.length ? (
          <GroupedSection>
            {secondaryRows.map((item) => (
              <Row key={item.key} icon={item.icon} label={item.label} hint={item.hint} value={item.value} action={item.action} />
            ))}
          </GroupedSection>
        ) : null}
      </section>

      {error ? <p className="px-1 text-sm text-warn-text">Часть ссылок не удалось обновить: {error}</p> : null}

      <section className="flex flex-col gap-2.5">
        <h2 className="px-1 text-xs font-bold tracking-[0.08em] text-ink-muted uppercase">Как подключиться за 3 шага</h2>
        <InstructionSteps
          steps={[
            {
              art: "download",
              title: "Скачайте и установите",
              description: "Файл для Android или Windows выше на этой странице. Другие источники лучше не использовать.",
            },
            {
              art: "login",
              title: "Войдите в тот же аккаунт",
              description: "Почта или Telegram — тем же способом, что и здесь. Доступ подтянется сам.",
            },
            {
              art: "connect",
              title: "Нажмите «Подключить»",
              description: "Одна кнопка в приложении. Настраивать ничего не нужно.",
            },
          ]}
        />
      </section>

      <GroupedSection title="После скачивания">
        <Row icon={LogIn} label="Войти в тот же аккаунт" hint="Профиль подтянется сам" value={hasAndroid || hasWindows ? "важно" : undefined} />
        <Row icon={MonitorSmartphone} label="Проверить устройство" hint="После входа оно появится в списке" href="/devices/" />
        <Row icon={LifeBuoy} label="Поддержка" hint="Если файл не открылся или вход не прошел" href="/support/" />
        <Row icon={RefreshCw} label="Обновлено" hint="По данным страницы загрузок" value={formatDate(payload?.updated_at)} />
      </GroupedSection>
    </main>
  );
}

export default CabinetDownloadsSurface;
