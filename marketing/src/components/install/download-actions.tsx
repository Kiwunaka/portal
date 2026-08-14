"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { CANONICAL_API_BASE_URL } from "../../lib/pokrov";
import { mintAcquisitionHandoff } from "../../lib/acquisition";
import { approvedReleaseAsset, RELEASE_ASSET_NAMES } from "../../lib/release-assets";
import { Button } from "../ui/button";

type PublicReleasePayload = {
  android?: { apk_url?: string };
  windows?: { exe_url?: string };
};

type DownloadState = {
  android: string;
  windows: string;
  loading: boolean;
};

export function DownloadActions({
  initialAndroidUrl,
  initialWindowsUrl,
  releasesHelpHref,
}: {
  initialAndroidUrl: string;
  initialWindowsUrl: string;
  releasesHelpHref: string;
}) {
  const initial = useMemo(
    () => ({
      android: approvedReleaseAsset(initialAndroidUrl, RELEASE_ASSET_NAMES.android),
      windows: approvedReleaseAsset(initialWindowsUrl, RELEASE_ASSET_NAMES.windows),
    }),
    [initialAndroidUrl, initialWindowsUrl],
  );
  const [downloads, setDownloads] = useState<DownloadState>({ ...initial, loading: !initial.android || !initial.windows });
  const [continuation, setContinuation] = useState<{ handle: string; platform: "android" | "windows" } | null>(null);

  const prepareContinuation = (platform: "android" | "windows", asset: string): void => {
    void mintAcquisitionHandoff(platform === "android" ? "android_install" : "windows_install", asset).then((payload) => {
      if (payload?.handle) setContinuation({ handle: payload.handle, platform });
    });
  };

  useEffect(() => {
    const controller = new AbortController();
    void fetch(`${CANONICAL_API_BASE_URL}/api/public/client-apps?channel=beta`, {
      credentials: "omit",
      headers: { Accept: "application/json" },
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) throw new Error("release_catalog_unavailable");
        return (await response.json()) as PublicReleasePayload;
      })
      .then((payload) => {
        setDownloads({
          android:
            approvedReleaseAsset(payload.android?.apk_url || "", RELEASE_ASSET_NAMES.android) || initial.android,
          windows:
            approvedReleaseAsset(payload.windows?.exe_url || "", RELEASE_ASSET_NAMES.windows) || initial.windows,
          loading: false,
        });
      })
      .catch(() => setDownloads((current) => ({ ...current, loading: false })));
    return () => controller.abort();
  }, [initial]);

  return (
    <>
      <div className="flex flex-wrap items-center justify-center gap-3">
        {downloads.android ? (
          <Button
            href={downloads.android}
            size="lg"
            target="_blank"
            rel="noreferrer"
            data-pokrov-asset="pokrov-android-arm64-v8a.apk"
            data-pokrov-platform="android"
            onClick={() => prepareContinuation("android", "pokrov-android-arm64-v8a.apk")}
          >
            Скачать POKROV на Android
          </Button>
        ) : (
          <Button size="lg" disabled aria-label="Android-файл временно недоступен">
            {downloads.loading ? "Проверяем Android-файл…" : "Android-файл временно недоступен"}
          </Button>
        )}
        {downloads.windows ? (
          <Button
            href={downloads.windows}
            size="lg"
            variant="secondary"
            target="_blank"
            rel="noreferrer"
            data-pokrov-asset="pokrov-windows-setup-x64.exe"
            data-pokrov-platform="windows"
            onClick={() => prepareContinuation("windows", "pokrov-windows-setup-x64.exe")}
          >
            Скачать POKROV на Windows
          </Button>
        ) : (
          <Button size="lg" variant="secondary" disabled aria-label="Windows-файл временно недоступен">
            {downloads.loading ? "Проверяем Windows-файл…" : "Windows-файл временно недоступен"}
          </Button>
        )}
      </div>
      {continuation ? (
        <div className="mx-auto flex max-w-2xl flex-col items-center gap-2 rounded-2xl border border-line bg-surface px-4 py-3 text-center shadow-soft">
          <strong className="text-sm text-ink">После установки вернитесь сюда</strong>
          <p className="m-0 text-[0.8125rem] text-ink-soft">
            Продолжение связывает источник с первым запуском. На доступ и работу POKROV это не влияет.
          </p>
          <Button
            href={`pokrov://acquisition/continue?handle=${encodeURIComponent(continuation.handle)}&purpose=${continuation.platform}_install`}
            size="md"
            variant="secondary"
            data-pokrov-cta="post_install_continue"
          >
            Продолжить в POKROV
          </Button>
        </div>
      ) : null}
      <div className="flex flex-col items-center gap-1">
        <p className="m-0 text-[0.8125rem] text-ink-soft">
          {downloads.android || downloads.windows
            ? "Файлы скачиваются напрямую из официального POKROV Releases."
            : "Ссылка не подменяется кабинетом: дождитесь каталога или проверьте Releases."}
        </p>
        <Link
          href={releasesHelpHref}
          className="text-[0.8125rem] font-medium text-brand no-underline hover:text-brand-strong focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
        >
          Файлы и checksums — на GitHub Releases
        </Link>
      </div>
    </>
  );
}
