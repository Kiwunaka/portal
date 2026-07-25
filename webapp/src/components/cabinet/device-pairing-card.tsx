"use client";

import { Clock3, Link2, QrCode, ShieldCheck, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import CopyButton from "@/components/cabinet/copy-button";
import SubscriptionQrCard from "@/components/subscription-qr-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Note } from "@/components/ui/note";
import {
  cancelDevicePairingCode,
  issueDevicePairingCode,
  type DevicePairingCode,
} from "@/lib/api";

function remainingSeconds(expiresAt: string | null, now: number): number {
  if (!expiresAt) return 0;
  const value = new Date(expiresAt).getTime();
  if (!Number.isFinite(value)) return 0;
  return Math.max(0, Math.ceil((value - now) / 1000));
}

function countdownLabel(seconds: number): string {
  const minutes = Math.floor(seconds / 60);
  const rest = seconds % 60;
  return `${minutes}:${String(rest).padStart(2, "0")}`;
}

export default function DevicePairingCard() {
  const [pairing, setPairing] = useState<DevicePairingCode | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [now, setNow] = useState(() => Date.now());

  const secondsLeft = useMemo(() => remainingSeconds(pairing?.expires_at || null, now), [now, pairing?.expires_at]);
  const active = Boolean(pairing?.status === "active" && pairing.code && secondsLeft > 0);

  useEffect(() => {
    if (!pairing || pairing.status !== "active") return;
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [pairing]);

  const issue = async (): Promise<void> => {
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      const next = await issueDevicePairingCode();
      setPairing(next);
      setNow(Date.now());
    } catch (caught) {
      setError(String((caught as { message?: string })?.message || "Не удалось создать код."));
    } finally {
      setBusy(false);
    }
  };

  const cancel = async (): Promise<void> => {
    if (!pairing || busy) return;
    setBusy(true);
    setError("");
    try {
      await cancelDevicePairingCode(pairing.id);
      setPairing(null);
    } catch (caught) {
      setError(String((caught as { message?: string })?.message || "Не удалось отменить код."));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card className="flex flex-col gap-4" data-testid="device-pairing-card">
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-center gap-3">
          <span className="grid size-10 shrink-0 place-items-center rounded-[12px] bg-brand-soft text-brand">
            <QrCode size={20} strokeWidth={2} aria-hidden="true" />
          </span>
          <div>
            <h2 className="text-base font-bold text-ink">Добавить устройство</h2>
            <p className="mt-0.5 text-sm leading-5 text-ink-muted">QR для телефона или код для Android TV</p>
          </div>
        </div>
        {active ? <Badge tone="success" dot>{countdownLabel(secondsLeft)}</Badge> : null}
      </div>

      {!pairing ? (
        <>
          <Note tone="neutral">Код действует 10 минут и только один раз. Он даёт доступ к аккаунту, но не раскрывает ссылку подписки.</Note>
          {error ? <Note tone="danger">{error}</Note> : null}
          <Button onClick={() => void issue()} loading={busy} disabled={busy} data-testid="device-pairing-issue">
            <Link2 size={18} strokeWidth={2} aria-hidden="true" />
            Создать код
          </Button>
        </>
      ) : active ? (
        <div className="grid gap-5 md:grid-cols-[240px_1fr] md:items-center">
          <div className="flex justify-center md:justify-start">
            <SubscriptionQrCard value={pairing.pairing_uri || ""} active alt="QR-код привязки устройства POKROV" />
          </div>
          <div className="flex min-w-0 flex-col gap-3">
            <div>
              <p className="text-xs font-bold tracking-[0.08em] text-ink-muted uppercase">Код вручную</p>
              <p className="mt-1 font-mono text-3xl font-bold tracking-[0.14em] text-ink" data-testid="device-pairing-code">
                {pairing.code}
              </p>
            </div>
            <p className="text-sm leading-6 text-ink-soft">
              На новом устройстве откройте POKROV → «Войти по коду» и введите восемь символов.
            </p>
            <div className="flex flex-wrap gap-2">
              <CopyButton text={pairing.code || ""} label="Скопировать код" variant="secondary" />
              <Button variant="ghost" onClick={() => void cancel()} disabled={busy}>
                <X size={18} strokeWidth={2} aria-hidden="true" />
                Отменить
              </Button>
            </div>
            {error ? <Note tone="danger">{error}</Note> : null}
          </div>
        </div>
      ) : (
        <>
          <Note tone="warning">Код истёк или уже закрыт. Он больше не может привязать устройство.</Note>
          {error ? <Note tone="danger">{error}</Note> : null}
          <Button onClick={() => void issue()} loading={busy} disabled={busy}>
            <Clock3 size={18} strokeWidth={2} aria-hidden="true" />
            Создать новый код
          </Button>
        </>
      )}

      <div className="flex items-start gap-2 border-t border-line pt-3 text-xs leading-5 text-ink-muted">
        <ShieldCheck size={16} strokeWidth={2} aria-hidden="true" className="mt-0.5 shrink-0 text-brand" />
        После успешного входа код сразу закрывается. Отвязать устройство можно в списке устройств.
      </div>
    </Card>
  );
}
