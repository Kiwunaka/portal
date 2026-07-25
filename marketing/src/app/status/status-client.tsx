"use client";

import { useEffect, useState } from "react";

import { Card } from "../../components/ui/card";
import { CANONICAL_API_BASE_URL } from "../../lib/pokrov";

type Incident = {
  id: string;
  key: string;
  title: string;
  summary: string;
  severity: string;
  status: string;
  startedAt?: string | null;
  endedAt?: string | null;
  compensationDays: number;
  compensationState: string;
};

type ServiceStatus = {
  status: "operational" | "degraded";
  checkedAt?: string | null;
  current: Incident[];
  recent: Incident[];
};

function formatTime(value?: string | null): string {
  if (!value) return "время уточняется";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "время уточняется";
  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(parsed);
}

export function StatusClient() {
  const [data, setData] = useState<ServiceStatus | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), 7000);
    fetch(`${CANONICAL_API_BASE_URL}/api/public/service-status`, {
      signal: controller.signal,
      headers: { Accept: "application/json" },
    })
      .then(async (response) => {
        if (!response.ok) throw new Error("status unavailable");
        return (await response.json()) as ServiceStatus;
      })
      .then((payload) => {
        setData(payload);
        setError("");
      })
      .catch(() => setError("Не получилось получить свежий серверный статус."))
      .finally(() => window.clearTimeout(timer));
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, []);

  if (error) {
    return (
      <Card className="border-line bg-canvas-alt">
        <h2 className="font-display text-xl font-bold text-ink">Статус неизвестен</h2>
        <p className="mt-2 text-sm leading-relaxed text-ink-soft">
          {error} Это не считается зелёным состоянием. Проверьте центр защиты в приложении или напишите в поддержку.
        </p>
      </Card>
    );
  }

  if (!data) {
    return <Card className="text-sm text-ink-soft">Получаем подтверждённые инциденты…</Card>;
  }

  return (
    <div className="flex flex-col gap-4">
      <Card className={data.status === "operational" ? "border-line" : "border-brand bg-canvas-alt"}>
        <p className="text-xs font-semibold tracking-[0.08em] text-brand uppercase">
          {data.status === "operational" ? "Подтверждённых активных инцидентов нет" : "Есть активный инцидент"}
        </p>
        <h2 className="mt-2 font-display text-2xl font-bold text-ink">
          {data.status === "operational" ? "Серверный статус: работает" : "Серверный статус: нестабильно"}
        </h2>
        <p className="mt-2 text-sm leading-relaxed text-ink-soft">
          Проверено {formatTime(data.checkedAt)}. Эта страница не видит туннель, DNS и маршруты конкретного устройства.
        </p>
      </Card>

      {data.current.map((incident) => (
        <Card key={incident.id} className="flex flex-col gap-2 border-brand bg-canvas-alt">
          <p className="text-xs font-semibold tracking-[0.08em] text-brand uppercase">Активный · {incident.severity}</p>
          <h2 className="font-display text-xl font-bold text-ink">{incident.title}</h2>
          <p className="text-sm leading-relaxed text-ink-soft">{incident.summary}</p>
          <p className="text-xs text-ink-soft">Начало: {formatTime(incident.startedAt)}</p>
        </Card>
      ))}

      <div>
        <h2 className="font-display text-xl font-bold text-ink">Недавние подтверждённые инциденты</h2>
        {data.recent.length === 0 ? (
          <p className="mt-2 text-sm text-ink-soft">В журнале пока нет закрытых инцидентов.</p>
        ) : (
          <div className="mt-3 grid gap-3">
            {data.recent.map((incident) => (
              <Card key={incident.id} className="flex flex-col gap-2">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h3 className="font-display text-lg font-bold text-ink">{incident.title}</h3>
                  <span className="text-xs font-semibold text-ink-soft">Закрыт {formatTime(incident.endedAt)}</span>
                </div>
                <p className="text-sm leading-relaxed text-ink-soft">{incident.summary}</p>
                <p className="text-xs font-semibold text-ink">
                  {incident.compensationDays > 0
                    ? incident.compensationState === "completed"
                      ? `Компенсация: ${incident.compensationDays} дн., начислена затронутым аккаунтам`
                      : `Компенсация: ${incident.compensationDays} дн., обработка`
                    : "Компенсация не назначена"}
                </p>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
