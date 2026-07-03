"use client";

import type { TelegramWebLoginPayload } from "@/lib/api";
import { usePortalSession } from "@/lib/session";
import { useEffect, useRef, useState } from "react";

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

function legacyTelegramWidgetEnabled(): boolean {
  return (
    String(process.env.NEXT_PUBLIC_ENABLE_LEGACY_TELEGRAM_WIDGET || process.env.VITE_ENABLE_LEGACY_TELEGRAM_WIDGET || "")
      .trim()
      .toLowerCase() === "true"
  );
}

type TelegramLoginWidgetProps = {
  buttonClassName?: string;
  buttonLabel?: string;
  busyLabel?: string;
  showHint?: boolean;
};

export default function TelegramLoginWidget({
  buttonClassName = "btn-primary w-full rounded-xl px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em]",
  buttonLabel = "Открыть Telegram для входа",
  busyLabel = "Открываем Telegram...",
  showHint = true,
}: TelegramLoginWidgetProps) {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const authDoneRef = useRef(false);
  const legacyWidget = legacyTelegramWidgetEnabled();
  const botSource = String(
    process.env.NEXT_PUBLIC_TELEGRAM_BOT_URL || process.env.VITE_TELEGRAM_BOT_URL || "https://t.me/pokrov_vpnbot",
  ).trim();
  const botName = resolveTelegramBotName(botSource);
  const [widgetHint, setWidgetHint] = useState(() =>
    botName ? "" : "Не удалось подготовить Telegram-вход. Кнопка ниже откроет тот же путь вручную.",
  );
  const { loginByWidget, startTelegramLogin, webLoginBusy } = usePortalSession();

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    let cancelled = false;
    host.innerHTML = "";
    if (!legacyWidget) {
      queueMicrotask(() => {
        if (!cancelled) setWidgetHint("");
      });
      delete window.onTelegramAuth;
      return () => {
        cancelled = true;
      };
    }
    const isLocalHost = ["localhost", "127.0.0.1", "::1"].includes(window.location.hostname);
    if (isLocalHost) {
      queueMicrotask(() => {
        setWidgetHint("Telegram-вход здесь не открылся. Нажмите кнопку ещё раз или войдите по email.");
      });
      delete window.onTelegramAuth;
      return;
    }
    if (!botName) {
      delete window.onTelegramAuth;
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
      setWidgetHint("Виджет Telegram не загрузился. Кнопка выше запускает тот же вход.");
    };
    host.appendChild(script);

    const warnTimer = window.setTimeout(() => {
      if (authDoneRef.current) return;
      setWidgetHint("Если виджет не сработал автоматически, просто нажмите кнопку выше.");
    }, 4500);

    return () => {
      cancelled = true;
      window.clearTimeout(warnTimer);
      host.innerHTML = "";
      delete window.onTelegramAuth;
    };
  }, [botName, legacyWidget, loginByWidget]);

  return (
    <div className="space-y-2">
      <button
        className={buttonClassName}
        disabled={webLoginBusy}
        onClick={() => void startTelegramLogin()}
        type="button"
      >
        {webLoginBusy ? busyLabel : buttonLabel}
      </button>
      {showHint ? (
        <p className="text-xs leading-5 text-[color:var(--atlas-text-soft)]">
          Telegram подтвердит вход и вернет вас обратно в кабинет без лишних экранов.
        </p>
      ) : null}
      <div ref={hostRef} className={legacyWidget ? "min-h-[56px]" : "hidden"} id="tg-login-widget" />
      {legacyWidget && widgetHint ? <p className="text-xs leading-5 text-[color:var(--atlas-status-warning-text)]">{widgetHint}</p> : null}
    </div>
  );
}
