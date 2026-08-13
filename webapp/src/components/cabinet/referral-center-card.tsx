"use client";

import { Clock3, Gift, Send, ShieldCheck, Users } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import CopyButton from "@/components/cabinet/copy-button";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Note } from "@/components/ui/note";
import { SkeletonBlock, SkeletonRegion } from "@/components/ui/skeleton";
import { fetchReferralSummary, type ReferralHistoryStatus, type ReferralSummary } from "@/lib/api";

const STATUS_COPY: Record<ReferralHistoryStatus, { label: string; tone: "neutral" | "info" | "warning" | "success" }> = {
  invited: { label: "Приглашён", tone: "neutral" },
  review: { label: "Проверка", tone: "warning" },
  activated: { label: "Активирован", tone: "info" },
  hold: { label: "Ожидание", tone: "warning" },
  paid: { label: "Оплатил", tone: "info" },
  rewarded: { label: "Начислено", tone: "success" },
};

function formatDate(value: string | null): string {
  if (!value) return "Дата уточняется";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "Дата уточняется";
  return new Intl.DateTimeFormat("ru-RU", { day: "numeric", month: "short", year: "numeric" }).format(parsed);
}

export default function ReferralCenterCard() {
  const [summary, setSummary] = useState<ReferralSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async (): Promise<void> => {
    setLoading(true);
    setError("");
    try {
      setSummary(await fetchReferralSummary());
    } catch {
      setError("Реферальный центр временно недоступен");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const share = async (): Promise<void> => {
    if (!summary?.link) return;
    const payload = {
      title: "POKROV VPN",
      text: "Моя ссылка на POKROV VPN",
      url: summary.link,
    };
    if (navigator.share) {
      try {
        await navigator.share(payload);
      } catch {
        // Native share cancellation is not an error state.
      }
      return;
    }
    await navigator.clipboard.writeText(summary.link);
  };

  if (loading) {
    return (
      <SkeletonRegion label="Загружаем реферальный центр">
        <SkeletonBlock className="h-72" />
      </SkeletonRegion>
    );
  }

  if (error || !summary) {
    return (
      <Card className="flex flex-col gap-4">
        <Note tone="warning">{error || "Реферальный центр временно недоступен"}</Note>
        <Button variant="secondary" onClick={() => void load()}>Повторить</Button>
      </Card>
    );
  }

  const metrics = [
    { label: "Приглашены", value: summary.conversion.invited, icon: Users },
    { label: "Оплатили", value: summary.conversion.paid, icon: ShieldCheck },
    { label: "Награды", value: summary.conversion.rewarded, icon: Gift },
  ];

  return (
    <Card className="flex flex-col gap-5" data-testid="referral-center">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <span className="grid size-10 shrink-0 place-items-center rounded-[12px] bg-brand-soft text-brand">
            <Users size={20} strokeWidth={2} aria-hidden="true" />
          </span>
          <div>
            <h2 className="text-base font-bold text-ink">Реферальный центр</h2>
            <p className="mt-0.5 text-sm leading-5 text-ink-muted">Статусы и конверсия без имён приглашённых</p>
          </div>
        </div>
        <Badge tone="success">+{summary.bonus_days} дн. после условий</Badge>
      </div>

      <div className="grid grid-cols-3 gap-2">
        {metrics.map(({ label, value, icon: Icon }) => (
          <div key={label} className="rounded-control border border-line bg-canvas-alt p-3">
            <Icon size={17} strokeWidth={2} aria-hidden="true" className="text-brand" />
            <p className="mt-2 text-xl font-bold text-ink">{value}</p>
            <p className="mt-0.5 text-xs text-ink-muted">{label}</p>
          </div>
        ))}
      </div>

      <div className="rounded-control border border-line bg-surface p-3.5">
        <p className="text-xs font-bold tracking-[0.08em] text-ink-muted uppercase">Ваша ссылка</p>
        <p className="mt-1 truncate text-sm font-semibold text-ink" data-testid="referral-link">
          {summary.link || "Ссылка появится после создания кода"}
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          <CopyButton text={summary.link} disabled={!summary.link} label="Скопировать" variant="secondary" />
          <Button variant="ghost" disabled={!summary.link} onClick={() => void share()}>
            <Send size={18} strokeWidth={2} aria-hidden="true" />
            Поделиться
          </Button>
        </div>
      </div>

      <div>
        <div className="mb-2 flex items-center justify-between gap-3">
          <p className="text-xs font-bold tracking-[0.08em] text-ink-muted uppercase">Последние приглашения</p>
          <span className="text-xs text-ink-muted">Оплатили {summary.conversion.paid_pct}%</span>
        </div>
        {summary.history.length ? (
          <div className="divide-y divide-line overflow-hidden rounded-control border border-line">
            {summary.history.slice(0, 6).map((item, index) => {
              const status = STATUS_COPY[item.status] || STATUS_COPY.invited;
              return (
                <div key={item.id} className="flex items-center gap-3 px-3.5 py-3">
                  <Clock3 size={17} strokeWidth={2} aria-hidden="true" className="shrink-0 text-ink-muted" />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-semibold text-ink">Приглашение №{summary.history.length - index}</p>
                    <p className="mt-0.5 text-xs text-ink-muted">{formatDate(item.created_at)}</p>
                  </div>
                  <Badge tone={status.tone}>{status.label}</Badge>
                </div>
              );
            })}
          </div>
        ) : (
          <Note tone="neutral">Приглашений пока нет. Здесь появятся только обезличенные статусы.</Note>
        )}
      </div>

      <p className="flex items-start gap-2 text-xs leading-5 text-ink-muted">
        <ShieldCheck size={16} strokeWidth={2} aria-hidden="true" className="mt-0.5 shrink-0 text-brand" />
        {summary.privacy}
      </p>
    </Card>
  );
}
