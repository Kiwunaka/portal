"use client";

import { useEffect, useMemo, useState, useSyncExternalStore } from "react";

import { mintAcquisitionHandoff } from "../../lib/acquisition";
import { CANONICAL_API_BASE_URL } from "../../lib/pokrov";
import {
  approvedReleaseAsset,
  RELEASE_ASSET_NAMES,
  type ReleasePlatform,
} from "../../lib/release-assets";
import { Button } from "../ui/button";

type PublicReleasePayload = {
  android?: { apk_url?: string };
  windows?: { exe_url?: string };
};

function detectPlatform(): ReleasePlatform | null {
  const userAgent = navigator.userAgent.toLowerCase();
  if (userAgent.includes("android")) return "android";
  if (userAgent.includes("windows")) return "windows";
  return null;
}

export function PlatformDownloadAction({
  initialAndroidUrl,
  initialWindowsUrl,
}: {
  initialAndroidUrl: string;
  initialWindowsUrl: string;
}) {
  const initial = useMemo(
    () => ({
      android: approvedReleaseAsset(initialAndroidUrl, RELEASE_ASSET_NAMES.android),
      windows: approvedReleaseAsset(initialWindowsUrl, RELEASE_ASSET_NAMES.windows),
    }),
    [initialAndroidUrl, initialWindowsUrl],
  );
  const platform = useSyncExternalStore(
    () => () => undefined,
    detectPlatform,
    () => null,
  );
  const [downloads, setDownloads] = useState(initial);
  const [continuation, setContinuation] = useState<{ handle: string; platform: ReleasePlatform } | null>(null);

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
        });
      })
      .catch(() => undefined);
    return () => controller.abort();
  }, [initial]);

  const href = platform ? downloads[platform] : "";
  const label =
    platform === "android"
      ? "Скачать на Android"
      : platform === "windows"
        ? "Скачать на Windows"
        : "Скачать POKROV";

  const prepareContinuation = (): void => {
    if (!platform || !href) return;
    const asset = RELEASE_ASSET_NAMES[platform];
    void mintAcquisitionHandoff(`${platform}_install`, asset).then((payload) => {
      if (payload?.handle) setContinuation({ handle: payload.handle, platform });
    });
  };

  return (
    <div className="flex flex-col items-start gap-2">
      <Button
        href={href || "/install/"}
        size="lg"
        target={href ? "_blank" : undefined}
        rel={href ? "noreferrer" : undefined}
        data-pokrov-asset={platform ? RELEASE_ASSET_NAMES[platform] : undefined}
        data-pokrov-platform={platform || undefined}
        data-pokrov-cta="hero_download"
        onClick={prepareContinuation}
      >
        {label}
      </Button>
      {continuation ? (
        <a
          href={`pokrov://acquisition/continue?handle=${encodeURIComponent(continuation.handle)}&purpose=${continuation.platform}_install`}
          className="text-sm font-semibold text-brand no-underline hover:text-brand-strong focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
          data-pokrov-cta="post_install_continue"
        >
          Файл скачан? Продолжить в POKROV
        </a>
      ) : null}
    </div>
  );
}
