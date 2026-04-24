"use client";

import { useEffect, useRef, useState } from "react";

import type { TelegramWebLoginPayload } from "@/lib/api";
import { usePortalSession } from "@/lib/session";

declare global {
  interface Window {
    onTelegramAuth?: (user: TelegramWebLoginPayload) => void;
  }
}

function resolveTelegramBotName(raw: string): string {
  const value = String(raw || "").trim();
  if (!value) return "";

  if (/^https?:\/\//i.test(value)) {
    try {
      const url = new URL(value);
      const segment = url.pathname.split("/").filter(Boolean)[0] || "";
      return segment.replace(/^@+/, "").toLowerCase();
    } catch {
      return value
        .replace(/^https?:\/\/t\.me\//i, "")
        .replace(/^@+/, "")
        .split(/[/?#]/)[0]
        .toLowerCase();
    }
  }

  return value.replace(/^@+/, "").split(/[/?#]/)[0].toLowerCase();
}

function isLocalPreviewHost(): boolean {
  if (typeof window === "undefined") return false;
  const host = window.location.hostname.toLowerCase();
  return host === "localhost" || host === "127.0.0.1" || host === "::1";
}

export default function TelegramLoginWidget() {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const authDoneRef = useRef(false);
  const botSource = String(
    process.env.NEXT_PUBLIC_TELEGRAM_BOT_URL || process.env.VITE_TELEGRAM_BOT_URL || "https://t.me/pokrov_vpnbot",
  ).trim();
  const botName = resolveTelegramBotName(botSource);
  const [widgetHint, setWidgetHint] = useState(() =>
    botName ? "" : "Не удалось подготовить Telegram-вход. Основная кнопка откроет тот же путь вручную.",
  );
  const { loginByWidget, startTelegramLogin, webLoginBusy } = usePortalSession();

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    host.innerHTML = "";
    if (!botName) {
      delete window.onTelegramAuth;
      return;
    }
    if (isLocalPreviewHost()) {
      delete window.onTelegramAuth;
      setWidgetHint("В локальном предпросмотре используйте основную кнопку входа выше.");
      return;
    }

    authDoneRef.current = false;

    window.onTelegramAuth = (user: TelegramWebLoginPayload) => {
      authDoneRef.current = true;
      setWidgetHint("");
      void loginByWidget(user);
    };

    const script = document.createElement("script");
    script.async = true;
    script.src = "https://telegram.org/js/telegram-widget.js?22";
    script.setAttribute("data-telegram-login", botName);
    script.setAttribute("data-size", "large");
    script.setAttribute("data-userpic", "false");
    script.setAttribute("data-request-access", "write");
    script.setAttribute("data-radius", "12");
    script.setAttribute("data-lang", "ru");
    script.setAttribute("data-onauth", "onTelegramAuth(user)");
    script.onerror = () => {
      setWidgetHint("Виджет Telegram не загрузился. Основная кнопка запускает тот же вход.");
    };
    host.appendChild(script);

    const warnTimer = window.setTimeout(() => {
      if (authDoneRef.current) return;
      setWidgetHint("Если виджет не сработал автоматически, используйте основную кнопку входа.");
    }, 4500);

    return () => {
      window.clearTimeout(warnTimer);
      host.innerHTML = "";
      delete window.onTelegramAuth;
    };
  }, [botName, loginByWidget]);

  return (
    <div className="space-y-2">
      <button
        className="btn-primary w-full rounded-xl px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em]"
        disabled={webLoginBusy}
        onClick={() => void startTelegramLogin()}
        type="button"
      >
        {webLoginBusy ? "Открываем Telegram..." : "Открыть Telegram для входа"}
      </button>
      <p className="text-xs leading-5 text-slate-500 dark:text-slate-400">
        Telegram подтвердит вход и вернет вас обратно в кабинет без лишних экранов.
      </p>
      <div ref={hostRef} className="min-h-[56px]" id="tg-login-widget" />
      {widgetHint ? <p className="text-xs leading-5 text-amber-600 dark:text-amber-300">{widgetHint}</p> : null}
    </div>
  );
}
