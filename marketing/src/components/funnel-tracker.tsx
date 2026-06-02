"use client";

import { useEffect } from "react";

import { CANONICAL_API_BASE_URL, CANONICAL_WEBAPP_URL } from "../lib/pokrov";

const SESSION_KEY = "pokrov-funnel-session";

function getSessionId(): string {
  try {
    const existing = window.localStorage.getItem(SESSION_KEY);
    if (existing && existing.length >= 8) return existing;
    const next =
      typeof window.crypto?.randomUUID === "function"
        ? window.crypto.randomUUID()
        : `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
    window.localStorage.setItem(SESSION_KEY, next);
    return next;
  } catch {
    return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
  }
}

function sourceFromLocation(params: URLSearchParams): string {
  const utm = params.get("utm_source");
  if (utm) return utm;
  try {
    if (document.referrer) return new URL(document.referrer).hostname.slice(0, 64) || "site";
  } catch {
    return "site";
  }
  return "site";
}

function classifyHref(href: string): { event_name: string; stage: string; channel: string } {
  try {
    const url = new URL(href, window.location.href);
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
    const sessionId = getSessionId();
    const params = new URLSearchParams(window.location.search);
    const source = sourceFromLocation(params);
    const campaign = params.get("utm_campaign") || params.get("campaign") || "";
    sendFunnelEvent({
      event_name: "page_view",
      stage: "site_visit",
      channel: "site",
      source,
      session_id: sessionId,
      path: `${window.location.pathname}${window.location.search || ""}`.slice(0, 512),
      referrer: document.referrer || "",
      campaign,
    });

    const onClick = (event: MouseEvent) => {
      const target = event.target;
      if (!(target instanceof Element)) return;
      const link = target.closest("a[href]");
      if (!(link instanceof HTMLAnchorElement)) return;
      const classified = classifyHref(link.href);
      if (classified.event_name === "cta_click" && !link.href) return;
      sendFunnelEvent({
        ...classified,
        source,
        session_id: sessionId,
        path: `${window.location.pathname}${window.location.search || ""}`.slice(0, 512),
        referrer: document.referrer || "",
        campaign,
        meta: {
          href: link.href.slice(0, 400),
          text: (link.textContent || "").trim().slice(0, 120),
        },
      });
    };

    document.addEventListener("click", onClick, { capture: true });
    return () => document.removeEventListener("click", onClick, { capture: true });
  }, []);

  return null;
}
