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
import { userFacingErrorMessage } from "@/lib/public-error-messages";
import { usePortalSession } from "@/lib/session";
import { useEffect, useState, type FormEvent } from "react";

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);
const isEmailPublicReady = (payload: Awaited<ReturnType<typeof getEmailAuthStatus>>): boolean =>
  Boolean(
    payload.enabled &&
      payload.public_enabled &&
      payload.delivery_configured &&
      payload.delivery_secret_configured &&
      !payload.debug_echo,
  );

const EMAIL_MODE_LABELS = {
  login: "Войти",
  register: "Создать аккаунт",
  verify: "Подтвердить",
  recover: "Восстановить доступ",
} as const;

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
  const [verifyToken, setVerifyToken] = useState("");
  const [recoveryToken, setRecoveryToken] = useState("");
  const [newPassword, setNewPassword] = useState("");

  useEffect(() => {
    let cancelled = false;
    void getEmailAuthStatus()
      .then((payload) => {
        if (!cancelled) setEmailReady(isEmailPublicReady(payload));
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
      setEmailError("Не получен токен email-сессии.");
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
      setEmailError(userFacingErrorMessage(error, "Не удалось выполнить действие с email. Попробуйте позже или напишите в поддержку."));
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
          ? "Письмо для подтверждения отправлено."
          : "Аккаунт создан. Введите код подтверждения из письма.",
      );
      setVerifyToken("");
      setRecoveryToken("");
      setEmailMode("verify");
    });
  };

  const submitVerify = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    await runEmailAction(async () => {
      const token = String(verifyToken || "").trim();
      if (!token) {
        setEmailError("Введите код подтверждения из письма.");
        return;
      }
      const payload = await verifyEmailToken({ token });
      completeEmailLogin(payload.token);
    });
  };

  const submitRecovery = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    await runEmailAction(async () => {
      const token = String(recoveryToken || "").trim();
      if (!token) {
        await startEmailRecovery({ email });
        setEmailMessage("Письмо для восстановления отправлено. Введите код и новый пароль.");
        return;
      }
      const nextPassword = String(newPassword || "").trim();
      if (!nextPassword) {
        setEmailError("Введите новый пароль из письма восстановления.");
        return;
      }
      const payload = await finishEmailRecovery({ token, password: nextPassword });
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
              {emailReady ? "Email-вход" : "Проверяем доставку"}
            </h3>
          </div>
          <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-600 dark:border-white/10 dark:bg-white/[0.05] dark:text-slate-300">
            {emailReady ? "Готово" : "Недоступно"}
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
                    if (mode === "verify") setRecoveryToken("");
                    if (mode === "recover") setVerifyToken("");
                  }}
                  className={`rounded-full border px-3 py-2 text-xs font-semibold uppercase tracking-[0.12em] ${
                    emailMode === mode
                      ? "border-emerald-400 bg-emerald-100 text-emerald-900 dark:border-emerald-300/40 dark:bg-emerald-400/15 dark:text-emerald-100"
                      : "border-slate-200 bg-white text-slate-600 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-300"
                  }`}
                >
                  {EMAIL_MODE_LABELS[mode]}
                </button>
              ))}
            </div>

            {emailMode === "login" ? (
              <form className="space-y-3" onSubmit={submitLogin}>
                <input className={inputClass} value={email} onChange={(event) => setEmail(event.target.value)} type="email" placeholder="email@example.com" required />
                <input className={inputClass} value={password} onChange={(event) => setPassword(event.target.value)} type="password" placeholder="Пароль" required />
                <button type="submit" disabled={emailBusy} className="btn-primary rounded-2xl px-5 py-3 text-sm font-semibold disabled:opacity-60">
                  Войти
                </button>
              </form>
            ) : null}

            {emailMode === "register" ? (
              <form className="space-y-3" onSubmit={submitRegister}>
                <input className={inputClass} value={email} onChange={(event) => setEmail(event.target.value)} type="email" placeholder="email@example.com" required />
                <input className={inputClass} value={displayName} onChange={(event) => setDisplayName(event.target.value)} placeholder="Имя" />
                <input className={inputClass} value={password} onChange={(event) => setPassword(event.target.value)} type="password" placeholder="Пароль" required />
                <button type="submit" disabled={emailBusy} className="btn-primary rounded-2xl px-5 py-3 text-sm font-semibold disabled:opacity-60">
                  Создать аккаунт
                </button>
              </form>
            ) : null}

            {emailMode === "verify" ? (
              <form className="space-y-3" onSubmit={submitVerify}>
                <input className={inputClass} value={verifyToken} onChange={(event) => setVerifyToken(event.target.value)} placeholder="Код подтверждения" required />
                <button type="submit" disabled={emailBusy} className="btn-primary rounded-2xl px-5 py-3 text-sm font-semibold disabled:opacity-60">
                  Подтвердить
                </button>
              </form>
            ) : null}

            {emailMode === "recover" ? (
              <form className="space-y-3" onSubmit={submitRecovery}>
                <input className={inputClass} value={email} onChange={(event) => setEmail(event.target.value)} type="email" placeholder="email@example.com" required />
                <input className={inputClass} value={recoveryToken} onChange={(event) => setRecoveryToken(event.target.value)} placeholder="Код восстановления" />
                <input className={inputClass} value={newPassword} onChange={(event) => setNewPassword(event.target.value)} type="password" placeholder="Новый пароль" required={Boolean(recoveryToken)} />
                <button type="submit" disabled={emailBusy} className="btn-primary rounded-2xl px-5 py-3 text-sm font-semibold disabled:opacity-60">
                  {recoveryToken ? "Сбросить пароль и войти" : "Отправить письмо"}
                </button>
              </form>
            ) : null}

            {emailMessage ? <p className="text-sm leading-6 text-emerald-700 dark:text-emerald-200">{emailMessage}</p> : null}
            {emailError ? <p className="text-sm leading-6 text-rose-700 dark:text-rose-200">{emailError}</p> : null}
          </div>
        ) : (
          <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
            Email-вход скрыт, пока доставка писем на проде недоступна. Сейчас для браузера используйте Telegram или напишите в поддержку, если доступ нужно восстановить вручную.
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
