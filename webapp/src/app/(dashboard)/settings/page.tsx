"use client";

import { useEffect, useState, type FormEvent } from "react";

import AppRouteLink from "@/components/app-route-link";
import { icon } from "@/components/cabinet/icon";
import { CabinetActionCard, CabinetActionGrid, CabinetGroup, CabinetRow, CabinetStatus, CabinetTile, CabinetTiles } from "@/components/cabinet/surface";
import { useToast } from "@/components/cabinet/toast";
import { Button, Input, Note } from "@/components/cabinet/ui";
import { getDeviceLimit, resolvePlanLabel, resolveTrafficStatusText } from "@/lib/access-policy";
import {
  checkChannelSubscriberStatus,
  claimChannelBonus,
  getEmailAuthStatus,
  registerByEmail,
  setWebSessionToken,
  startTelegramLink,
  type EmailAuthStatusResult,
  type TelegramLinkStartResult,
  verifyEmailToken,
} from "@/lib/api";
import { isEmailAuthPublicReady } from "@/lib/email-auth-readiness";
import { userFacingErrorMessage } from "@/lib/public-error-messages";
import { usePortalSession } from "@/lib/session";

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
  const { showToast } = useToast();
  const [bonusCheck, setBonusCheck] = useState<BonusCheckState | null>(null);
  const [bonusMessage, setBonusMessage] = useState("");
  const [bonusError, setBonusError] = useState("");
  const [bonusBusy, setBonusBusy] = useState<"check" | "claim" | "">("");
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
  const [emailAuthStatus, setEmailAuthStatus] = useState<EmailAuthStatusResult | null>(null);
  const [emailAuthChecked, setEmailAuthChecked] = useState(false);

  useEffect(() => {
    let cancelled = false;

    getEmailAuthStatus()
      .then((payload) => {
        if (!cancelled) setEmailAuthStatus(payload);
      })
      .catch(() => {
        if (!cancelled) setEmailAuthStatus(null);
      })
      .finally(() => {
        if (!cancelled) setEmailAuthChecked(true);
      });

    return () => {
      cancelled = true;
    };
  }, []);

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
  const emailAuthReady = isEmailAuthPublicReady(emailAuthStatus);
  const channelBonusDays = bonusCheck?.bonusDays || user?.bonuses?.channel_bonus?.premium_days || 10;
  const channelBonusClaimedAt = user?.bonuses?.channel_bonus?.claimed_at || null;
  const channelBonusReady = Boolean(user?.bonuses?.channel_bonus?.can_claim);
  const canClaimBonus = !channelBonusClaimedAt && (channelBonusReady || Boolean(bonusCheck?.subscriber && !bonusCheck.alreadyClaimed));
  const canLinkEmail = !linkedEmail && emailAuthReady;
  const emailLinkUnavailable = !linkedEmail && emailAuthChecked && !emailAuthReady;
  const bonusStatusText =
    bonusMessage ||
    (channelBonusClaimedAt
      ? `Бонус уже добавлен ${formatDate(channelBonusClaimedAt)}.`
      : bonusCheck?.message || (channelBonusReady ? `Можно забрать +${channelBonusDays} дней.` : "Проверьте подписку на канал."));

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
      if (!payload.already_claimed) showToast(`Бонус +${days} дней добавлен`, "success");
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
      showToast("Письмо с кодом отправлено", "success");
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
      showToast("Email подтвержден и привязан", "success");
    } catch (error) {
      setEmailLinkError(userFacingErrorMessage(error, "Не удалось подтвердить email. Проверьте код и попробуйте еще раз."));
    } finally {
      setEmailLinkBusy("");
    }
  };

  return (
    <main className="cab-page">
      <CabinetStatus
        title="Аккаунт"
        meta={profileName}
        body={dash?.is_active ? "Вход, устройства и бонусы этого профиля." : "Продлите доступ или откройте поддержку, если что-то не сходится."}
        tone={dash?.is_active ? "success" : "warning"}
        emblem={icon("account_circle", "h-7 w-7")}
        action={
          <Button href="/subscription/" className="w-full sm:w-auto">
            Продлить
          </Button>
        }
      />

      <section className="flex flex-col gap-2.5">
        <h2 className="cab-eyebrow px-1">Профиль</h2>
        <CabinetTiles>
          <CabinetTile icon={icon("verified_user")} label="Доступ" value={resolvePlanLabel(dash, user)} hint={resolveTrafficStatusText(dash, user)} tone="success" href="/subscription/" />
          <CabinetTile icon={icon("calendar_month")} label="Срок" value={formatDate(dash?.expiry_at || user?.expiry_at)} hint="По профилю" tone="neutral" />
          <CabinetTile icon={icon("devices")} label="Устройства" value={`до ${deviceLimit}`} hint="Лимит профиля" tone="neutral" href="/devices/" />
        </CabinetTiles>
      </section>

      <CabinetGroup title="Вход и восстановление">
        <CabinetRow
          icon={icon("send")}
          label="Telegram"
          hint={hasLinkedTelegram ? "Подключен к этому профилю" : "Для входа, бонуса и восстановления"}
          value={telegramName}
          action={
            hasLinkedTelegram ? (
              <AppRouteLink href={supportLink} className="cab-link">
                Поддержка
              </AppRouteLink>
            ) : (
              <button
                type="button"
                onClick={() => void onTelegramLink()}
                disabled={telegramLinkBusy}
                className="cab-link"
              >
                {telegramLinkBusy ? "Открываем..." : "Подключить Telegram"}
              </button>
            )
          }
        />
        <CabinetRow
          icon={icon("alternate_email")}
          label="Email"
          hint={linkedEmail ? "Дополнительный вход подключен" : emailAuthReady ? "Можно добавить к этому профилю" : "Пока входите через Telegram или поддержку"}
          value={linkedEmail || (emailAuthReady ? "доступен" : emailAuthChecked ? "недоступен" : "проверяем")}
          action={
            canLinkEmail ? (
              <a href="#email-link" className="cab-link">
                Добавить
              </a>
            ) : null
          }
        />
      </CabinetGroup>

      {emailLinkUnavailable ? (
        <Note tone="info">Email-вход временно недоступен. Используйте Telegram, а если нужно восстановить доступ, напишите в поддержку.</Note>
      ) : null}

      {telegramLinkError ? (
        <div className="cab-note" data-tone="danger">{telegramLinkError}</div>
      ) : telegramLinkPayload ? (
        telegramLinkPayload.linked ? (
          <div className="cab-note" data-tone="success">Telegram уже подключен к этому профилю.</div>
        ) : (
          <div className="cab-note flex flex-wrap items-center justify-between gap-3" data-tone="info">
            <span className="font-semibold">Откройте бота и завершите привязку Telegram.</span>
            <Button variant="secondary" size="sm" href={telegramLinkPayload.bot_url || supportLink} target="_blank" hardNavigate={false}>
              Открыть бота
            </Button>
          </div>
        )
      ) : null}

      {canLinkEmail ? (
        <section id="email-link" className="scroll-mt-24 space-y-2">
          <div className="px-1">
            <h2 className="cab-eyebrow">Подключить email к текущему аккаунту</h2>
          </div>
          <div className="cab-panel p-4">
            <div className="grid gap-5 lg:grid-cols-[1fr_0.9fr]">
              <form className="space-y-3" onSubmit={onEmailLinkRequest}>
                <Input
                  value={emailLinkEmail}
                  onChange={(event) => setEmailLinkEmail(event.target.value)}
                  type="email"
                  placeholder="name@example.com"
                  autoComplete="email"
                  required
                />
                <Input
                  value={emailLinkName}
                  onChange={(event) => setEmailLinkName(event.target.value)}
                  placeholder="Как обращаться"
                  autoComplete="name"
                />
                <Input
                  value={emailLinkPassword}
                  onChange={(event) => setEmailLinkPassword(event.target.value)}
                  type="password"
                  placeholder="Минимум 10 символов"
                  autoComplete="new-password"
                  minLength={10}
                  required
                />
                <Button type="submit" loading={emailLinkBusy === "request"} disabled={emailLinkBusy !== ""}>
                  Отправить письмо
                </Button>
              </form>

              <form className="space-y-3" onSubmit={onEmailLinkVerify}>
                <Input
                  value={emailLinkToken}
                  onChange={(event) => setEmailLinkToken(event.target.value)}
                  placeholder="Код подтверждения"
                  autoComplete="one-time-code"
                  required
                />
                <Button type="submit" variant="secondary" loading={emailLinkBusy === "verify"} disabled={emailLinkBusy !== ""}>
                  Подтвердить email
                </Button>
                {emailLinkMessage ? <Note tone="success">{emailLinkMessage}</Note> : null}
                {emailLinkError ? <Note tone="danger">{emailLinkError}</Note> : null}
              </form>
            </div>
          </div>
        </section>
      ) : emailLinkMessage ? (
        <p className="px-1 text-sm font-semibold text-[color:var(--atlas-primary)]">{emailLinkMessage}</p>
      ) : null}

      <CabinetGroup title="Telegram-бонус">
        <CabinetRow
          icon={icon("campaign")}
          label="Канал"
          hint="Официальные новости и бонус"
          value="@pokrov_vpn"
          action={
            channelLink ? (
              <AppRouteLink href={channelLink} target="_blank" hardNavigate={false} className="cab-link">
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
              className="cab-link"
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
              className="cab-link"
            >
              {bonusBusy === "claim" ? "Добавляем..." : `Забрать +${channelBonusDays} дней`}
            </button>
          }
        />
      </CabinetGroup>

      <section className="flex flex-col gap-2.5">
        <h2 className="cab-eyebrow px-1">Действия</h2>
        <CabinetActionGrid>
          <CabinetActionCard icon={icon("devices")} title="Устройства" hint="Связанные телефоны и компьютеры" href="/devices/" />
          <CabinetActionCard icon={icon("download")} title="Загрузки" hint="Android и Windows" href="/downloads/" />
          <CabinetActionCard icon={icon("support_agent")} title="Поддержка" hint="Обращения, вложения и Telegram" href="/support/" />
        </CabinetActionGrid>
      </section>
    </main>
  );
}
