"use client";

import { motion, useReducedMotion } from "framer-motion";
import { CircleCheck, Clock3, Gift, Sparkles } from "lucide-react";
import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Note } from "@/components/ui/note";
import { spinBonusWheel, type BonusWheelState } from "@/lib/api";
import { formatDays } from "@/lib/ru-plural";

const MAX_SECTORS = 12;
const MAX_REWARD_DAYS = 365;
const DISCOUNT_VALUES = new Set([5, 7, 10]);

type RewardSector = {
  key: string;
  kind: "days" | "discount";
  value: number;
  label: string;
};

export function validateRewardSectors(raw: unknown): number[] | null {
  if (!Array.isArray(raw) || raw.length === 0 || raw.length > MAX_SECTORS) return null;
  if (!raw.every((value) => Number.isInteger(value) && value > 0 && value <= MAX_REWARD_DAYS)) return null;

  const sectors = raw as number[];
  return new Set(sectors).size === sectors.length ? [...sectors] : null;
}

export function validateRewardDisplaySectors(raw: unknown, legacyRaw: unknown): RewardSector[] | null {
  if (Array.isArray(raw) && raw.length > 0 && raw.length <= MAX_SECTORS) {
    const sectors: RewardSector[] = [];
    const keys = new Set<string>();
    for (const item of raw) {
      if (!item || typeof item !== "object") return null;
      const candidate = item as Record<string, unknown>;
      const kind = candidate.kind;
      const value = candidate.value;
      if (kind !== "days" && kind !== "discount") return null;
      if (!Number.isInteger(value) || Number(value) <= 0) return null;
      if (kind === "days" && Number(value) > MAX_REWARD_DAYS) return null;
      if (kind === "discount" && !DISCOUNT_VALUES.has(Number(value))) return null;
      const expectedKey = `${kind}:${Number(value)}`;
      const key = typeof candidate.key === "string" ? candidate.key : expectedKey;
      if (key !== expectedKey || keys.has(key)) return null;
      keys.add(key);
      sectors.push({
        key,
        kind,
        value: Number(value),
        label: kind === "days" ? `+${Number(value)} дн.` : `−${Number(value)}%`,
      });
    }
    return sectors;
  }
  const legacy = validateRewardSectors(legacyRaw);
  return legacy?.map((value) => ({ key: `days:${value}`, kind: "days", value, label: `+${value}` })) ?? null;
}

function pointOnCircle(angleDegrees: number, radius: number): { x: number; y: number } {
  const angle = (angleDegrees * Math.PI) / 180;
  return {
    x: 100 + radius * Math.cos(angle),
    y: 100 + radius * Math.sin(angle),
  };
}

function segmentPath(index: number, count: number): string {
  const step = 360 / count;
  const start = pointOnCircle(-90 + index * step, 92);
  const end = pointOnCircle(-90 + (index + 1) * step, 92);
  const largeArc = step > 180 ? 1 : 0;
  return `M 100 100 L ${start.x} ${start.y} A 92 92 0 ${largeArc} 1 ${end.x} ${end.y} Z`;
}

function formatNextSpin(value: string | null): string {
  if (!value) return "Следующая попытка появится после обновления статуса";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "Следующая попытка появится после обновления статуса";
  const formatted = new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(parsed);
  return `Следующая попытка ${formatted}`;
}

function WheelGraphic({ sectors, rotation, spinning, onAnimationComplete }: {
  sectors: RewardSector[];
  rotation: number;
  spinning: boolean;
  onAnimationComplete: () => void;
}) {
  const step = 360 / sectors.length;

  return (
    <div className="relative mx-auto w-full max-w-[310px] px-3 pt-3">
      <span
        aria-hidden="true"
        className="absolute top-1 left-1/2 z-10 h-0 w-0 -translate-x-1/2 border-x-[9px] border-t-[16px] border-x-transparent border-t-brand drop-shadow-sm"
      />
      <motion.div
        initial={false}
        animate={{ rotate: rotation }}
        transition={{ duration: spinning ? 1.45 : 0, ease: [0.22, 1, 0.36, 1] }}
        onAnimationComplete={onAnimationComplete}
        data-spinning={spinning ? "true" : "false"}
        className="origin-center rounded-full"
      >
        <svg
          data-wheel
          viewBox="0 0 200 200"
          role="img"
          aria-label={`Рулетка с ${sectors.length} равными секторами`}
          className="h-auto w-full drop-shadow-sm"
        >
          <title>Секторы рулетки</title>
          <desc>Визуальные секторы равны по размеру и не показывают вероятность награды.</desc>
          {sectors.map((sector, index) => {
            const label = pointOnCircle(-90 + (index + 0.5) * step, 59);
            return (
              <g key={sector.key}>
                <path
                  d={segmentPath(index, sectors.length)}
                  fill={index % 2 === 0 ? "var(--pokrov-accent-soft)" : "var(--pokrov-bg-alt)"}
                  stroke="var(--pokrov-line)"
                  strokeWidth="1.5"
                />
                <text
                  x={label.x}
                  y={label.y}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  fill="var(--pokrov-text)"
                  fontSize={sectors.length > 8 ? 8 : 10}
                  fontWeight="700"
                >
                  {sector.label}
                </text>
              </g>
            );
          })}
          <circle cx="100" cy="100" r="18" fill="var(--pokrov-surface)" stroke="var(--pokrov-line)" strokeWidth="2" />
          <circle cx="100" cy="100" r="5" fill="var(--pokrov-accent)" />
        </svg>
      </motion.div>
    </div>
  );
}

export function BonusWheel({
  state,
  onStateChange,
  onCommitted,
}: {
  state: BonusWheelState;
  onStateChange: (state: BonusWheelState) => void;
  onCommitted: () => Promise<void>;
}) {
  const reducedMotion = useReducedMotion();
  const sectors = useMemo(
    () => validateRewardDisplaySectors(state.display_sectors, state.sectors),
    [state.display_sectors, state.sectors],
  );
  const [busy, setBusy] = useState(false);
  const [spinning, setSpinning] = useState(false);
  const [rotation, setRotation] = useState(0);
  const [resultMessage, setResultMessage] = useState("");
  const [actionError, setActionError] = useState("");
  const [sectorSyncError, setSectorSyncError] = useState(false);

  const spin = async (): Promise<void> => {
    if (!sectors || !state.enabled || !state.eligible || !state.can_spin || busy || spinning) return;

    const currentSectors = [...sectors];
    setBusy(true);
    setResultMessage("");
    setActionError("");
    setSectorSyncError(false);
    try {
      const mutation = await spinBonusWheel();
      onStateChange(mutation.state);

      const rewardDays = mutation.reward_days;
      const discountPct = mutation.discount_pct ?? 0;
      if (mutation.reward_kind === "discount" && DISCOUNT_VALUES.has(discountPct)) {
        setResultMessage(`Скидка −${discountPct}% сохранена для одного продления`);
      } else if (Number.isInteger(rewardDays) && rewardDays > 0 && rewardDays <= MAX_REWARD_DAYS) {
        setResultMessage(`Начислено +${formatDays(rewardDays)}`);
      } else {
        setResultMessage("Бонус начислен");
      }

      const targetKey = mutation.sector_key || `${mutation.reward_kind ?? "days"}:${mutation.reward_value ?? rewardDays}`;
      const targetIndex = currentSectors.findIndex((sector) => sector.key === targetKey);
      if (targetIndex < 0) {
        setSectorSyncError(true);
        setSpinning(false);
      } else {
        const targetOffset = 360 - (targetIndex + 0.5) * (360 / currentSectors.length);
        setRotation((current) => current + 720 + targetOffset);
        setSpinning(!reducedMotion);
      }

      await onCommitted();
    } catch {
      setActionError("Не удалось запустить рулетку. Попробуйте ещё раз.");
      setSpinning(false);
    } finally {
      setBusy(false);
    }
  };

  const controlsDisabled = busy || spinning || !state.can_spin || !state.enabled || !state.eligible || !sectors;

  return (
    <Card className="flex h-full flex-col gap-4 overflow-hidden">
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-center gap-3">
          <span className="grid size-10 shrink-0 place-items-center rounded-[12px] bg-brand-soft text-brand">
            <Sparkles size={20} strokeWidth={2} aria-hidden="true" />
          </span>
          <div className="min-w-0">
            <h2 className="text-base font-bold text-ink">Еженедельная рулетка</h2>
            <p className="mt-0.5 text-sm leading-5 text-ink-muted">Одна попытка каждые 7 дней</p>
          </div>
        </div>
        <Badge tone={state.can_spin ? "success" : "neutral"} dot>
          {state.can_spin ? "Доступна" : "Ожидание"}
        </Badge>
      </div>

      {!state.enabled ? (
        <>
          <Note tone="neutral">Колесо пока выключено</Note>
          <Button block disabled>Крутить колесо</Button>
        </>
      ) : !state.eligible ? (
        <>
          <Note tone="warning">Нужна активная платная подписка</Note>
          <Button block disabled>Крутить колесо</Button>
        </>
      ) : !sectors ? (
        <>
          <Note tone="danger">Не удалось синхронизировать сектора</Note>
          <Button block disabled>Крутить колесо</Button>
        </>
      ) : (
        <>
          {sectors.length === 1 ? (
            <div className="flex flex-1 flex-col items-center justify-center gap-3 rounded-card border border-line bg-canvas-alt px-5 py-8 text-center">
              <span className="grid size-14 place-items-center rounded-full bg-brand-soft text-brand">
                <Gift size={25} strokeWidth={1.9} aria-hidden="true" />
              </span>
              <p className="text-base font-bold text-ink">
                Гарантированная награда: {sectors[0].kind === "days" ? `+${formatDays(sectors[0].value)}` : `−${sectors[0].value}%`}
              </p>
            </div>
          ) : (
            <>
              <WheelGraphic
                sectors={sectors}
                rotation={rotation}
                spinning={spinning}
                onAnimationComplete={() => setSpinning(false)}
              />
              <p className="text-center text-xs leading-5 text-ink-muted">Размер сектора не означает вероятность</p>
              {sectors.some((sector) => sector.kind === "discount") ? (
                <p className="text-center text-xs leading-5 text-ink-muted">Скидка действует на одно продление и не складывается с другой скидкой</p>
              ) : null}
            </>
          )}

          {!state.can_spin ? (
            <div className="flex items-center gap-2 rounded-control bg-canvas-alt px-3.5 py-3 text-sm text-ink-soft">
              <Clock3 size={17} strokeWidth={2} aria-hidden="true" className="shrink-0 text-brand" />
              <span>{formatNextSpin(state.next_spin_at)}</span>
            </div>
          ) : null}

          {resultMessage ? (
            <div role="status">
              <Note tone="success" className="flex items-center gap-2">
                <CircleCheck size={17} strokeWidth={2} aria-hidden="true" className="shrink-0" />
                <span>{resultMessage}</span>
              </Note>
            </div>
          ) : null}
          {sectorSyncError ? <Note tone="danger">Не удалось синхронизировать сектора</Note> : null}
          {actionError ? <Note tone="danger">{actionError}</Note> : null}

          <Button block loading={busy} disabled={controlsDisabled} onClick={spin}>
            Крутить колесо
          </Button>
        </>
      )}
    </Card>
  );
}
