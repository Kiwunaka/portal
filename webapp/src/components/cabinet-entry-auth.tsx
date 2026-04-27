"use client";

import { pokrovBranding } from "@/app/branding";
import AppRouteLink from "@/components/app-route-link";
import TelegramLoginWidget from "@/components/telegram-login-widget";
import {
  finishEmailRecovery,
  getEmailAuthStatus,
  loginByEmail,
  registerByEmail,
  setWebSessionToken,
  startEmailRecovery,
  verifyEmailToken,
} from "@/lib/api";
import { getPortalPublicConfig } from "@/lib/portal";
import { usePortalSession } from "@/lib/session";
import { useEffect, useState, type FormEvent } from "react";

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);

export default function CabinetEntryAuth({ siteUrl }: { siteUrl: string }) {
  const { logoutWebSession, webLoginBusy, webLoginError } = usePortalSession();
  const [emailReady, setEmailReady] = useState(false);
  const [emailMode, setEmailMode] = useState<"login" | "register" | "verify" | "recover">("login");
  const [emailBusy, setEmailBusy] = useState(false);
  const [emailMessage, setEmailMessage] = useState("");
  const [emailError, setEmailError] = useState("");
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [token, setToken] = useState("");
  const [newPassword, setNewPassword] = useState("");

  useEffect(() => {
    let cancelled = false;
    void getEmailAuthStatus()
      .then((payload) => {
        if (!cancelled) setEmailReady(Boolean(payload.enabled));
      })
      .catch(() => {
        if (!cancelled) setEmailReady(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const completeEmailLogin = (nextToken?: string | null): void => {
    if (!nextToken) {
      setEmailError("Email session token is missing.");
      return;
    }
    setWebSessionToken(nextToken);
    if (typeof window !== "undefined") {
      window.location.replace("/");
    }
  };

  const runEmailAction = async (action: () => Promise<void>): Promise<void> => {
    setEmailBusy(true);
    setEmailError("");
    setEmailMessage("");
    try {
      await action();
    } catch (error) {
      setEmailError(String((error as { message?: string })?.message || error || "Email action failed."));
    } finally {
      setEmailBusy(false);
    }
  };

  const submitLogin = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    await runEmailAction(async () => {
      const payload = await loginByEmail({ email, password });
      completeEmailLogin(payload.token);
    });
  };

  const submitRegister = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    await runEmailAction(async () => {
      const payload = await registerByEmail({ email, password, display_name: displayName || undefined });
      setEmailMessage(
        payload?.delivery?.status === "sent"
          ? "Verification email sent."
          : "Account created. Enter the verification token from the email.",
      );
      setEmailMode("verify");
    });
  };

  const submitVerify = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    await runEmailAction(async () => {
      const payload = await verifyEmailToken({ token });
      completeEmailLogin(payload.token);
    });
  };

  const submitRecovery = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    await runEmailAction(async () => {
      if (!token) {
        await startEmailRecovery({ email });
        setEmailMessage("Reset email sent. Enter the reset token and new password.");
        return;
      }
      const payload = await finishEmailRecovery({ token, password: newPassword || password });
      completeEmailLogin(payload.token);
    });
  };

  const inputClass =
    "w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-emerald-400 dark:border-white/10 dark:bg-white/[0.04]";

  return (
    <div className="space-y-5">
      <div className="rounded-[1.5rem] border border-emerald-200/70 bg-emerald-50/90 p-5 dark:border-emerald-400/20 dark:bg-emerald-400/10">
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-emerald-800 dark:text-emerald-200">
          Основной вход
        </p>
        <h3 className="mt-2 text-xl font-semibold text-slate-950 dark:text-slate-50">
          Telegram подтверждает кабинет
        </h3>
        <p className="mt-2 text-sm leading-6 text-slate-700 dark:text-slate-200">
          Нажмите кнопку, подтвердите вход в Telegram, и мы вернем вас сюда с тем же профилем. Это путь продолжения, а не новая регистрация.
        </p>
        <div className="mt-4">
          <TelegramLoginWidget />
        </div>
        {webLoginError ? (
          <div className="mt-4 rounded-2xl border border-rose-200/70 bg-rose-50/85 px-4 py-3 text-sm leading-6 text-rose-700 dark:border-rose-400/20 dark:bg-rose-400/10 dark:text-rose-200">
            {webLoginError}
          </div>
        ) : null}
      </div>

      <div className="rounded-[1.5rem] border border-slate-200/80 bg-slate-50/90 p-5 dark:border-white/10 dark:bg-white/[0.04]">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">
              Email
            </p>
            <h3 className="mt-2 text-xl font-semibold text-slate-950 dark:text-slate-50">
              {emailReady ? "Email-вход" : "Готовим аккуратно"}
            </h3>
          </div>
          <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-600 dark:border-white/10 dark:bg-white/[0.05] dark:text-slate-300">
            {emailReady ? "Готово" : "Скоро"}
          </span>
        </div>

        {emailReady ? (
          <div className="mt-4 space-y-4">
            <div className="flex flex-wrap gap-2">
              {(["login", "register", "verify", "recover"] as const).map((mode) => (
                <button
                  key={mode}
                  type="button"
                  onClick={() => {
                    setEmailMode(mode);
                    setEmailError("");
                    setEmailMessage("");
                  }}
                  className={`rounded-full border px-3 py-2 text-xs font-semibold uppercase tracking-[0.12em] ${
                    emailMode === mode
                      ? "border-emerald-400 bg-emerald-100 text-emerald-900 dark:border-emerald-300/40 dark:bg-emerald-400/15 dark:text-emerald-100"
                      : "border-slate-200 bg-white text-slate-600 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-300"
                  }`}
                >
                  {mode}
                </button>
              ))}
            </div>

            {emailMode === "login" ? (
              <form className="space-y-3" onSubmit={submitLogin}>
                <input className={inputClass} value={email} onChange={(event) => setEmail(event.target.value)} type="email" placeholder="email@example.com" required />
                <input className={inputClass} value={password} onChange={(event) => setPassword(event.target.value)} type="password" placeholder="Password" required />
                <button type="submit" disabled={emailBusy} className="btn-primary rounded-2xl px-5 py-3 text-sm font-semibold disabled:opacity-60">
                  Sign in
                </button>
              </form>
            ) : null}

            {emailMode === "register" ? (
              <form className="space-y-3" onSubmit={submitRegister}>
                <input className={inputClass} value={email} onChange={(event) => setEmail(event.target.value)} type="email" placeholder="email@example.com" required />
                <input className={inputClass} value={displayName} onChange={(event) => setDisplayName(event.target.value)} placeholder="Name" />
                <input className={inputClass} value={password} onChange={(event) => setPassword(event.target.value)} type="password" placeholder="Password" required />
                <button type="submit" disabled={emailBusy} className="btn-primary rounded-2xl px-5 py-3 text-sm font-semibold disabled:opacity-60">
                  Create account
                </button>
              </form>
            ) : null}

            {emailMode === "verify" ? (
              <form className="space-y-3" onSubmit={submitVerify}>
                <input className={inputClass} value={token} onChange={(event) => setToken(event.target.value)} placeholder="Verification token" required />
                <button type="submit" disabled={emailBusy} className="btn-primary rounded-2xl px-5 py-3 text-sm font-semibold disabled:opacity-60">
                  Verify
                </button>
              </form>
            ) : null}

            {emailMode === "recover" ? (
              <form className="space-y-3" onSubmit={submitRecovery}>
                <input className={inputClass} value={email} onChange={(event) => setEmail(event.target.value)} type="email" placeholder="email@example.com" required />
                <input className={inputClass} value={token} onChange={(event) => setToken(event.target.value)} placeholder="Reset token" />
                <input className={inputClass} value={newPassword} onChange={(event) => setNewPassword(event.target.value)} type="password" placeholder="New password" />
                <button type="submit" disabled={emailBusy} className="btn-primary rounded-2xl px-5 py-3 text-sm font-semibold disabled:opacity-60">
                  {token ? "Reset and sign in" : "Send reset email"}
                </button>
              </form>
            ) : null}

            {emailMessage ? <p className="text-sm leading-6 text-emerald-700 dark:text-emerald-200">{emailMessage}</p> : null}
            {emailError ? <p className="text-sm leading-6 text-rose-700 dark:text-rose-200">{emailError}</p> : null}
          </div>
        ) : (
          <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
            Email-вход появится после готовности доставки писем. Сейчас для браузера используйте Telegram или напишите в поддержку, если доступ нужно восстановить вручную.
          </p>
        )}
      </div>

      {webLoginBusy ? (
        <p className="text-xs leading-5 text-slate-500 dark:text-slate-400">
          Открываем Telegram. Если окно уже появилось, завершите вход там и вернитесь в эту вкладку.
        </p>
      ) : null}

      <div className="flex flex-wrap gap-3">
        <AppRouteLink
          href={siteUrl}
          hardNavigate
          className="outline-btn rounded-2xl px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em]"
        >
          {pokrovBranding.siteLinkLabel}
        </AppRouteLink>
        <AppRouteLink
          href={config.supportTelegramUrl}
          target="_blank"
          hardNavigate={false}
          className="outline-btn rounded-2xl px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em]"
        >
          Поддержка
        </AppRouteLink>
        <button
          type="button"
          disabled={webLoginBusy}
          onClick={logoutWebSession}
          className="outline-btn rounded-2xl px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em] disabled:opacity-60"
        >
          Сменить аккаунт
        </button>
      </div>
    </div>
  );
}
