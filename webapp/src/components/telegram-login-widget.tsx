"use client";

import type { TelegramWebLoginPayload } from "@/lib/api";
import { usePortalSession } from "@/lib/session";
import { useEffect, useRef } from "react";

declare global {
  interface Window {
    onTelegramAuth?: (user: TelegramWebLoginPayload) => void;
  }
}

export default function TelegramLoginWidget() {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const { loginByWidget } = usePortalSession();

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    host.innerHTML = "";

    const botName = (process.env.NEXT_PUBLIC_TELEGRAM_LOGIN_BOT || process.env.VITE_TELEGRAM_LOGIN_BOT || "net4ebur_bot").trim();

    window.onTelegramAuth = (user: TelegramWebLoginPayload) => {
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
    host.appendChild(script);

    return () => {
      host.innerHTML = "";
      delete window.onTelegramAuth;
    };
  }, [loginByWidget]);

  return <div ref={hostRef} className="min-h-[56px]" id="tg-login-widget" />;
}
