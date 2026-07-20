"use client";

import { useEffect, useState, type FormEvent } from "react";
import {
  AtSign,
  CalendarCheck,
  CircleCheck,
  CirclePlus,
  CircleUserRound,
  Download,
  LifeBuoy,
  Megaphone,
  MonitorSmartphone,
  Send,
  ShieldCheck,
} from "lucide-react";

import AppRouteLink from "@/components/app-route-link";
import { StatusHero } from "@/components/cabinet/status-hero";
import { Button } from "@/components/ui/button";
import { GroupedSection, Row } from "@/components/ui/grouped";
import { Input } from "@/components/ui/input";
import { Note } from "@/components/ui/note";
import { ActionCard, ActionGrid, Tile, TileGrid } from "@/components/ui/tiles";
import { useToast } from "@/components/ui/toast";
import { getDeviceLimit, resolvePlanLabel, resolveTrafficStatusText } from "@/lib/access-policy";
import {
  checkChannelSubscriberStatus,
  claimChannelBonus,
  fetchBonuses,
  getEmailAuthStatus,
  registerByEmail,
  setWebSessionToken,
  startTelegramLink,
  type BonusPayload,
  type EmailAuthStatusResult,
  type TelegramLinkStartResult,
  verifyEmailToken,
} from "@/lib/api";
import { isEmailAuthPublicReady } from "@/lib/email-auth-readiness";
import { userFacingErrorMessage } from "@/lib/public-error-messages";
import { usePortalSession } from "@/lib/session";

const LINK_BUTTON_CLASS = "text-sm font-semibold text-brand hover:text-brand-strong disabled:opacity-55";

function formatDate(value?: string | null): string {
  if (!value) return "уточняется";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "уточняется";
  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "long",
  }).format(parsed);
}

function positiveDays(value: unknown, fallback: number): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? Math.floor(parsed) : fallback;
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
  const [bonusSummary, setBonusSummary] = useState<BonusPayload | null>(null);

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

    fetchBonuses()
      .then((payload) => {
        if (!cancelled) setBonusSummary(payload);
      })
      .catch(() => {
        if (!cancelled) setBonusSummary(null);
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
  const userChannelBonus = user?.bonuses?.channel_bonus;
  const summaryChannelBonus = bonusSummary?.channel;
  const channelBonusOfferDays = positiveDays(
    bonusCheck?.bonusDays ?? summaryChannelBonus?.offer_days ?? userChannelBonus?.offer_days,
    5,
  );
  const channelBonusClaimedAt = summaryChannelBonus?.claimed_at ?? userChannelBonus?.claimed_at ?? null;
  const channelBonusClaimed = Boolean(summaryChannelBonus?.claimed || channelBonusClaimedAt || bonusCheck?.alreadyClaimed);
  const channelBonusClaimedDays = positiveDays(
    summaryChannelBonus?.claimed_days ??
      userChannelBonus?.claimed_days ??
      (channelBonusClaimed ? userChannelBonus?.premium_days : undefined),
    channelBonusOfferDays,
  );
  const channelBonusReady = Boolean(user?.bonuses?.channel_bonus?.can_claim);
  const canClaimBonus = !channelBonusClaimed && (channelBonusReady || Boolean(bonusCheck?.subscriber && !bonusCheck.alreadyClaimed));
  const canLinkEmail = !linkedEmail && emailAuthReady;
  const emailLinkUnavailable = !linkedEmail && emailAuthChecked && !emailAuthReady;
  const bonusStatusText =
    bonusMessage ||
    (channelBonusClaimed
      ? `Получено +${channelBonusClaimedDays} дней${channelBonusClaimedAt ? ` ${formatDate(channelBonusClaimedAt)}` : ""}.`
      : bonusCheck?.message ||
        (channelBonusReady ? `Можно забрать +${channelBonusOfferDays} дней.` : "Проверьте подписку на канал."));

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
        bonusDays: positiveDays(payload.bonus_days, channelBonusOfferDays),
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
      const days = positiveDays(payload.premium_days, channelBonusOfferDays);
      setBonusCheck({
        subscriber: true,
        alreadyClaimed: true,
        bonusDays: days,
        message: payload.already_claimed ? "Бонус уже был добавлен раньше." : `Бонус +${days} дней добавлен.`,
      });
      setBonusMessage(payload.already_claimed ? "Бонус уже был добавлен раньше." : `Бонус +${days} дней добавлен.`);
      if (!payload.already_claimed) showToast(`Бонус +${days} дней добавлен`, "success");
      const latestSummary = await fetchBonuses().catch(() => null);
      if (latestSummary) setBonusSummary(latestSummary);
      await refresh();
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
    <main className="mx-auto flex w-full max-w-[860px] flex-col gap-5">
      <StatusHero
        title="Аккаунт"
        meta={profileName}
        body={dash?.is_active ? "Вход, устройства и бонусы этого профиля." : "Продлите доступ или откройте поддержку, если что-то не сходится."}
        tone={dash?.is_active ? "success" : "warning"}
        icon={CircleUserRound}
        action={
          <Button href="/subscription/" className="w-full sm:w-auto">
            Продлить
          </Button>
        }
      />

      <section className="flex flex-col gap-2.5">
        <h2 className="px-1 text-xs font-bold tracking-[0.08em] text-ink-soft uppercase">Профиль</h2>
        <TileGrid className="xl:grid-cols-3">
          <Tile icon={ShieldCheck} label="Доступ" value={resolvePlanLabel(dash, user)} hint={resolveTrafficStatusText(dash, user)} tone="success" href="/subscription/" />
          <Tile icon={CalendarCheck} label="Срок" value={formatDate(dash?.expiry_at || user?.expiry_at)} hint="По профилю" tone="neutral" />
          <Tile icon={MonitorSmartphone} label="Устройства" value={`до ${deviceLimit}`} hint="Лимит профиля" tone="neutral" href="/devices/" />
        </TileGrid>
      </section>

      <GroupedSection title="Вход и восстановление">
        <Row
          icon={Send}
          label="Telegram"
          hint={hasLinkedTelegram ? "Подключен к этому профилю" : "Для входа, бонуса и восстановления"}
          value={telegramName}
          action={
            hasLinkedTelegram ? (
              <AppRouteLink href={supportLink} className={LINK_BUTTON_CLASS}>
                Поддержка
              </AppRouteLink>
            ) : (
              <button
                type="button"
                onClick={() => void onTelegramLink()}
                disabled={telegramLinkBusy}
                className={LINK_BUTTON_CLASS}
              >
                {telegramLinkBusy ? "Открываем..." : "Подключить Telegram"}
              </button>
            )
          }
        />
        <Row
          icon={AtSign}
          label="Email"
          hint={linkedEmail ? "Дополнительный вход подключен" : emailAuthReady ? "Можно добавить к этому профилю" : "Пока входите через Telegram или поддержку"}
          value={linkedEmail || (emailAuthReady ? "доступен" : emailAuthChecked ? "недоступен" : "проверяем")}
          action={
            canLinkEmail ? (
              <a href="#email-link" className={LINK_BUTTON_CLASS}>
                Добавить
              </a>
            ) : null
          }
        />
      </GroupedSection>

      {emailLinkUnavailable ? (
        <Note tone="info">Email-вход временно недоступен. Используйте Telegram, а если нужно восстановить доступ, напишите в поддержку.</Note>
      ) : null}

      {telegramLinkError ? (
        <Note tone="danger">{telegramLinkError}</Note>
      ) : telegramLinkPayload ? (
        telegramLinkPayload.linked ? (
          <Note tone="success">Telegram уже подключен к этому профилю.</Note>
        ) : (
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-control border border-info-line bg-info-bg px-3.5 py-2.5 text-sm text-info-text">
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
            <h2 className="text-xs font-bold tracking-[0.08em] text-ink-soft uppercase">Подключить email к текущему аккаунту</h2>
          </div>
          <div className="rounded-card border border-line bg-surface p-4 shadow-soft">
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
        <p className="px-1 text-sm font-semibold text-brand">{emailLinkMessage}</p>
      ) : null}

      <GroupedSection title="Telegram-бонус">
        <Row
          icon={Megaphone}
          label="Канал"
          hint="Официальные новости и бонус"
          value="@pokrov_vpn"
          action={
            channelLink ? (
              <AppRouteLink href={channelLink} target="_blank" hardNavigate={false} className={LINK_BUTTON_CLASS}>
                Открыть
              </AppRouteLink>
            ) : null
          }
        />
        <Row
          icon={CircleCheck}
          label="Проверка"
          hint={bonusStatusText}
          action={
            <button
              type="button"
              onClick={() => void onCheckBonus()}
              disabled={bonusBusy !== ""}
              className={LINK_BUTTON_CLASS}
            >
              {bonusBusy === "check" ? "Проверяем..." : "Проверить подписку"}
            </button>
          }
        />
        <Row
          icon={CirclePlus}
          label={channelBonusClaimed ? `Получено +${channelBonusClaimedDays} дней` : `Бонус +${channelBonusOfferDays} дней`}
          hint={bonusError || (channelBonusClaimed ? "Уже добавлен" : "После подтверждения канала")}
          action={
            <button
              type="button"
              onClick={() => void onClaimBonus()}
              disabled={bonusBusy !== "" || channelBonusClaimed || (!canClaimBonus && !bonusCheck?.subscriber)}
              className={LINK_BUTTON_CLASS}
            >
              {bonusBusy === "claim" ? "Добавляем..." : channelBonusClaimed ? "Получено" : `Забрать +${channelBonusOfferDays} дней`}
            </button>
          }
        />
      </GroupedSection>

      <section className="flex flex-col gap-2.5">
        <h2 className="px-1 text-xs font-bold tracking-[0.08em] text-ink-soft uppercase">Действия</h2>
        <ActionGrid className="sm:grid-cols-3">
          <ActionCard icon={MonitorSmartphone} title="Устройства" hint="Связанные телефоны и компьютеры" href="/devices/" />
          <ActionCard icon={Download} title="Загрузки" hint="Android и Windows" href="/downloads/" />
          <ActionCard icon={LifeBuoy} title="Поддержка" hint="Обращения, вложения и Telegram" href="/support/" />
        </ActionGrid>
      </section>
    </main>
  );
}
