"use client";

import { BadgeCheck, CalendarCheck, CircleCheck, CircleHelp, CreditCard, KeyRound, LifeBuoy, QrCode, Search } from "lucide-react";

import { StatusHero } from "@/components/cabinet/status-hero";
import { Button } from "@/components/ui/button";
import { GroupedSection, Row } from "@/components/ui/grouped";
import { Input } from "@/components/ui/input";
import { Note } from "@/components/ui/note";
import { ActionCard, ActionGrid } from "@/components/ui/tiles";
import { useToast } from "@/components/ui/toast";
import { resolvePlanLabel } from "@/lib/access-policy";
import { fetchAccessKeyStatus, redeemAccessKey, type AccessKeyStatusPayload } from "@/lib/api";
import { usePortalSession } from "@/lib/session";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { formatDevicesLimit } from "@/lib/ru-plural";

function normalizeKey(value: string): string {
  return String(value || "").trim().toUpperCase();
}

function looksLikeConnectionLink(value: string): boolean {
  const normalized = String(value || "").trim().toLowerCase();
  return (
    normalized.startsWith("http://") ||
    normalized.startsWith("https://") ||
    normalized.includes("connect.pokrov.space") ||
    normalized.includes("/s8kx2mp7qr4wt/")
  );
}

const CONNECTION_LINK_ERROR =
  "Это ссылка подключения, а не код активации. Ее нужно вставлять в совместимый клиент, а код оплаты или подарка вводится здесь.";

function formatDate(value?: string | null): string {
  if (!value) return "не использован";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "не задан";
  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "long",
  }).format(parsed);
}

export default function RedeemPage() {
  const searchParams = useSearchParams();
  const { user, dash, refresh } = usePortalSession();
  const { showToast } = useToast();
  const [keyInput, setKeyInput] = useState(() => normalizeKey(searchParams.get("key") || ""));
  const [status, setStatus] = useState<AccessKeyStatusPayload | null>(null);
  const [lookupBusy, setLookupBusy] = useState(false);
  const [redeemBusy, setRedeemBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const lookup = async (rawKey?: string): Promise<AccessKeyStatusPayload | null> => {
    const rawValue = rawKey ?? keyInput;
    if (looksLikeConnectionLink(rawValue)) {
      setStatus(null);
      setMessage("");
      setError(CONNECTION_LINK_ERROR);
      return null;
    }
    const key = normalizeKey(rawValue);
    if (!key) {
      setError("Введите код, чтобы мы могли его проверить.");
      return null;
    }

    setLookupBusy(true);
    setError("");
    setMessage("");
    try {
      const nextStatus = await fetchAccessKeyStatus(key);
      setStatus(nextStatus);
      if (!nextStatus.exists) {
        setMessage("Такой код не найден. Проверьте, не потерялся ли символ.");
      } else if (nextStatus.redeemed) {
        setMessage("Этот код уже был использован. Нужна помощь? Откройте поддержку.");
      } else {
        setMessage("Код найден. Его можно активировать в текущем профиле.");
      }
      return nextStatus;
    } catch (nextError) {
      setError(String((nextError as { message?: string })?.message || nextError || "Не удалось проверить код."));
      return null;
    } finally {
      setLookupBusy(false);
    }
  };

  const onRedeem = async (): Promise<void> => {
    const nextStatus = status || (await lookup());
    if (!nextStatus) return;
    if (!nextStatus.exists) {
      setError("Такой код не найден.");
      return;
    }
    if (nextStatus.redeemed) {
      setError("Код уже был использован. Для восстановления лучше открыть поддержку.");
      return;
    }

    setRedeemBusy(true);
    setError("");
    setMessage("");
    try {
      const payload = await redeemAccessKey(nextStatus.key);
      setStatus(payload.status);
      await refresh();
      setMessage(`Код ${payload.key} активирован. Профиль уже обновлен.`);
      showToast("Код активирован", "success");
    } catch (nextError) {
      const errorText = String((nextError as { message?: string })?.message || nextError || "Не удалось активировать код.");
      setError(errorText);
      showToast("Не удалось активировать код", "danger");
    } finally {
      setRedeemBusy(false);
    }
  };

  useEffect(() => {
    const nextKey = normalizeKey(searchParams.get("key") || "");
    if (!nextKey) return;
    setKeyInput(nextKey);
    void lookup(nextKey);
    // searchParams is stable enough here and we only react to URL changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  return (
    <main className="mx-auto flex w-full max-w-[860px] flex-col gap-5">
      <StatusHero
        title="Активировать код"
        meta={resolvePlanLabel(dash, user)}
        body="Введите код оплаты, подарка или промокод. Личная ссылка подключения сюда не подходит."
        tone={status?.exists && !status.redeemed ? "success" : status?.redeemed ? "warning" : "neutral"}
        icon={KeyRound}
        action={
          <Button variant="secondary" href="/subscription/checkout/" className="w-full sm:w-auto">
            Купить доступ
          </Button>
        }
      />

      <GroupedSection title="Код">
        <div className="space-y-3 p-4">
          <Input
            value={keyInput}
            onChange={(event) => setKeyInput(normalizeKey(event.target.value))}
            placeholder="Код активации"
          />
          <div className="flex flex-col gap-3 sm:flex-row">
            <Button variant="secondary" loading={lookupBusy} onClick={() => void lookup()}>
              Проверить
            </Button>
            <Button loading={redeemBusy} onClick={() => void onRedeem()}>
              Активировать
            </Button>
          </div>
          <p className="text-xs leading-5 text-ink-muted">
            Если у вас длинная ссылка connect.pokrov.space, откройте ручную настройку в разделе доступа.
          </p>
        </div>
      </GroupedSection>

      {message ? <Note tone="success">{message}</Note> : null}
      {error ? <Note tone="danger">{error}</Note> : null}

      <GroupedSection title="Статус">
        {status ? (
          <>
            <Row icon={status.exists ? CircleCheck : CircleHelp} label="Проверка" hint={status.exists ? "Код найден" : "Код не найден"} value={status.exists ? "найден" : "не найден"} />
            <Row icon={BadgeCheck} label="Что дает" hint={status.plan?.label || status.kind || "Уточним после проверки"} value={formatDevicesLimit(status.device_limit || 1)} />
            <Row icon={CalendarCheck} label="Использован" hint="По данным кабинета" value={formatDate(status.redeemed_at)} />
          </>
        ) : (
          <Row icon={Search} label="Ждет проверки" hint="Введите код и нажмите Проверить" value="не запускалась" />
        )}
      </GroupedSection>

      <section className="flex flex-col gap-2.5">
        <h2 className="px-1 text-xs font-bold tracking-[0.08em] text-ink-muted uppercase">Что дальше</h2>
        <ActionGrid className="sm:grid-cols-3">
          <ActionCard icon={CreditCard} title="Купить доступ" hint="Если кода еще нет" href="/subscription/checkout/" />
          <ActionCard icon={LifeBuoy} title="Поддержка" hint="Если код уже использован или не найден" href="/support/" />
          <ActionCard icon={QrCode} title="Ссылка для совместимого клиента" hint="Только если приложение не подключилось само" href="/subscription/#manual-setup" />
        </ActionGrid>
      </section>
    </main>
  );
}
