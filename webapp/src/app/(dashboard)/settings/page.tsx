"use client";

import { useEffect, useState, type FormEvent } from "react";

import AppRouteLink from "@/components/app-route-link";
import { CabinetGroup, CabinetRow, CabinetStatus } from "@/components/cabinet/surface";
import { getDeviceLimit, resolvePlanLabel, resolveTrafficStatusText } from "@/lib/access-policy";
import {
  checkChannelSubscriberStatus,
  claimChannelBonus,
  getEmailAuthStatus,
  registerByEmail,
  setWebSessionToken,
  startTelegramLink,
  type TelegramLinkStartResult,
  verifyEmailToken,
} from "@/lib/api";
import { isEmailAuthPublicReady } from "@/lib/email-auth-readiness";
import { userFacingErrorMessage } from "@/lib/public-error-messages";
import { usePortalSession } from "@/lib/session";

function icon(name: string) {
  return <span className="material-symbols-rounded text-[20px]">{name}</span>;
}

function formatDate(value?: string | null): string {
  if (!value) return "уточняется";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "уточняется";
  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "long",
  }).format(parsed);
}

function profileLabel(username?: string | null, tgId?: number | null): string {
  if (username) return `@${username}`;
  if (tgId) return `ID ${tgId}`;
  return "Аккаунт POKROV";
}

function isSyntheticEmailAccountId(value?: number | string | null): boolean {
  const id = Number(value || 0);
  return Number.isFinite(id) && id >= 8_000_000_000_000 && id < 9_000_000_000_000;
}

type BonusCheckState = {
  subscriber: boolean;
  alreadyClaimed: boolean;
  bonusDays: number;
  message: string;
};

export default function SettingsPage() {
  const { user, dash, refresh } = usePortalSession();
  const [bonusCheck, setBonusCheck] = useState<BonusCheckState | null>(null);
  const [bonusMessage, setBonusMessage] = useState("");
  const [bonusError, setBonusError] = useState("");
  const [bonusBusy, setBonusBusy] = useState<"check" | "claim" | "">("");
  const [emailReady, setEmailReady] = useState(false);
  const [emailLinkEmail, setEmailLinkEmail] = useState("");
  const [emailLinkName, setEmailLinkName] = useState("");
  const [emailLinkPassword, setEmailLinkPassword] = useState("");
  const [emailLinkToken, setEmailLinkToken] = useState("");
  const [emailLinkBusy, setEmailLinkBusy] = useState<"request" | "verify" | "">("");
  const [emailLinkMessage, setEmailLinkMessage] = useState("");
  const [emailLinkError, setEmailLinkError] = useState("");
  const [telegramLinkBusy, setTelegramLinkBusy] = useState(false);
  const [telegramLinkPayload, setTelegramLinkPayload] = useState<TelegramLinkStartResult | null>(null);
  const [telegramLinkError, setTelegramLinkError] = useState("");

  const linked = user?.linked_identities || dash?.linked_identities || null;
  const linkedEmail = user?.email || linked?.email?.email || "";
  const linkedTelegram = linked?.telegram || null;
  const linkedTelegramId = Number(linkedTelegram?.id || 0);
  const linkedTelegramUsername = String(linkedTelegram?.username || "").trim();
  const hasLinkedTelegram = Boolean(
    linkedTelegramUsername ||
      (linkedTelegramId && !isSyntheticEmailAccountId(linkedTelegramId)) ||
      (!linkedEmail && (user?.username || (user?.tg_id && !isSyntheticEmailAccountId(user.tg_id)))),
  );
  const profileName = user?.username ? profileLabel(user.username, user?.tg_id) : linkedEmail || profileLabel(user?.username, user?.tg_id);
  const telegramName = hasLinkedTelegram
    ? linkedTelegramUsername
      ? `@${linkedTelegramUsername}`
      : profileLabel(user?.username, user?.tg_id)
    : "не подключен";
  const deviceLimit = getDeviceLimit(dash, user);
  const channelLink = user?.channel?.link || "";
  const supportLink = user?.support?.link || "/support/";
  const channelBonusDays = bonusCheck?.bonusDays || user?.bonuses?.channel_bonus?.premium_days || 10;
  const channelBonusClaimedAt = user?.bonuses?.channel_bonus?.claimed_at || null;
  const channelBonusReady = Boolean(user?.bonuses?.channel_bonus?.can_claim);
  const canClaimBonus = !channelBonusClaimedAt && (channelBonusReady || Boolean(bonusCheck?.subscriber && !bonusCheck.alreadyClaimed));
  const canLinkEmail = Boolean(emailReady && !linkedEmail);
  const bonusStatusText =
    bonusMessage ||
    (channelBonusClaimedAt
      ? `Бонус уже добавлен ${formatDate(channelBonusClaimedAt)}.`
      : bonusCheck?.message || (channelBonusReady ? `Можно забрать +${channelBonusDays} дней.` : "Проверьте подписку на канал."));

  useEffect(() => {
    let cancelled = false;
    void getEmailAuthStatus()
      .then((payload) => {
        if (!cancelled) setEmailReady(isEmailAuthPublicReady(payload));
      })
      .catch(() => {
        if (!cancelled) setEmailReady(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function onTelegramLink(): Promise<void> {
    setTelegramLinkBusy(true);
    setTelegramLinkError("");
    setTelegramLinkPayload(null);
    try {
      const payload = await startTelegramLink();
      setTelegramLinkPayload(payload);
      if (payload.linked) {
        await refresh();
      }
    } catch (error) {
      setTelegramLinkError(
        userFacingErrorMessage(error, "Не удалось подготовить привязку Telegram. Попробуйте еще раз или откройте поддержку."),
      );
    } finally {
      setTelegramLinkBusy(false);
    }
  }

  const onCheckBonus = async (): Promise<void> => {
    setBonusBusy("check");
    setBonusError("");
    setBonusMessage("");
    try {
      const payload = await checkChannelSubscriberStatus();
      const subscriber = Boolean(payload.subscriber);
      const alreadyClaimed = Boolean(payload.already_claimed);
      setBonusCheck({
        subscriber,
        alreadyClaimed,
        bonusDays: Number(payload.bonus_days || channelBonusDays || 10),
        message: alreadyClaimed
          ? "Бонус уже был добавлен раньше."
          : subscriber
            ? "Подписка подтверждена. Теперь можно забрать бонус."
            : "Подписка пока не подтверждена. Откройте канал и попробуйте еще раз.",
      });
    } catch (error) {
      setBonusError(userFacingErrorMessage(error, "Не удалось проверить подписку. Попробуйте позже или откройте поддержку."));
    } finally {
      setBonusBusy("");
    }
  };

  const onClaimBonus = async (): Promise<void> => {
    setBonusBusy("claim");
    setBonusError("");
    setBonusMessage("");
    try {
      const payload = await claimChannelBonus();
      const days = Number(payload.premium_days || channelBonusDays || 10);
      setBonusMessage(payload.already_claimed ? "Бонус уже был добавлен раньше." : `Бонус +${days} дней добавлен.`);
    } catch (error) {
      setBonusError(userFacingErrorMessage(error, "Не удалось добавить бонус. Попробуйте позже или откройте поддержку."));
    } finally {
      setBonusBusy("");
    }
  };

  const onEmailLinkRequest = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setEmailLinkBusy("request");
    setEmailLinkError("");
    setEmailLinkMessage("");
    try {
      await registerByEmail({
        email: emailLinkEmail.trim(),
        password: emailLinkPassword,
        display_name: emailLinkName.trim() || undefined,
      });
      setEmailLinkMessage("Письмо отправлено. Введите код подтверждения из письма.");
    } catch (error) {
      setEmailLinkError(userFacingErrorMessage(error, "Не удалось отправить письмо. Проверьте email и попробуйте еще раз."));
    } finally {
      setEmailLinkPassword("");
      setEmailLinkBusy("");
    }
  };

  const onEmailLinkVerify = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setEmailLinkBusy("verify");
    setEmailLinkError("");
    setEmailLinkMessage("");
    try {
      const payload = await verifyEmailToken({ token: emailLinkToken.trim() });
      if (payload?.token) {
        setWebSessionToken(payload.token);
      }
      await refresh();
      setEmailLinkPassword("");
      setEmailLinkMessage("Email подтвержден и привязан к текущему аккаунту.");
    } catch (error) {
      setEmailLinkError(userFacingErrorMessage(error, "Не удалось подтвердить email. Проверьте код и попробуйте еще раз."));
    } finally {
      setEmailLinkBusy("");
    }
  };

  return (
    <main className="mx-auto w-full max-w-[840px] space-y-5">
      <CabinetStatus
        title="Аккаунт"
        meta={profileName}
        body={dash?.is_active ? "Доступ, вход и бонусы собраны здесь." : "Продлите доступ или откройте поддержку, если что-то не сходится."}
        tone={dash?.is_active ? "success" : "warning"}
        action={
          <AppRouteLink href="/subscription/" className="btn-primary w-full rounded-full px-5 py-3 text-sm font-semibold sm:w-auto">
            Продлить
          </AppRouteLink>
        }
      />

      <CabinetGroup title="Профиль">
        <CabinetRow icon={icon("verified_user")} label="Доступ" hint={resolveTrafficStatusText(dash, user)} value={resolvePlanLabel(dash, user)} href="/subscription/" />
        <CabinetRow icon={icon("calendar_month")} label="Срок" hint="По текущему профилю" value={formatDate(dash?.expiry_at || user?.expiry_at)} />
        <CabinetRow icon={icon("devices")} label="Устройства" hint="Лимит профиля" value={`до ${deviceLimit}`} href="/devices/" />
      </CabinetGroup>

      <CabinetGroup title="Вход и восстановление">
        <CabinetRow
          icon={icon("send")}
          label="Telegram"
          hint={hasLinkedTelegram ? "Подключен к этому профилю" : "Для входа, бонуса и восстановления"}
          value={telegramName}
          action={
            hasLinkedTelegram ? (
              <AppRouteLink href={supportLink} className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
                Поддержка
              </AppRouteLink>
            ) : (
              <button
                type="button"
                onClick={() => void onTelegramLink()}
                disabled={telegramLinkBusy}
                className="text-sm font-semibold text-emerald-800 disabled:opacity-60 dark:text-emerald-300"
              >
                {telegramLinkBusy ? "Открываем..." : "Подключить Telegram"}
              </button>
            )
          }
        />
        <CabinetRow
          icon={icon("alternate_email")}
          label="Email"
          hint={linkedEmail ? "Дополнительный вход подключен" : emailReady ? "Можно добавить к этому профилю" : "Появится после проверки писем"}
          value={linkedEmail || (emailReady ? "доступен" : "скоро")}
          action={
            canLinkEmail ? (
              <a href="#email-link" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
                Добавить
              </a>
            ) : null
          }
        />
      </CabinetGroup>

      {telegramLinkPayload || telegramLinkError ? (
        <div className="rounded-2xl border border-emerald-200/70 bg-emerald-50/85 px-5 py-4 text-sm leading-6 text-emerald-900 dark:border-emerald-400/25 dark:bg-emerald-400/10 dark:text-emerald-100">
          {telegramLinkError ? (
            <p className="font-semibold text-rose-700 dark:text-rose-200">{telegramLinkError}</p>
          ) : telegramLinkPayload?.linked ? (
            <p className="font-semibold">Telegram уже подключен к этому профилю.</p>
          ) : (
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="font-semibold">Откройте бота и завершите привязку Telegram.</p>
              <AppRouteLink
                href={telegramLinkPayload?.bot_url || supportLink}
                target="_blank"
                hardNavigate={false}
                className="outline-btn rounded-full px-4 py-2 text-sm font-semibold"
              >
                Открыть бота
              </AppRouteLink>
            </div>
          )}
        </div>
      ) : null}

      {canLinkEmail ? (
        <section id="email-link" className="scroll-mt-24 space-y-2">
          <div className="px-1">
            <h2 className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">
              Подключить email к текущему аккаунту
            </h2>
          </div>
          <div className="rounded-2xl border border-slate-200/80 bg-white/86 p-4 dark:border-white/10 dark:bg-white/[0.04]">
            <div className="grid gap-5 lg:grid-cols-[1fr_0.9fr]">
              <form className="space-y-3" onSubmit={onEmailLinkRequest}>
                <input
                  className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-emerald-400 dark:border-white/10 dark:bg-white/[0.04]"
                  value={emailLinkEmail}
                  onChange={(event) => setEmailLinkEmail(event.target.value)}
                  type="email"
                  placeholder="name@example.com"
                  autoComplete="email"
                  required
                />
                <input
                  className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-emerald-400 dark:border-white/10 dark:bg-white/[0.04]"
                  value={emailLinkName}
                  onChange={(event) => setEmailLinkName(event.target.value)}
                  placeholder="Как обращаться"
                  autoComplete="name"
                />
                <input
                  className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-emerald-400 dark:border-white/10 dark:bg-white/[0.04]"
                  value={emailLinkPassword}
                  onChange={(event) => setEmailLinkPassword(event.target.value)}
                  type="password"
                  placeholder="Минимум 10 символов"
                  autoComplete="new-password"
                  minLength={10}
                  required
                />
                <button
                  type="submit"
                  disabled={emailLinkBusy !== ""}
                  className="btn-primary rounded-2xl px-5 py-3 text-sm font-semibold disabled:opacity-60"
                >
                  {emailLinkBusy === "request" ? "Отправляем..." : "Отправить письмо"}
                </button>
              </form>

              <form className="space-y-3" onSubmit={onEmailLinkVerify}>
                <input
                  className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-emerald-400 dark:border-white/10 dark:bg-white/[0.04]"
                  value={emailLinkToken}
                  onChange={(event) => setEmailLinkToken(event.target.value)}
                  placeholder="Код подтверждения"
                  autoComplete="one-time-code"
                  required
                />
                <button
                  type="submit"
                  disabled={emailLinkBusy !== ""}
                  className="outline-btn rounded-2xl px-5 py-3 text-sm font-semibold disabled:opacity-60"
                >
                  {emailLinkBusy === "verify" ? "Проверяем..." : "Подтвердить email"}
                </button>
                {emailLinkMessage ? <p className="text-sm leading-6 text-emerald-700 dark:text-emerald-200">{emailLinkMessage}</p> : null}
                {emailLinkError ? <p className="text-sm leading-6 text-rose-700 dark:text-rose-200">{emailLinkError}</p> : null}
              </form>
            </div>
          </div>
        </section>
      ) : emailLinkMessage ? (
        <p className="px-1 text-sm font-semibold text-emerald-800 dark:text-emerald-300">{emailLinkMessage}</p>
      ) : null}

      <CabinetGroup title="Telegram-бонус">
        <CabinetRow
          icon={icon("campaign")}
          label="Канал"
          hint="Официальные новости и бонус"
          value="@pokrov_vpn"
          action={
            channelLink ? (
              <AppRouteLink href={channelLink} target="_blank" hardNavigate={false} className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
                Открыть
              </AppRouteLink>
            ) : null
          }
        />
        <CabinetRow
          icon={icon("fact_check")}
          label="Проверка"
          hint={bonusStatusText}
          action={
            <button
              type="button"
              onClick={() => void onCheckBonus()}
              disabled={bonusBusy !== ""}
              className="text-sm font-semibold text-emerald-800 disabled:opacity-60 dark:text-emerald-300"
            >
              {bonusBusy === "check" ? "Проверяем..." : "Проверить подписку"}
            </button>
          }
        />
        <CabinetRow
          icon={icon("add_circle")}
          label={`Бонус +${channelBonusDays} дней`}
          hint={bonusError || (channelBonusClaimedAt ? "Уже добавлен" : "После подтверждения канала")}
          action={
            <button
              type="button"
              onClick={() => void onClaimBonus()}
              disabled={bonusBusy !== "" || Boolean(channelBonusClaimedAt) || (!canClaimBonus && !bonusCheck?.subscriber)}
              className="text-sm font-semibold text-emerald-800 disabled:opacity-50 dark:text-emerald-300"
            >
              {bonusBusy === "claim" ? "Добавляем..." : `Забрать +${channelBonusDays} дней`}
            </button>
          }
        />
      </CabinetGroup>

      <CabinetGroup title="Действия">
        <CabinetRow icon={icon("devices")} label="Устройства" hint="Связанные телефоны и компьютеры" href="/devices/" />
        <CabinetRow icon={icon("download")} label="Загрузки" hint="Android APK и Windows beta" href="/downloads/" />
        <CabinetRow icon={icon("support_agent")} label="Поддержка" hint="Обращения, вложения и Telegram" href="/support/" />
      </CabinetGroup>
    </main>
  );
}
