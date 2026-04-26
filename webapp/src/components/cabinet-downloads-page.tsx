"use client";

import AppRouteLink from "@/components/app-route-link";
import { CabinetActionList, CabinetFactGrid, CabinetPage, CabinetSection } from "@/components/cabinet-page";
import { fetchClientApps, type ClientAppsPayload } from "@/lib/api";
import { getPortalPublicConfig } from "@/lib/portal";
import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);

type DownloadCard = {
  key: string;
  title: string;
  body: string;
  badge: string;
  tone: "success" | "warning" | "danger" | "info" | "neutral";
  action: ReactNode;
};

function formatDate(value?: string | null): string {
  if (!value) return "РЈС‚РѕС‡РЅРёРј РїРѕ РјРµСЂРµ РѕР±РЅРѕРІР»РµРЅРёСЏ";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "РЈС‚РѕС‡РЅРёРј РїРѕ РјРµСЂРµ РѕР±РЅРѕРІР»РµРЅРёСЏ";
  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "long",
    hour: "2-digit",
    minute: "2-digit",
  }).format(parsed);
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
          title: "Android В· Google Play",
          body: "РЎР°РјС‹Р№ РїСЂРѕСЃС‚РѕР№ РїСѓС‚СЊ РґР»СЏ РѕР±С‹С‡РЅРѕР№ СѓСЃС‚Р°РЅРѕРІРєРё РЅР° Android.",
          badge: "Р РµРєРѕРјРµРЅРґСѓРµРј",
          tone: "success",
          action: (
            <a href={androidPlay} target="_blank" rel="noreferrer" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
              РћС‚РєСЂС‹С‚СЊ
            </a>
          ),
        }
      : null,
    androidApk
      ? {
          key: "android-apk",
          title: "Android В· APK",
          body: "РџРѕРґС…РѕРґРёС‚, РµСЃР»Рё СѓРґРѕР±РЅРµРµ СѓСЃС‚Р°РЅРѕРІРёС‚СЊ РїСЂРёР»РѕР¶РµРЅРёРµ РІСЂСѓС‡РЅСѓСЋ.",
          badge: "Р—Р°РїР°СЃРЅРѕР№ РїСѓС‚СЊ",
          tone: "neutral",
          action: (
            <a href={androidApk} target="_blank" rel="noreferrer" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
              РЎРєР°С‡Р°С‚СЊ
            </a>
          ),
        }
      : null,
    androidMirror
      ? {
          key: "android-mirror",
          title: "Android В· Р РµР·РµСЂРІРЅР°СЏ СЃСЃС‹Р»РєР°",
          body: "РќСѓР¶РЅР° С‚РѕР»СЊРєРѕ РµСЃР»Рё РѕСЃРЅРѕРІРЅРѕР№ РїСѓС‚СЊ РІСЂРµРјРµРЅРЅРѕ РЅРµСѓРґРѕР±РµРЅ.",
          badge: "РќР° РІСЃСЏРєРёР№ СЃР»СѓС‡Р°Р№",
          tone: "info",
          action: (
            <a href={androidMirror} target="_blank" rel="noreferrer" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
              РћС‚РєСЂС‹С‚СЊ
            </a>
          ),
        }
      : null,
    windowsExe
      ? {
          key: "windows-exe",
          title: "Windows",
          body: "РћСЃРЅРѕРІРЅРѕР№ СѓСЃС‚Р°РЅРѕРІС‰РёРє РґР»СЏ Windows.",
          badge: "РћСЃРЅРѕРІРЅРѕР№ РїСѓС‚СЊ",
          tone: "success",
          action: (
            <a href={windowsExe} target="_blank" rel="noreferrer" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
              РЎРєР°С‡Р°С‚СЊ EXE
            </a>
          ),
        }
      : null,
    windowsMirror
      ? {
          key: "windows-mirror",
          title: "Windows В· Р РµР·РµСЂРІРЅР°СЏ СЃСЃС‹Р»РєР°",
          body: "РџРѕРґС…РѕРґРёС‚, РµСЃР»Рё РѕСЃРЅРѕРІРЅРѕР№ РїСѓС‚СЊ РІСЂРµРјРµРЅРЅРѕ РЅРµРґРѕСЃС‚СѓРїРµРЅ.",
          badge: "Р—Р°РїР°СЃРЅРѕР№ РїСѓС‚СЊ",
          tone: "info",
          action: (
            <a href={windowsMirror} target="_blank" rel="noreferrer" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
              РћС‚РєСЂС‹С‚СЊ
            </a>
          ),
        }
      : null,
    docsUrl
      ? {
          key: "docs",
          title: "РљРѕСЂРѕС‚РєР°СЏ СЃРїСЂР°РІРєР°",
          body: "Р•СЃР»Рё РЅСѓР¶РµРЅ Р±С‹СЃС‚СЂС‹Р№ СЃС‚Р°СЂС‚ РёР»Рё РїРѕРґСЃРєР°Р·РєР° РїРѕ СѓСЃС‚Р°РЅРѕРІРєРµ.",
          badge: "Р•СЃР»Рё РЅСѓР¶РЅР° РїРѕРґСЃРєР°Р·РєР°",
          tone: "neutral",
          action: (
            <a href={docsUrl} target="_blank" rel="noreferrer" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
              РћС‚РєСЂС‹С‚СЊ
            </a>
          ),
        }
      : null,
  ].filter(Boolean) as DownloadCard[];
}

export default function CabinetDownloadsPage() {
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

  const facts = [
    {
      label: "Android",
      value: cards.some((item) => item.key.startsWith("android")) ? "Р•СЃС‚СЊ СЃСЃС‹Р»РєРё" : "РЈС‚РѕС‡РЅСЏРµРј",
      hint: "РћСЃРЅРѕРІРЅРѕР№ РїСѓС‚СЊ вЂ” С‡РµСЂРµР· Google Play, Р·Р°РїР°СЃРЅРѕР№ вЂ” APK.",
      tone: cards.some((item) => item.key === "android-play") ? ("success" as const) : ("neutral" as const),
    },
    {
      label: "Windows",
      value: cards.some((item) => item.key.startsWith("windows")) ? "Р•СЃС‚СЊ СЃСЃС‹Р»РєРё" : "РЈС‚РѕС‡РЅСЏРµРј",
      hint: "РћСЃРЅРѕРІРЅРѕР№ РїСѓС‚СЊ вЂ” С‡РµСЂРµР· EXE-СѓСЃС‚Р°РЅРѕРІС‰РёРє.",
      tone: cards.some((item) => item.key === "windows-exe") ? ("success" as const) : ("neutral" as const),
    },
    {
      label: "РЎРїСЂР°РІРєР°",
      value: cards.some((item) => item.key === "docs") ? "РџРѕРґ СЂСѓРєРѕР№" : "РќРµ РїРѕРєР°Р·Р°РЅР°",
      hint: "РљРѕСЂРѕС‚РєРёРµ РїРѕРґСЃРєР°Р·РєРё РЅР° СЃР»СѓС‡Р°Р№, РµСЃР»Рё РѕРЅРё РЅСѓР¶РЅС‹.",
      tone: "neutral" as const,
    },
    {
      label: "РћР±РЅРѕРІР»РµРЅРѕ",
      value: formatDate(payload?.updated_at),
      hint: "Р•СЃР»Рё РєР°РєР°СЏ-С‚Рѕ СЃСЃС‹Р»РєР° РІРµРґРµС‚ СЃРµР±СЏ СЃС‚СЂР°РЅРЅРѕ, Р»СѓС‡С€Рµ СЃСЂР°Р·Сѓ РѕС‚РєСЂС‹С‚СЊ РїРѕРґРґРµСЂР¶РєСѓ.",
      tone: "neutral" as const,
    },
  ];

  const howToItems = [
    {
      key: "step-1",
      title: "РџРѕСЃС‚Р°РІСЊС‚Рµ РїСЂРёР»РѕР¶РµРЅРёРµ",
      body: "Р’С‹Р±РµСЂРёС‚Рµ Android РёР»Рё Windows Рё РѕС‚РєСЂРѕР№С‚Рµ РїРѕРґС…РѕРґСЏС‰СѓСЋ СЃСЃС‹Р»РєСѓ РІС‹С€Рµ.",
      badge: "РЁР°Рі 1",
      tone: "neutral" as const,
    },
    {
      key: "step-2",
      title: "Р’РѕР№РґРёС‚Рµ РІ С‚РѕС‚ Р¶Рµ Р°РєРєР°СѓРЅС‚",
      body: "РўР°Рє РїСЂРѕС„РёР»СЊ РїРѕРґС‚СЏРЅРµС‚СЃСЏ СЃР°Рј. РќРёС‡РµРіРѕ РІСЂСѓС‡РЅСѓСЋ РєРѕРїРёСЂРѕРІР°С‚СЊ РёР· РєР°Р±РёРЅРµС‚Р° РЅРµ РЅСѓР¶РЅРѕ.",
      badge: "РЁР°Рі 2",
      tone: "neutral" as const,
    },
    {
      key: "step-3",
      title: "Р•СЃР»Рё СѓСЃС‚Р°РЅРѕРІРєР° РёРґРµС‚ РЅРµ С‚Р°Рє, СЃСЂР°Р·Сѓ РѕС‚РєСЂРѕР№С‚Рµ РїРѕРґРґРµСЂР¶РєСѓ",
      body: "Р­С‚Рѕ Р±С‹СЃС‚СЂРµРµ Рё СЃРїРѕРєРѕР№РЅРµРµ, С‡РµРј РёСЃРєР°С‚СЊ РѕР±С…РѕРґРЅРѕР№ РїСѓС‚СЊ РІСЃР»РµРїСѓСЋ.",
      badge: "РЁР°Рі 3",
      tone: "neutral" as const,
      action: (
        <AppRouteLink href="/support/" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
          РџРѕРґРґРµСЂР¶РєР°
        </AppRouteLink>
      ),
    },
  ];

  return (
    <CabinetPage
      eyebrow="Р—Р°РіСЂСѓР·РєРё"
      title="РџСЂРёР»РѕР¶РµРЅРёСЏ Рё Р±С‹СЃС‚СЂС‹Р№ СЃС‚Р°СЂС‚"
      description="Р—РґРµСЃСЊ Р»РµР¶Р°С‚ С‚РѕР»СЊРєРѕ РЅСѓР¶РЅС‹Рµ СЃСЃС‹Р»РєРё РЅР° РїСЂРёР»РѕР¶РµРЅРёСЏ Рё РєРѕСЂРѕС‚РєРёРµ РїРѕРґСЃРєР°Р·РєРё РїРѕ СѓСЃС‚Р°РЅРѕРІРєРµ."
      actions={
        <>
          <AppRouteLink href="/devices/" className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
            РЈСЃС‚СЂРѕР№СЃС‚РІР°
          </AppRouteLink>
          <AppRouteLink href="/support/" className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
            РџРѕРґРґРµСЂР¶РєР°
          </AppRouteLink>
        </>
      }
    >
      <CabinetFactGrid facts={facts} />

      <div className="grid gap-6 xl:grid-cols-[1.08fr_0.92fr]">
        <CabinetSection
          eyebrow="РЎСЃС‹Р»РєРё"
          title="Р§С‚Рѕ РјРѕР¶РЅРѕ РѕС‚РєСЂС‹С‚СЊ РїСЂСЏРјРѕ СЃРµР№С‡Р°СЃ"
          description="РџРѕРєР°Р·С‹РІР°РµРј С‚РѕР»СЊРєРѕ Р¶РёРІС‹Рµ Рё РїРѕРЅСЏС‚РЅС‹Рµ РїСѓС‚Рё."
        >
          <CabinetActionList items={cards} empty="РЎСЃС‹Р»РєРё РїРѕСЏРІСЏС‚СЃСЏ Р·РґРµСЃСЊ РїРѕСЃР»Рµ Р·Р°РіСЂСѓР·РєРё РґР°РЅРЅС‹С…" />
          {error ? <p className="mt-4 text-sm text-amber-700 dark:text-amber-200">РќРµ РІСЃРµ СЃСЃС‹Р»РєРё Р·Р°РіСЂСѓР·РёР»РёСЃСЊ Р°РІС‚РѕРјР°С‚РёС‡РµСЃРєРё: {error}</p> : null}
        </CabinetSection>

        <CabinetSection
          eyebrow="РљР°Рє РґРµР№СЃС‚РІРѕРІР°С‚СЊ"
          title="Р•СЃР»Рё СЃС‚Р°РІРёС‚Рµ РїСЂРёР»РѕР¶РµРЅРёРµ РІРїРµСЂРІС‹Рµ"
          description="Р­С‚РёС… С‚СЂРµС… С€Р°РіРѕРІ РѕР±С‹С‡РЅРѕ РґРѕСЃС‚Р°С‚РѕС‡РЅРѕ."
        >
          <CabinetActionList items={howToItems} />
        </CabinetSection>
      </div>
    </CabinetPage>
  );
}
