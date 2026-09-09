"use client";

import { Badge } from "@/components/ui";
import type { SupportConnectivity } from "@/lib/admin-api/support";

const PROTOCOLS: Record<string, string> = {
  vless: "VLESS", awg2: "AWG2", awg31: "AWG3.1", hysteria2: "Hysteria2", unknown: "Неизвестен",
};
const PROOF_STAGES: Record<string, string> = {
  unknown: "Нет наблюдения", not_running: "Туннель не работает", tunnel: "Туннель запущен",
  dns: "DNS подтверждён", egress: "Туннель, DNS и выход подтверждены", degraded: "Защита с предупреждением",
};
const NEXT_ACTIONS: Record<string, string> = {
  refresh_profile: "Попросите обновить профиль и повторить подключение. Сверьте свежую попытку перед изменением назначения.",
  refresh_proof: "Попросите обновить проверку защиты в приложении.",
  request_diagnostics: "Попросите выполнить подключение и прислать диагностический пакет из приложения.",
};

export function ConnectivityReport({ data }: { data: SupportConnectivity | null }) {
  if (!data) return <p className="text-xs text-[color:var(--atlas-text-muted)]">Данных о применённом профиле нет. Нужен свежий отчёт приложения.</p>;
  const mismatch = data.alignment === "mismatch";
  const profiles = [
    ["Назначен сервером", data.assignment], ["Скачан", data.fetched],
    ["Подготовлен", data.staged], ["Работает по отчёту", data.effective],
  ] as const;
  return <section aria-label="Назначенный и работающий профиль" className="space-y-3 text-xs">
    <div className="flex flex-wrap items-center gap-2">
      <strong>Назначен {PROTOCOLS[data.assignment.protocol] || "неизвестный протокол"} · {data.proofStage === "not_running" ? "туннель не работает" : `работает ${PROTOCOLS[data.effective.protocol] || "неизвестный протокол"}`}</strong>
      <Badge tone={mismatch ? "warning" : "neutral"}>{mismatch ? "Не совпадает с назначением" : data.alignment === "match" ? "Revision совпадает" : "Сравнение недоступно"}</Badge>
    </div>
    <dl className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">{profiles.map(([label, profile]) => <div key={label} className="min-w-0 rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] p-2">
      <dt className="text-[color:var(--atlas-text-muted)]">{label}</dt>
      <dd className="mt-1 font-semibold">{PROTOCOLS[profile.protocol] || "Неизвестен"}</dd>
      <dd className="mt-1 break-all font-mono text-[11px]">{profile.revision || "Revision неизвестна"}</dd>
    </div>)}</dl>
    <p><strong>Доказательство клиента:</strong> {PROOF_STAGES[data.proofStage] || "Нет наблюдения"}. {data.proofAgeSeconds === null ? "Время подтверждения неизвестно." : `При загрузке данных переход к подтверждённой защите наблюдался ${data.proofAgeSeconds} с назад.`}</p>
    <p className="text-[color:var(--atlas-text-muted)]">Назначение рассчитано сервером при получении отчёта{data.receivedAt ? ` (${new Date(data.receivedAt).toLocaleString("ru-RU")})` : ""}. Состояние туннеля сообщило приложение; это не независимое серверное подтверждение трафика.</p>
    <p><strong>Следующий шаг:</strong> {NEXT_ACTIONS[data.nextAction] || NEXT_ACTIONS.request_diagnostics}</p>
  </section>;
}
