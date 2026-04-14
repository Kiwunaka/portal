"use client";

import AppRouteLink from "@/components/app-route-link";
import {
  getAccessState,
  getDeviceLimit,
  getTrafficLimitGb,
  isFreeMonthlyState,
  isPaidUnlimitedState,
  isTrialPremiumState,
} from "@/lib/access-policy";
import { getPortalPublicConfig } from "@/lib/portal";
import { usePortalSession } from "@/lib/session";
import { useMemo } from "react";

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);
const ACTIVE_USERS_LABEL = "Людей онлайн сейчас";
const ACTIVE_USERS_HINT = "Оценка по живой активности на точках POKROV. Это ориентир, а не точное число людей.";

const SUPPORT_STEPS = [
  "Откройте приложения POKROV на новом устройстве и войдите в тот же аккаунт.",
  "Проверьте, появилось ли устройство в кабинете и обновился ли текущий статус доступа.",
  "Если устройство не подтянулось, напишите в службу заботы и приложите модель устройства или короткий скриншот.",
] as const;

function fmtNumber(value: number): string {
  if (!Number.isFinite(value)) return "0";
  return new Intl.NumberFormat("ru-RU").format(Math.max(0, Math.floor(value)));
}

export default function DevicesPage() {
  const { loading, error, user, dash } = usePortalSession();

  const activeConnections = Math.max(0, Number(dash?.connection_snapshot?.active_connections ?? dash?.active_sessions ?? 0));
  const activeUsersEstimate = Math.max(0, Number(dash?.connection_snapshot?.active_users_estimate ?? user?.connections?.active_users_estimate ?? 0));
  const deviceLimit = getDeviceLimit(dash, user);
  const knownAppDevices = Math.max(0, Number(user?.sync?.device_count ?? user?.devices?.length ?? 0));
  const activeNodes = Math.max(0, Number(dash?.connection_snapshot?.active_nodes ?? 0));
  const knownNodes = Math.max(0, Number(dash?.connection_snapshot?.known_nodes ?? user?.nodes?.length ?? 0));
  const accessState = getAccessState(dash, user);
  const paidMode = isPaidUnlimitedState(accessState);
  const trialMode = isTrialPremiumState(accessState);
  const freeMode = isFreeMonthlyState(accessState);
  const freeLimitGb = getTrafficLimitGb(dash, user);

  const nodes = useMemo(() => {
    const list = [...(user?.nodes || [])];
    list.sort((a, b) => Number(Boolean(b.enabled)) - Number(Boolean(a.enabled)));
    return list;
  }, [user?.nodes]);

  if (loading) {
    return (
      <main className="space-y-6">
        <section className="glass-card p-7">
          <p className="font-mono text-xs uppercase tracking-[0.18em] text-slate-500">устройства</p>
          <h1 className="mt-2 font-display text-4xl font-bold">Загружаем устройства…</h1>
        </section>
      </main>
    );
  }

  if (error || !user || !dash) {
    return (
      <main className="space-y-6">
        <section className="glass-card p-7">
          <p className="font-mono text-xs uppercase tracking-[0.18em] text-rose-500">ошибка</p>
          <h1 className="mt-2 font-display text-4xl font-bold">Не удалось показать устройства</h1>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{error || "Нет данных профиля."}</p>
          <div className="mt-5 flex flex-wrap gap-3">
            <AppRouteLink href="/support" className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold">
              Открыть поддержку
            </AppRouteLink>
            <AppRouteLink
              href={config.supportTelegramUrl}
              target="_blank"
              hardNavigate={false}
              className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold"
            >
              Написать в Telegram
            </AppRouteLink>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="space-y-6">
      <section className="glass-card p-7">
        <p className="font-mono text-xs uppercase tracking-[0.18em] text-slate-500">устройства</p>
        <h1 className="mt-2 font-display text-4xl font-bold">Устройства и подключения</h1>
        <p className="mt-2 max-w-3xl text-sm text-slate-600 dark:text-slate-300">
          Здесь видно, сколько ваших устройств уже в работе, насколько спокойно синхронизируется доступ и когда лучше перейти в приложения или службу заботы.
        </p>
        <p className="mt-2 max-w-3xl text-sm text-slate-600 dark:text-slate-300">
          Кабинет не показывает личные ссылки подключения и не предлагает копировать их на экран. Для нового устройства используйте приложения POKROV, а если что-то пошло не так, продолжайте через поддержку.
        </p>

        <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-2xl bg-white/70 p-4 dark:bg-white/10">
            <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Подключений сейчас</p>
            <p className="mt-2 text-2xl font-semibold">
              {fmtNumber(activeConnections)} / {fmtNumber(deviceLimit)}
            </p>
            <p className="mt-2 text-[11px] text-slate-500">Из доступных слотов вашего текущего режима</p>
          </div>
          <div className="rounded-2xl border border-emerald-200/60 bg-emerald-50/80 p-4 dark:border-emerald-500/30 dark:bg-emerald-500/10">
            <p className="text-xs uppercase tracking-[0.16em] text-emerald-700 dark:text-emerald-300">{ACTIVE_USERS_LABEL}</p>
            <p className="mt-2 text-2xl font-semibold text-emerald-700 dark:text-emerald-200">{fmtNumber(activeUsersEstimate)}</p>
            <p className="mt-2 text-[11px] text-emerald-700/80 dark:text-emerald-200/80">{ACTIVE_USERS_HINT}</p>
          </div>
          <div className="rounded-2xl bg-white/70 p-4 dark:bg-white/10">
            <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Нод с активностью</p>
            <p className="mt-2 text-2xl font-semibold">
              {fmtNumber(activeNodes)} / {fmtNumber(knownNodes)}
            </p>
            <p className="mt-2 text-[11px] text-slate-500">Где ваш доступ уже виден в текущем маршруте</p>
          </div>
          <div className="rounded-2xl bg-white/70 p-4 dark:bg-white/10">
            <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Известных app-устройств</p>
            <p className="mt-2 text-2xl font-semibold">{fmtNumber(knownAppDevices)}</p>
            <p className="mt-2 text-[11px] text-slate-500">App-first синхронизация ваших устройств</p>
          </div>
        </div>

        <div className="mt-5 flex flex-wrap gap-3">
          <AppRouteLink href="/dashboard/downloads" className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold">
            Открыть приложения
          </AppRouteLink>
          <AppRouteLink href="/support" className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold">
            Служба заботы
          </AppRouteLink>
          <AppRouteLink href="/subscription" className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold">
            Посмотреть доступ
          </AppRouteLink>
        </div>
      </section>

      <section className="grid gap-5 xl:grid-cols-[1.1fr,0.9fr]">
        <article className="glass-card p-6">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-emerald-500">как перенести доступ</p>
          <h2 className="mt-2 font-display text-3xl font-semibold">Новый экран лучше подключать через приложения POKROV</h2>
          <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
            Такой путь безопаснее и спокойнее для пользователя: доступ подтягивается внутри приложения, а кабинет остаётся местом для статуса, продления и помощи без ручной раздачи личных ссылок.
          </p>
          <div className="mt-4 space-y-3">
            {SUPPORT_STEPS.map((step, index) => (
              <div key={step} className="flex items-start gap-3 rounded-2xl border border-white/40 bg-white/55 p-4 dark:border-white/10 dark:bg-white/5">
                <span className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-emerald-900 text-xs font-semibold text-white dark:bg-emerald-700">
                  {index + 1}
                </span>
                <p className="text-sm leading-6 text-slate-700 dark:text-slate-200">{step}</p>
              </div>
            ))}
          </div>
        </article>

        <article className="glass-card p-6">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">что по лимитам</p>
          <h2 className="mt-2 font-display text-3xl font-semibold">
            {paidMode
              ? "Оплаченный доступ уже даёт спокойный запас по устройствам"
              : trialMode
                ? "Премиум-период можно использовать для спокойной проверки на нескольких экранах"
                : freeMode
                  ? "В бесплатном режиме устройство и трафик остаются под контролем"
                  : "Текущий режим зависит от вашего доступа"}
          </h2>
          <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
            {paidMode
              ? "На paid доступно до 5 устройств и безлимитный трафик, поэтому кабинет показывает текущее состояние без лишней ручной настройки."
              : trialMode
                ? "Во время премиум-периода можно спокойно проверить сервис на нескольких своих устройствах, а затем выбрать, нужно ли продление."
                : freeMode
                  ? `На бесплатном режиме доступно до ${deviceLimit} устройств и ${freeLimitGb ? `${fmtNumber(freeLimitGb)} ГБ в месяц` : "месячная квота"}.`
                  : "Если лимиты выглядят неожиданно, лучше сразу проверить раздел подписки или обратиться в поддержку."}
          </p>
          <div className="mt-4 rounded-2xl border border-white/40 bg-white/55 p-4 dark:border-white/10 dark:bg-white/5">
            <p className="text-sm leading-6 text-slate-700 dark:text-slate-200">
              Безопасное подключение продолжается через приложения POKROV и канонический хост <span className="font-semibold">connect.pokrov.space</span>, но личный маршрут на экран кабинета не выводится.
            </p>
          </div>
        </article>
      </section>

      <section className="glass-card p-5">
        <div className="mb-3 flex items-center justify-between gap-2">
          <h2 className="font-display text-2xl font-semibold">Маршруты POKROV</h2>
          <span className="rounded-full bg-white/75 px-3 py-1 text-xs dark:bg-white/10">{fmtNumber(nodes.length)} шт.</span>
        </div>

        {nodes.length ? (
          <div className="space-y-2">
            {nodes.map((node) => (
              <article key={node.code} className="rounded-2xl border border-white/30 bg-white/70 p-4 text-sm dark:border-white/10 dark:bg-white/5">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="font-semibold">{node.name || node.code}</p>
                  <span
                    className={`rounded-full px-2.5 py-1 text-[11px] uppercase tracking-[0.12em] ${
                      node.enabled ? "bg-emerald-500 text-white" : "bg-slate-300 text-slate-700 dark:bg-slate-700 dark:text-slate-100"
                    }`}
                  >
                    {node.enabled ? "готова" : "на паузе"}
                  </span>
                </div>
                <p className="mt-2 text-xs leading-5 text-slate-500">
                  {node.enabled
                    ? "Эта точка сейчас участвует в вашем доступе и может использоваться приложениями POKROV."
                    : "Эта точка временно не участвует в вашем маршруте. Если это неожиданно, лучше уточнить у службы заботы."}
                </p>
              </article>
            ))}
          </div>
        ) : (
          <p className="text-sm text-slate-500">
            Маршруты пока не подтянулись. Если это выглядит неожиданно, откройте службу заботы и сообщите модель устройства или коротко опишите ситуацию.
          </p>
        )}
      </section>
    </main>
  );
}
