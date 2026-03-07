"use client";

import type { TelegramWebLoginPayload } from "@/lib/api";
import { usePortalSession } from "@/lib/session";
import { useEffect, useRef, useState } from "react";

declare global {
  interface Window {
    onTelegramAuth?: (user: TelegramWebLoginPayload) => void;
  }
}

export default function TelegramLoginWidget() {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const authDoneRef = useRef(false);
  const [widgetHint, setWidgetHint] = useState("");
  const { loginByWidget } = usePortalSession();

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    host.innerHTML = "";

    const rawBot = String(process.env.NEXT_PUBLIC_TELEGRAM_LOGIN_BOT || process.env.VITE_TELEGRAM_LOGIN_BOT || "")
      .trim()
      .replace(/^@+/, "")
      .toLowerCase();
    const botName = rawBot;
    if (!botName) {
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
    script.setAttribute("data-onauth", "onTelegramAuth(user)");
    script.onerror = () => {
      setWidgetHint("Не удалось открыть Telegram-виджет. Используйте кнопку входа через Telegram ниже.");
    };
    host.appendChild(script);

    const warnTimer = window.setTimeout(() => {
      if (authDoneRef.current) return;
      setWidgetHint("Если виджет не подтверждает вход, продолжите через Telegram кнопкой ниже.");
    }, 4500);

    return () => {
      window.clearTimeout(warnTimer);
      host.innerHTML = "";
      delete window.onTelegramAuth;
    };
  }, [loginByWidget]);

  return (
    <div className="space-y-2">
      <div ref={hostRef} className="min-h-[56px]" id="tg-login-widget" />
      {widgetHint ? <p className="text-xs text-amber-500">{widgetHint}</p> : null}
    </div>
  );
}
