"use client";

import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";

import { icon } from "@/components/cabinet/icon";
import { CabinetGroup, CabinetRow, CabinetStatus } from "@/components/cabinet/surface";
import { Button } from "@/components/cabinet/ui";
import { fetchClientApps, type ClientAppsPayload } from "@/lib/api";
import { getPortalPublicConfig } from "@/lib/portal";

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);

type DownloadRow = {
  key: string;
  icon: string;
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
    <a href={href} target="_blank" rel="noreferrer" className="cab-link">
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
      icon: "android",
      label: variant.abi === "armeabi-v7a" ? "Android для старых устройств" : "Android для новых устройств",
      hint: variant.abi === "armeabi-v7a" ? "ARMv7 · если телефон очень старый" : "ARM64 · основной файл для большинства телефонов",
      value: "APK",
      href: variant.url,
      action: externalAction(variant.url, "Скачать"),
    })),
    !androidVariants.length && androidApk
      ? {
          key: "android-apk",
          icon: "android",
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
          icon: "backup",
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
          icon: "desktop_windows",
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
          icon: "backup",
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
          icon: "description",
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
    <main className="cab-page">
      <CabinetStatus
        title="Загрузки"
        meta={rows.length ? "Публичная бета" : "Файлы подгружаются"}
        body="Скачайте приложение для Android или Windows отсюда, затем войдите в тот же аккаунт."
        tone={rows.length ? "success" : "neutral"}
        emblem={icon("download", "h-7 w-7")}
        action={
          firstDownload?.href ? (
            <a href={firstDownload.href} target="_blank" rel="noreferrer" className="cab-btn cab-btn--primary w-full sm:w-auto">
              Скачать
            </a>
          ) : (
            <Button href="/support/" className="w-full sm:w-auto">
              Поддержка
            </Button>
          )
        }
      />

      <section className="flex flex-col gap-2.5">
        <h2 className="cab-eyebrow px-1">Файлы</h2>
        {primaryRows.length ? (
          <div className="cab-dlgrid">
            {primaryRows.map((item) => (
              <article key={item.key} className="cab-dlcard">
                <div className="cab-dltop">
                  <span className="cab-dlicon" data-platform={item.icon === "desktop_windows" ? "windows" : "android"}>
                    {icon(item.icon, "h-6 w-6")}
                  </span>
                  <span className="cab-dlbadge">{item.value}</span>
                </div>
                <h3 className="cab-dltitle">{item.label}</h3>
                <p className="cab-dlhint">{item.hint}</p>
                {item.href ? (
                  <a href={item.href} target="_blank" rel="noreferrer" className="cab-btn cab-btn--primary cab-btn--block">
                    Скачать
                  </a>
                ) : null}
              </article>
            ))}
          </div>
        ) : (
          <div className="cab-panel">
            <CabinetRow icon={icon("hourglass_empty")} label="Файлы подгружаются" hint="Если срочно, откройте поддержку" href="/support/" />
          </div>
        )}
        {secondaryRows.length ? (
          <div className="cab-panel">
            {secondaryRows.map((item) => (
              <CabinetRow key={item.key} icon={icon(item.icon)} label={item.label} hint={item.hint} value={item.value} action={item.action} />
            ))}
          </div>
        ) : null}
      </section>

      {error ? <p className="px-1 text-sm text-[color:var(--atlas-status-warning-text)]">Часть ссылок не удалось обновить: {error}</p> : null}

      <CabinetGroup title="После скачивания">
        <CabinetRow icon={icon("login")} label="Войти в тот же аккаунт" hint="Профиль подтянется сам" value={hasAndroid || hasWindows ? "важно" : undefined} />
        <CabinetRow icon={icon("devices")} label="Проверить устройство" hint="После входа оно появится в списке" href="/devices/" />
        <CabinetRow icon={icon("support_agent")} label="Поддержка" hint="Если файл не открылся или вход не прошел" href="/support/" />
        <CabinetRow icon={icon("update")} label="Обновлено" hint="По данным страницы загрузок" value={formatDate(payload?.updated_at)} />
      </CabinetGroup>
    </main>
  );
}

export default CabinetDownloadsSurface;
