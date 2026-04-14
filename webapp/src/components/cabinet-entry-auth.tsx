"use client";

import AppRouteLink from "@/components/app-route-link";
import TelegramLoginWidget from "@/components/telegram-login-widget";
import {
  finishEmailRecovery,
  loginByEmail,
  registerByEmail,
  setWebSessionToken,
  startEmailRecovery,
  verifyEmailToken,
} from "@/lib/api";
import { getPortalPublicConfig } from "@/lib/portal";
import { usePortalSession } from "@/lib/session";
import { useEffect, useMemo, useState } from "react";

import { pokrovBranding } from "@/app/branding";
import PokrovLogo from "@/app/pokrov-logo";

type EmailPanelMode = "login" | "register" | "verify" | "recovery-start" | "recovery-finish";

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);

function parseErrorMessage(error: unknown): string {
  if (error instanceof Error) return error.message || "Не удалось завершить вход";
  if (typeof error === "string") return error;
  return String((error as { message?: string } | null)?.message || "Не удалось завершить вход");
}

function clearEmailAuthQueryParams(): void {
  if (typeof window === "undefined") return;
  const url = new URL(window.location.href);
  for (const key of ["auth", "email_state", "email", "email_verify_token", "email_reset_token"]) {
    url.searchParams.delete(key);
  }
  window.history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}` || "/");
}

export default function CabinetEntryAuth({ siteUrl }: { siteUrl: string }) {
  const { refresh, logoutWebSession, webLoginBusy, webLoginError } = usePortalSession();

  const [activeMethod, setActiveMethod] = useState<"telegram" | "email">("telegram");
  const [emailMode, setEmailMode] = useState<EmailPanelMode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [verifyToken, setVerifyToken] = useState("");
  const [resetToken, setResetToken] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    const auth = params.get("auth");
    const emailState = params.get("email_state");
    const emailParam = params.get("email");
    const verifyParam = params.get("email_verify_token");
    const resetParam = params.get("email_reset_token");

    if (emailParam) setEmail(emailParam);
    if (verifyParam) {
      setActiveMethod("email");
      setEmailMode("verify");
      setVerifyToken(verifyParam);
    } else if (resetParam) {
      setActiveMethod("email");
      setEmailMode("recovery-finish");
      setResetToken(resetParam);
    } else if (auth === "email") {
      setActiveMethod("email");
      setEmailMode(emailState === "sent" ? "verify" : "login");
    }

    if (emailState === "sent" && emailParam) {
      setMessage(`Письмо для входа отправлено на ${emailParam}. Подтвердите email и продолжайте.`);
    }
  }, []);

  async function acceptEmailSession(token: string): Promise<void> {
    setWebSessionToken(token);
    clearEmailAuthQueryParams();
    await refresh();
  }

  async function handleEmailLogin(event: React.FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setPending(true);
    setError("");
    setMessage("");
    try {
      const result = await loginByEmail({ email, password });
      await acceptEmailSession(result.token);
    } catch (authError) {
      setError(parseErrorMessage(authError));
    } finally {
      setPending(false);
    }
  }

  async function handleEmailRegister(event: React.FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setPending(true);
    setError("");
    setMessage("");
    try {
      const result = await registerByEmail({
        email,
        password,
        display_name: displayName.trim() || undefined,
      });
      if (result.debug?.verify_token) {
        setVerifyToken(result.debug.verify_token);
      }
      setEmailMode("verify");
      setActiveMethod("email");
      const deliveryState = result.delivery?.status === "sent" ? "Письмо уже отправлено." : "Подтвердите email, чтобы открыть кабинет.";
      setMessage(`${deliveryState}${email ? ` Адрес: ${email}.` : ""}`);
    } catch (authError) {
      setError(parseErrorMessage(authError));
    } finally {
      setPending(false);
    }
  }

  async function handleVerify(event: React.FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setPending(true);
    setError("");
    setMessage("");
    try {
      const result = await verifyEmailToken({ token: verifyToken });
      await acceptEmailSession(result.token);
    } catch (authError) {
      setError(parseErrorMessage(authError));
    } finally {
      setPending(false);
    }
  }

  async function handleRecoveryStart(event: React.FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setPending(true);
    setError("");
    setMessage("");
    try {
      const result = await startEmailRecovery({ email });
      if (result.debug?.reset_token) {
        setResetToken(result.debug.reset_token);
      }
      setEmailMode("recovery-finish");
      setMessage(`Инструкции для восстановления подготовлены${email ? ` для ${email}` : ""}. Введите код из письма и задайте новый пароль.`);
    } catch (authError) {
      setError(parseErrorMessage(authError));
    } finally {
      setPending(false);
    }
  }

  async function handleRecoveryFinish(event: React.FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setPending(true);
    setError("");
    setMessage("");
    try {
      const result = await finishEmailRecovery({ token: resetToken, password });
      await acceptEmailSession(result.token);
    } catch (authError) {
      setError(parseErrorMessage(authError));
    } finally {
      setPending(false);
    }
  }

  const emailSwitchers = useMemo(
    () => [
      { key: "login" as const, label: "Войти" },
      { key: "register" as const, label: "Регистрация" },
      { key: "verify" as const, label: "Подтвердить email" },
      { key: "recovery-start" as const, label: "Восстановить пароль" },
    ],
    [],
  );

  const methodCards = [
    {
      key: "telegram" as const,
      eyebrow: "Telegram",
      title: "Самый быстрый вход",
      body: "Хорошо подходит, если вы уже пользовались ботом или открыли кабинет из Telegram.",
    },
    {
      key: "email" as const,
      eyebrow: "Email",
      title: "Дополнительный путь",
      body: "Подходит, если нужен браузерный вход без Telegram, но с тем же кабинетом и тем же доступом.",
    },
  ];

  return (
    <div className="space-y-5">
      <div className="rounded-[24px] border border-emerald-900/10 bg-emerald-900/[0.04] p-4 dark:border-emerald-200/10 dark:bg-emerald-200/[0.05]">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-2">
            <PokrovLogo
              showWordmark
              className="inline-flex items-center gap-3"
              markClassName="h-10 w-10"
              caption={pokrovBranding.cabinetName}
              label="POKROV cabinet sign-in"
            />
            <p className="max-w-xl text-sm leading-6 text-slate-700 dark:text-slate-200">
              Выберите удобный способ входа. После подтверждения кабинет вернёт вас к доступу, устройствам и службе заботы без ручной настройки.
            </p>
          </div>
          <div className="rounded-2xl border border-white/70 bg-white/80 px-4 py-3 text-xs leading-5 text-slate-600 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-300">
            POKROV app остаётся основным путём подключения.
            <br />
            Кабинет помогает с продолжением доступа и поддержкой.
          </div>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        {methodCards.map((item) => {
          const selected = activeMethod === item.key;
          return (
            <button
              key={item.key}
              type="button"
              onClick={() => {
                setActiveMethod(item.key);
                setError("");
                setMessage("");
              }}
              className={`rounded-[24px] border px-4 py-4 text-left text-sm transition ${
                selected
                  ? "border-emerald-900/15 bg-emerald-900/[0.05] text-emerald-950 shadow-[0_20px_40px_-32px_rgba(18,48,36,0.55)] dark:border-emerald-200/20 dark:bg-emerald-200/[0.08] dark:text-emerald-100"
                  : "border-slate-200/80 bg-white/80 text-slate-600 dark:border-white/10 dark:bg-white/[0.03] dark:text-slate-300"
              }`}
            >
              <span className="block text-[11px] font-semibold uppercase tracking-[0.16em]">{item.eyebrow}</span>
              <span className="mt-2 block text-base font-semibold text-slate-900 dark:text-slate-50">{item.title}</span>
              <span className="mt-2 block leading-6">{item.body}</span>
            </button>
          );
        })}
      </div>

      {activeMethod === "telegram" ? (
        <div className="space-y-4 rounded-[24px] border border-white/70 bg-white/88 p-5 dark:border-white/10 dark:bg-[#121b17]/88">
          <div className="rounded-[20px] border border-white/70 bg-white/80 px-4 py-4 dark:border-white/10 dark:bg-white/[0.04]">
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">Рекомендуемый вход</p>
            <p className="mt-2 text-sm leading-6 text-slate-700 dark:text-slate-200">
              Telegram быстрее всего продолжает уже известный кабинет. Подтверждение занимает один шаг, после чего вы сразу попадёте в статус, устройства и поддержку.
            </p>
          </div>
          <TelegramLoginWidget />
          {webLoginError ? (
            <div className="rounded-2xl border border-rose-200/70 bg-rose-50/80 px-4 py-3 text-sm leading-6 text-rose-700 dark:border-rose-400/20 dark:bg-rose-400/10 dark:text-rose-200">
              {webLoginError}
            </div>
          ) : null}
        </div>
      ) : (
        <div className="space-y-4 rounded-[24px] border border-white/70 bg-white/88 p-5 dark:border-white/10 dark:bg-[#121b17]/88">
          <div className="rounded-[20px] border border-white/70 bg-white/80 px-4 py-4 dark:border-white/10 dark:bg-white/[0.04]">
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">Дополнительный путь</p>
            <p className="mt-2 text-sm leading-6 text-slate-700 dark:text-slate-200">
              Email-вход нужен для того же кабинета в браузере. Он не заменяет приложение и Telegram, а просто добавляет ещё один надёжный способ вернуться к своему доступу.
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            {emailSwitchers.map((item) => (
              <button
                key={item.key}
                type="button"
                onClick={() => {
                  setEmailMode(item.key);
                  setError("");
                  setMessage("");
                }}
                className={`rounded-full px-3 py-2 text-xs font-semibold uppercase tracking-[0.14em] transition ${
                  emailMode === item.key
                    ? "bg-emerald-900 text-white dark:bg-emerald-700"
                    : "border border-slate-200/80 bg-white/80 text-slate-600 dark:border-white/10 dark:bg-white/[0.03] dark:text-slate-300"
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>

          {emailMode === "login" ? (
            <form className="space-y-3" onSubmit={handleEmailLogin}>
              <label className="block text-sm">
                <span className="mb-1 block text-slate-600 dark:text-slate-300">Email</span>
                <input
                  className="w-full rounded-2xl border border-slate-200/80 bg-white px-4 py-3 text-slate-900 outline-none transition focus:border-emerald-700 dark:border-white/10 dark:bg-[#0f1714] dark:text-slate-100"
                  autoComplete="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="hello@pokrov.space"
                  type="email"
                  required
                />
              </label>
              <label className="block text-sm">
                <span className="mb-1 block text-slate-600 dark:text-slate-300">Пароль</span>
                <input
                  className="w-full rounded-2xl border border-slate-200/80 bg-white px-4 py-3 text-slate-900 outline-none transition focus:border-emerald-700 dark:border-white/10 dark:bg-[#0f1714] dark:text-slate-100"
                  autoComplete="current-password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  type="password"
                  required
                />
              </label>
              <div className="flex flex-wrap gap-3">
                <button className="btn-primary rounded-2xl px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em]" disabled={pending} type="submit">
                  {pending ? "Проверяем вход..." : "Открыть кабинет"}
                </button>
                <button
                  type="button"
                  className="outline-btn rounded-2xl px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em]"
                  onClick={() => {
                    setEmailMode("recovery-start");
                    setError("");
                    setMessage("");
                  }}
                >
                  Забыли пароль?
                </button>
              </div>
            </form>
          ) : null}

          {emailMode === "register" ? (
            <form className="space-y-3" onSubmit={handleEmailRegister}>
              <label className="block text-sm">
                <span className="mb-1 block text-slate-600 dark:text-slate-300">Email</span>
                <input
                  className="w-full rounded-2xl border border-slate-200/80 bg-white px-4 py-3 text-slate-900 outline-none transition focus:border-emerald-700 dark:border-white/10 dark:bg-[#0f1714] dark:text-slate-100"
                  autoComplete="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="hello@pokrov.space"
                  type="email"
                  required
                />
              </label>
              <label className="block text-sm">
                <span className="mb-1 block text-slate-600 dark:text-slate-300">Как к вам обращаться</span>
                <input
                  className="w-full rounded-2xl border border-slate-200/80 bg-white px-4 py-3 text-slate-900 outline-none transition focus:border-emerald-700 dark:border-white/10 dark:bg-[#0f1714] dark:text-slate-100"
                  autoComplete="name"
                  value={displayName}
                  onChange={(event) => setDisplayName(event.target.value)}
                  placeholder="POKROV user"
                  type="text"
                />
              </label>
              <label className="block text-sm">
                <span className="mb-1 block text-slate-600 dark:text-slate-300">Пароль</span>
                <input
                  className="w-full rounded-2xl border border-slate-200/80 bg-white px-4 py-3 text-slate-900 outline-none transition focus:border-emerald-700 dark:border-white/10 dark:bg-[#0f1714] dark:text-slate-100"
                  autoComplete="new-password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  type="password"
                  minLength={10}
                  required
                />
              </label>
              <button className="btn-primary rounded-2xl px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em]" disabled={pending} type="submit">
                {pending ? "Готовим email..." : "Создать доступ"}
              </button>
            </form>
          ) : null}

          {emailMode === "verify" ? (
            <form className="space-y-3" onSubmit={handleVerify}>
              <label className="block text-sm">
                <span className="mb-1 block text-slate-600 dark:text-slate-300">Код подтверждения</span>
                <textarea
                  className="min-h-[112px] w-full rounded-2xl border border-slate-200/80 bg-white px-4 py-3 text-slate-900 outline-none transition focus:border-emerald-700 dark:border-white/10 dark:bg-[#0f1714] dark:text-slate-100"
                  value={verifyToken}
                  onChange={(event) => setVerifyToken(event.target.value)}
                  placeholder="Вставьте код из письма"
                  required
                />
              </label>
              <button className="btn-primary rounded-2xl px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em]" disabled={pending} type="submit">
                {pending ? "Подтверждаем..." : "Продолжить через email"}
              </button>
            </form>
          ) : null}

          {emailMode === "recovery-start" ? (
            <form className="space-y-3" onSubmit={handleRecoveryStart}>
              <label className="block text-sm">
                <span className="mb-1 block text-slate-600 dark:text-slate-300">Email</span>
                <input
                  className="w-full rounded-2xl border border-slate-200/80 bg-white px-4 py-3 text-slate-900 outline-none transition focus:border-emerald-700 dark:border-white/10 dark:bg-[#0f1714] dark:text-slate-100"
                  autoComplete="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="hello@pokrov.space"
                  type="email"
                  required
                />
              </label>
              <button className="btn-primary rounded-2xl px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em]" disabled={pending} type="submit">
                {pending ? "Проверяем email..." : "Отправить письмо"}
              </button>
            </form>
          ) : null}

          {emailMode === "recovery-finish" ? (
            <form className="space-y-3" onSubmit={handleRecoveryFinish}>
              <label className="block text-sm">
                <span className="mb-1 block text-slate-600 dark:text-slate-300">Код восстановления</span>
                <textarea
                  className="min-h-[112px] w-full rounded-2xl border border-slate-200/80 bg-white px-4 py-3 text-slate-900 outline-none transition focus:border-emerald-700 dark:border-white/10 dark:bg-[#0f1714] dark:text-slate-100"
                  value={resetToken}
                  onChange={(event) => setResetToken(event.target.value)}
                  placeholder="Вставьте код из письма"
                  required
                />
              </label>
              <label className="block text-sm">
                <span className="mb-1 block text-slate-600 dark:text-slate-300">Новый пароль</span>
                <input
                  className="w-full rounded-2xl border border-slate-200/80 bg-white px-4 py-3 text-slate-900 outline-none transition focus:border-emerald-700 dark:border-white/10 dark:bg-[#0f1714] dark:text-slate-100"
                  autoComplete="new-password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  type="password"
                  minLength={10}
                  required
                />
              </label>
              <button className="btn-primary rounded-2xl px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em]" disabled={pending} type="submit">
                {pending ? "Обновляем пароль..." : "Сохранить новый пароль"}
              </button>
            </form>
          ) : null}

          <p className="text-xs leading-5 text-slate-500 dark:text-slate-400">
            Email-вход работает как дополнительный путь к тому же кабинету. Приложение и Telegram остаются совместимыми и продолжают тот же аккаунт.
          </p>
        </div>
      )}

      {message ? (
        <div className="rounded-2xl border border-emerald-900/10 bg-emerald-900/[0.04] px-4 py-3 text-sm leading-6 text-emerald-900 dark:border-emerald-200/10 dark:bg-emerald-200/[0.04] dark:text-emerald-100">
          {message}
        </div>
      ) : null}
      {error ? (
        <div className="rounded-2xl border border-rose-200/70 bg-rose-50/80 px-4 py-3 text-sm leading-6 text-rose-700 dark:border-rose-400/20 dark:bg-rose-400/10 dark:text-rose-200">
          {error}
        </div>
      ) : null}

      <div className="flex flex-wrap gap-3">
        <AppRouteLink
          href={siteUrl}
          hardNavigate
          aria-label="Вернуться на сайт"
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
          Служба заботы
        </AppRouteLink>
        <button
          className="outline-btn rounded-2xl px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em]"
          type="button"
          disabled={pending || webLoginBusy}
          onClick={logoutWebSession}
        >
          Сменить аккаунт
        </button>
      </div>
    </div>
  );
}
