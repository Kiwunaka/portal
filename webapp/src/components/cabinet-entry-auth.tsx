"use client";

import { pokrovBranding } from "@/app/branding";
import AppRouteLink from "@/components/app-route-link";
import TelegramLoginWidget from "@/components/telegram-login-widget";
import { getPortalPublicConfig } from "@/lib/portal";
import { usePortalSession } from "@/lib/session";

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);

export default function CabinetEntryAuth({ siteUrl }: { siteUrl: string }) {
  const { logoutWebSession, webLoginBusy, webLoginError } = usePortalSession();

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
          Нажмите кнопку, подтвердите вход в Telegram, и мы вернем вас сюда с тем же профилем. Это путь
          продолжения, а не новая регистрация.
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
              Готовим аккуратно
            </h3>
          </div>
          <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-600 dark:border-white/10 dark:bg-white/[0.05] dark:text-slate-300">
            Скоро
          </span>
        </div>
        <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
          Email-вход появится после готовности доставки писем. Сейчас для браузера используйте Telegram
          или напишите в поддержку, если доступ нужно восстановить вручную.
        </p>
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
