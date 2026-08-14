"use client";

import { useEffect } from "react";

import { attributionEventFields, getAcquisitionContext } from "../lib/acquisition";
import { CANONICAL_API_BASE_URL, CANONICAL_WEBAPP_URL } from "../lib/pokrov";

function classifyHref(link: HTMLAnchorElement): { event_name: string; stage: string; channel: string; meta?: Record<string, string> } {
  try {
    const url = new URL(link.href, window.location.href);
    const asset = link.dataset.pokrovAsset || "";
    if (asset) {
      return {
        event_name: "download_click",
        stage: "download",
        channel: "marketing",
        meta: { asset, platform: link.dataset.pokrovPlatform || "" },
      };
    }
    const webappHost = new URL(CANONICAL_WEBAPP_URL).hostname;
    if (url.pathname.startsWith("/checkout") || url.hostname.includes("pay.pokrov.space")) {
      return { event_name: "checkout_start", stage: "checkout_start", channel: "checkout" };
    }
    if (url.pathname.startsWith("/install") || url.pathname.startsWith("/devices") || url.pathname.startsWith("/mobile")) {
      return { event_name: "install_opened", stage: "install_intent", channel: "site" };
    }
    if (url.hostname === webappHost) {
      return { event_name: "cabinet_open_intent", stage: "cabinet_intent", channel: "site" };
    }
    if (url.hostname === "t.me" || url.hostname === "telegram.me") {
      return { event_name: "bot_open_intent", stage: "bot_intent", channel: "site" };
    }
  } catch {
    return { event_name: "cta_click", stage: "site_visit", channel: "site" };
  }
  return { event_name: "cta_click", stage: "site_visit", channel: "site" };
}

function sendFunnelEvent(payload: {
  event_name: string;
  stage: string;
  channel: string;
  source: string;
  session_id: string;
  path: string;
  referrer?: string;
  campaign?: string;
  utm_content?: string;
  ref?: string;
  entry_route?: string;
  meta?: Record<string, unknown>;
}): void {
  const url = `${CANONICAL_API_BASE_URL}/api/funnel/events`;
  const body = JSON.stringify(payload);
  try {
    if (navigator.sendBeacon) {
      const blob = new Blob([body], { type: "application/json" });
      if (navigator.sendBeacon(url, blob)) return;
    }
  } catch {
    // fall back to fetch
  }
  void fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
    keepalive: true,
  }).catch(() => undefined);
}

export default function FunnelTracker() {
  useEffect(() => {
    if (process.env.NEXT_PUBLIC_DISABLE_FUNNEL === "1") return;

    const acquisition = getAcquisitionContext();
    const attribution = attributionEventFields(acquisition);
    sendFunnelEvent({
      event_name: "page_view",
      stage: "site_visit",
      channel: "site",
      ...attribution,
      path: window.location.pathname,
    });

    const onClick = (event: MouseEvent) => {
      const target = event.target;
      if (!(target instanceof Element)) return;
      const link = target.closest("a[href]");
      if (!(link instanceof HTMLAnchorElement)) return;
      const classified = classifyHref(link);
      if (classified.event_name === "cta_click" && !link.href) return;
      sendFunnelEvent({
        ...classified,
        ...attribution,
        path: window.location.pathname,
        meta: classified.meta || {
          cta_id: link.dataset.pokrovCta || new URL(link.href, window.location.href).pathname.slice(0, 64),
        },
      });
    };

    document.addEventListener("click", onClick, { capture: true });
    return () => document.removeEventListener("click", onClick, { capture: true });
  }, []);

  return null;
}
