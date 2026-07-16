import { Badge, Card } from "@/components/ui";
import type { RuUploaderStatus } from "@/lib/admin-api/nodes";
import { formatSourceAge } from "@/lib/ops-status/presentation";

function formatBytes(value: number | null): string {
  if (value === null || !Number.isFinite(value)) return "—";
  const gib = value / 1024 ** 3;
  return `${gib.toLocaleString("ru-RU", { maximumFractionDigits: 1 })} ГиБ`;
}

export function UploaderStatus({ data }: { data: RuUploaderStatus }) {
  if (data.status === "stale") {
    return (
      <Card className="min-h-0" >
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h3 className="text-sm font-semibold">Доставка результатов</h3>
          <Badge tone="warning">Связь устарела</Badge>
        </div>
        <p className="mt-3 text-sm font-semibold text-[color:var(--command-status-warning-text)]">Нет свежей связи с загрузчиком</p>
        <p className="mt-1 text-xs leading-5 text-[color:var(--atlas-text-soft)]">
          Последний служебный сигнал получен {data.sampled_at ? formatSourceAge(data.sampled_at) : "в неизвестное время"}. До нового сигнала локальная причина неизвестна.
        </p>
      </Card>
    );
  }

  if (data.status === "missing" || !data.heartbeat) {
    return (
      <Card className="min-h-0">
        <h3 className="text-sm font-semibold">Доставка результатов</h3>
        <p className="mt-2 text-xs leading-5 text-[color:var(--atlas-text-soft)]">Связь с загрузчиком ещё не подтверждена. Это отдельное состояние и оно не объясняет отсутствие RU-запуска.</p>
      </Card>
    );
  }

  const heartbeat = data.heartbeat;
  const hasQueue = heartbeat.pending_count > 0 || heartbeat.blocked_count > 0 || heartbeat.quarantine_count > 0;
  return (
    <Card className="min-h-0">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold">Доставка результатов</h3>
        <Badge tone={hasQueue ? "warning" : "success"}>{hasQueue ? "Есть очередь" : "Доставка в норме"}</Badge>
      </div>
      <div className="mt-3 grid gap-2 text-xs sm:grid-cols-3">
        <div className="rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 py-2">
          <span className="font-semibold">Очередь отправки: {heartbeat.pending_count}</span>
        </div>
        <div className="rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 py-2">
          <span className="font-semibold">Заблокировано: {heartbeat.blocked_count}</span>
        </div>
        <div className="rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 py-2">
          <span className="font-semibold">Карантин: {heartbeat.quarantine_count}</span>
        </div>
      </div>
      <p className="mt-3 text-xs text-[color:var(--atlas-text-soft)]">
        Служебный сигнал получен {data.sampled_at ? formatSourceAge(data.sampled_at) : "без времени"}; запись в архив {heartbeat.archive_write_ok ? "подтверждена" : "не подтверждена"}.
      </p>
      <details className="mt-2 text-xs text-[color:var(--atlas-text-soft)]">
        <summary className="cursor-pointer select-none font-semibold text-[color:var(--atlas-text)]">Технические детали загрузчика</summary>
        <dl className="mt-2 grid gap-1 font-mono text-[11px]">
          <div><dt className="inline text-[color:var(--atlas-text-muted)]">probe_host: </dt><dd className="inline">{heartbeat.probe_host_id}</dd></div>
          <div><dt className="inline text-[color:var(--atlas-text-muted)]">service: </dt><dd className="inline">{heartbeat.service_version}</dd></div>
          <div><dt className="inline text-[color:var(--atlas-text-muted)]">disk_free: </dt><dd className="inline">{formatBytes(heartbeat.disk_free_bytes)}</dd></div>
          <div><dt className="inline text-[color:var(--atlas-text-muted)]">disk_state: </dt><dd className="inline">{heartbeat.disk_state}</dd></div>
          <div><dt className="inline text-[color:var(--atlas-text-muted)]">last_error: </dt><dd className="inline">{heartbeat.last_error_code || "—"}</dd></div>
        </dl>
      </details>
    </Card>
  );
}
