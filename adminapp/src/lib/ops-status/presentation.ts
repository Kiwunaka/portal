import type { OpsStatusCode, OpsStatusPresentation } from "./types";

export const STATUS_PRESENTATION: Record<OpsStatusCode, OpsStatusPresentation> = {
  ok: { label: "Норма", tone: "success", explanation: "Свежие обязательные проверки прошли." },
  degraded: { label: "Требует внимания", tone: "warning", explanation: "Источник дал данные, но есть частичное отклонение." },
  failed: { label: "Сбой", tone: "danger", explanation: "Проверка выполнилась и вернула явный отказ." },
  stale: { label: "Устарело", tone: "warning", explanation: "Последнее пригодное измерение старше допустимого окна." },
  unavailable: { label: "Недоступно", tone: "neutral", explanation: "Источник или путь проверки не позволил получить вердикт." },
  missing: { label: "Нет данных", tone: "neutral", explanation: "Пригодного измерения пока нет." },
  BLOCKED_BY_ACCESS: { label: "Доступ заблокирован", tone: "danger", explanation: "Есть подписанное доказательство отсутствия требуемого доступа." }
};

export function statusPresentation(code: OpsStatusCode): OpsStatusPresentation {
  return STATUS_PRESENTATION[code];
}

export function formatSourceAge(sampledAt: string | null, now: Date = new Date()): string {
  if (!sampledAt) {
    return "Нет данных";
  }

  const sampledTime = Date.parse(sampledAt);
  if (Number.isNaN(sampledTime)) {
    return "Нет данных";
  }

  const ageSeconds = Math.max(0, Math.floor((now.getTime() - sampledTime) / 1000));
  if (ageSeconds < 60) {
    return "только что";
  }
  if (ageSeconds < 60 * 60) {
    return `${Math.floor(ageSeconds / 60)} мин назад`;
  }
  if (ageSeconds < 24 * 60 * 60) {
    return `${Math.floor(ageSeconds / (60 * 60))} ч назад`;
  }
  return `${Math.floor(ageSeconds / (24 * 60 * 60))} дн назад`;
}

export type { OpsStatusCode, OpsStatusPresentation, OpsStatusTone } from "./types";
