"use client";

import { CalendarCheck2, CircleCheck, Clock3, Gift, History, Sparkles, Trophy } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { BonusWheel } from "@/components/cabinet/bonus-wheel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Note } from "@/components/ui/note";
import { SkeletonBlock, SkeletonLine, SkeletonRegion } from "@/components/ui/skeleton";
import {
  checkinBonusCalendar,
  fetchBonusCalendarState,
  fetchBonusHistory,
  fetchBonusWheelState,
  type BonusCalendarState,
  type BonusRewardHistory,
  type BonusRewardHistoryItem,
  type BonusWheelState,
} from "@/lib/api";
import { formatDays } from "@/lib/ru-plural";
import { usePortalSession } from "@/lib/session";

function formatOccurredAt(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "Дата уточняется";
  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(parsed);
}

function historyValue(item: BonusRewardHistoryItem): string {
  if (typeof item.days === "number" && item.days > 0) return `+${formatDays(item.days)}`;
  if (typeof item.discount_pct === "number" && item.discount_pct > 0) return `Скидка ${item.discount_pct}%`;
  return "Без изменения срока";
}

function RewardCardSkeleton({ label }: { label: string }) {
  return (
    <SkeletonRegion label={label}>
      <SkeletonBlock className="h-[430px]" />
    </SkeletonRegion>
  );
}

function RewardLoadError({ title, onRetry }: { title: string; onRetry: () => void }) {
  return (
    <Card className="flex min-h-[250px] flex-col justify-between gap-5">
      <div className="flex items-start gap-3">
        <span className="grid size-10 shrink-0 place-items-center rounded-[12px] bg-danger-bg text-danger-text">
          <Clock3 size={20} strokeWidth={2} aria-hidden="true" />
        </span>
        <div>
          <h2 className="text-base font-bold text-ink">{title}</h2>
          <p className="mt-1 text-sm leading-6 text-ink-muted">Другие награды продолжают работать независимо.</p>
        </div>
      </div>
      <Button variant="secondary" onClick={onRetry}>Повторить</Button>
    </Card>
  );
}

function ActivityCalendar({
  state,
  busy,
  message,
  error,
  onCheckin,
}: {
  state: BonusCalendarState;
  busy: boolean;
  message: string;
  error: string;
  onCheckin: () => Promise<void>;
}) {
  const cycleDay = Number.isInteger(state.calendar_cycle_day) ? Math.max(0, state.calendar_cycle_day) : 0;
  const completedInWeek = cycleDay === 0 ? 0 : cycleDay % 7 || 7;
  const nextCycleDay = cycleDay >= 28 ? 1 : cycleDay + 1;
  const statusMessage = message || (state.checked_in_today ? "Сегодня уже отмечено" : "");

  return (
    <Card className="flex h-full flex-col gap-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-center gap-3">
          <span className="grid size-10 shrink-0 place-items-center rounded-[12px] bg-brand-soft text-brand">
            <CalendarCheck2 size={20} strokeWidth={2} aria-hidden="true" />
          </span>
          <div className="min-w-0">
            <h2 className="text-base font-bold text-ink">Календарь активности</h2>
            <p className="mt-0.5 text-sm leading-5 text-ink-muted">Отмечайтесь каждый день</p>
          </div>
        </div>
        <Badge tone={state.checked_in_today ? "success" : "neutral"} dot>
          {state.checked_in_today ? "Готово" : `День ${nextCycleDay}`}
        </Badge>
      </div>

      {!state.enabled ? (
        <>
          <Note tone="neutral">Календарь пока выключен</Note>
          <Button block disabled>Отметить день</Button>
        </>
      ) : !state.eligible ? (
        <>
          <Note tone="warning">Нужна активная платная подписка</Note>
          <Button block disabled>Отметить день</Button>
        </>
      ) : (
        <>
          <div className="rounded-card border border-line bg-canvas-alt p-4">
            <div className="mb-4 flex items-baseline justify-between gap-3">
              <div>
                <p className="text-xs font-bold tracking-[0.08em] text-ink-muted uppercase">Текущий цикл</p>
                <p className="mt-1 text-2xl font-bold text-ink">{cycleDay} дней</p>
              </div>
              {state.next_milestone ? (
                <span className="text-right text-xs leading-5 text-ink-muted">Ближайшая отметка: {state.next_milestone} дней</span>
              ) : null}
            </div>
            <div className="grid grid-cols-7 gap-1.5" aria-label="Прогресс за семь дней">
              {Array.from({ length: 7 }, (_, index) => {
                const complete = index < completedInWeek;
                return (
                  <div key={index} className="flex flex-col items-center gap-1.5">
                    <span
                      className={`grid aspect-square w-full max-w-10 place-items-center rounded-[10px] border text-xs font-bold ${
                        complete
                          ? "border-ok-line bg-ok-bg text-ok-text"
                          : "border-line bg-surface text-ink-muted"
                      }`}
                      aria-label={`День ${index + 1}: ${complete ? "отмечен" : "не отмечен"}`}
                    >
                      {complete ? <CircleCheck size={16} strokeWidth={2.2} aria-hidden="true" /> : index + 1}
                    </span>
                    <span className="text-[10px] font-medium text-ink-muted">{index + 1}</span>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="flex items-start gap-3 rounded-control border border-info-line bg-info-bg px-3.5 py-3 text-info-text">
            <Trophy size={18} strokeWidth={2} aria-hidden="true" className="mt-0.5 shrink-0" />
            <p className="text-sm leading-6">За каждые 7 дней подряд начисляется 1 дополнительный день доступа.</p>
          </div>

          {statusMessage ? (
            <div role="status">
              <Note tone="success">{statusMessage}</Note>
            </div>
          ) : null}
          {error ? <Note tone="danger">{error}</Note> : null}

          <Button block loading={busy} disabled={!state.can_checkin || busy} onClick={onCheckin}>
            Отметить день
          </Button>
        </>
      )}
    </Card>
  );
}

function RewardHistoryCard({ history, error }: { history: BonusRewardHistory | null; error: string }) {
  const items = Array.isArray(history?.items) ? history.items.slice(0, 6) : [];

  return (
    <Card className="p-0">
      <div className="flex items-center justify-between gap-3 border-b border-line px-4 py-4 sm:px-5">
        <div className="flex items-center gap-3">
          <span className="grid size-9 place-items-center rounded-[10px] bg-brand-soft text-brand">
            <History size={18} strokeWidth={2} aria-hidden="true" />
          </span>
          <div>
            <h2 className="text-base font-bold text-ink">История наград</h2>
            <p className="text-xs text-ink-muted">Последние подтверждённые операции</p>
          </div>
        </div>
        {items.length ? <Badge tone="neutral">{items.length}</Badge> : null}
      </div>

      {error ? (
        <div className="p-4 sm:p-5">
          <Note tone="warning">История временно недоступна</Note>
        </div>
      ) : items.length ? (
        <div className="divide-y divide-line">
          {items.map((item, index) => (
            <div key={`${item.kind}-${item.occurred_at}-${index}`} className="flex items-center gap-3 px-4 py-3.5 sm:px-5">
              <span className="grid size-9 shrink-0 place-items-center rounded-[10px] bg-canvas-alt text-brand">
                {item.kind === "calendar_checkin" ? (
                  <CalendarCheck2 size={17} strokeWidth={2} aria-hidden="true" />
                ) : (
                  <Sparkles size={17} strokeWidth={2} aria-hidden="true" />
                )}
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-semibold text-ink">{item.title}</p>
                <p className="mt-0.5 text-xs text-ink-muted">{formatOccurredAt(item.occurred_at)}</p>
              </div>
              <span className="shrink-0 text-sm font-bold text-brand">{historyValue(item)}</span>
            </div>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center gap-2 px-5 py-9 text-center">
          <Gift size={22} strokeWidth={1.8} aria-hidden="true" className="text-ink-muted" />
          <p className="text-sm font-semibold text-ink">Пока нет подтверждённых наград</p>
          <p className="text-xs leading-5 text-ink-muted">После начисления операция появится здесь.</p>
        </div>
      )}
    </Card>
  );
}

export default function RewardsPage() {
  const { refresh } = usePortalSession();
  const [wheelState, setWheelState] = useState<BonusWheelState | null>(null);
  const [calendarState, setCalendarState] = useState<BonusCalendarState | null>(null);
  const [history, setHistory] = useState<BonusRewardHistory | null>(null);
  const [wheelLoading, setWheelLoading] = useState(true);
  const [calendarLoading, setCalendarLoading] = useState(true);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [wheelError, setWheelError] = useState("");
  const [calendarError, setCalendarError] = useState("");
  const [historyError, setHistoryError] = useState("");
  const [calendarBusy, setCalendarBusy] = useState(false);
  const [calendarMessage, setCalendarMessage] = useState("");
  const [calendarActionError, setCalendarActionError] = useState("");

  useEffect(() => {
    let active = true;

    void Promise.allSettled([
      fetchBonusWheelState(),
      fetchBonusCalendarState(),
      fetchBonusHistory(),
    ]).then(([wheelResult, calendarResult, historyResult]) => {
      if (!active) return;

      if (wheelResult.status === "fulfilled") {
        setWheelState(wheelResult.value);
        setWheelError("");
      } else {
        setWheelError("Колесо временно недоступно");
      }
      setWheelLoading(false);

      if (calendarResult.status === "fulfilled") {
        setCalendarState(calendarResult.value);
        setCalendarError("");
      } else {
        setCalendarError("Календарь временно недоступен");
      }
      setCalendarLoading(false);

      if (historyResult.status === "fulfilled") {
        setHistory(historyResult.value);
        setHistoryError("");
      } else {
        setHistoryError("История временно недоступна");
      }
      setHistoryLoading(false);
    });

    return () => {
      active = false;
    };
  }, []);

  const retryWheel = useCallback(async (): Promise<void> => {
    setWheelLoading(true);
    setWheelError("");
    try {
      setWheelState(await fetchBonusWheelState());
    } catch {
      setWheelError("Колесо временно недоступно");
    } finally {
      setWheelLoading(false);
    }
  }, []);

  const retryCalendar = useCallback(async (): Promise<void> => {
    setCalendarLoading(true);
    setCalendarError("");
    try {
      setCalendarState(await fetchBonusCalendarState());
    } catch {
      setCalendarError("Календарь временно недоступен");
    } finally {
      setCalendarLoading(false);
    }
  }, []);

  const refreshWheelContext = useCallback(async (): Promise<void> => {
    const [wheelResult, , historyResult] = await Promise.allSettled([
      fetchBonusWheelState(),
      refresh(),
      fetchBonusHistory(),
    ]);
    if (wheelResult.status === "fulfilled") {
      setWheelState(wheelResult.value);
      setWheelError("");
    }
    if (historyResult.status === "fulfilled") {
      setHistory(historyResult.value);
      setHistoryError("");
    }
  }, [refresh]);

  const refreshCalendarContext = useCallback(async (): Promise<void> => {
    const [calendarResult, sessionResult, historyResult] = await Promise.allSettled([
      fetchBonusCalendarState(),
      refresh(),
      fetchBonusHistory(),
    ]);
    if (calendarResult.status === "fulfilled") {
      setCalendarState(calendarResult.value);
      setCalendarError("");
    }
    if (historyResult.status === "fulfilled") {
      setHistory(historyResult.value);
      setHistoryError("");
    }
    if (sessionResult.status === "rejected") {
      setCalendarActionError("Награда сохранена. Статус подписки обновится при следующей загрузке.");
    }
  }, [refresh]);

  const checkin = async (): Promise<void> => {
    if (!calendarState?.can_checkin || calendarBusy) return;
    setCalendarBusy(true);
    setCalendarMessage("");
    setCalendarActionError("");
    try {
      const mutation = await checkinBonusCalendar();
      setCalendarState(mutation.state);
      if (mutation.already_checked_in) {
        setCalendarMessage("Сегодня уже отмечено");
      } else if (Number.isInteger(mutation.reward_days) && mutation.reward_days > 0) {
        setCalendarMessage(`Начислено +${formatDays(mutation.reward_days)}`);
      } else {
        setCalendarMessage("День отмечен");
      }
      await refreshCalendarContext();
    } catch {
      setCalendarActionError("Не удалось отметить день. Попробуйте ещё раз.");
    } finally {
      setCalendarBusy(false);
    }
  };

  return (
    <main className="mx-auto flex w-full max-w-[980px] flex-col gap-5">
      <section className="overflow-hidden rounded-panel border border-line bg-surface shadow-soft">
        <div className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between sm:p-6">
          <div className="flex items-start gap-4">
            <span className="grid size-12 shrink-0 place-items-center rounded-[15px] bg-brand-soft text-brand">
              <Gift size={24} strokeWidth={1.9} aria-hidden="true" />
            </span>
            <div>
              <Badge tone="success" dot>Для платной подписки</Badge>
              <h1 className="mt-2 text-2xl font-bold tracking-[-0.02em] text-ink">Награды за активность</h1>
              <p className="mt-1 max-w-2xl text-sm leading-6 text-ink-soft">
                Забирайте еженедельный бонус и отмечайте активность. Начисление всегда подтверждает сервер.
              </p>
            </div>
          </div>
        </div>
      </section>

      <div className="grid items-start gap-4 lg:grid-cols-2">
        {wheelLoading ? (
          <RewardCardSkeleton label="Загружаем рулетку" />
        ) : wheelError || !wheelState ? (
          <RewardLoadError title="Колесо временно недоступно" onRetry={() => void retryWheel()} />
        ) : (
          <BonusWheel state={wheelState} onStateChange={setWheelState} onCommitted={refreshWheelContext} />
        )}

        {calendarLoading ? (
          <RewardCardSkeleton label="Загружаем календарь" />
        ) : calendarError || !calendarState ? (
          <RewardLoadError title="Календарь временно недоступен" onRetry={() => void retryCalendar()} />
        ) : (
          <ActivityCalendar
            state={calendarState}
            busy={calendarBusy}
            message={calendarMessage}
            error={calendarActionError}
            onCheckin={checkin}
          />
        )}
      </div>

      {historyLoading ? (
        <SkeletonRegion label="Загружаем историю наград">
          <SkeletonLine className="h-4 w-36" />
          <SkeletonBlock className="h-44" />
        </SkeletonRegion>
      ) : (
        <RewardHistoryCard history={history} error={historyError} />
      )}
    </main>
  );
}
