"use client";

import { useId, type ReactNode } from "react";
import { ArrowLeft, Boxes, Cpu, Gauge, Network, Radio, ShieldCheck } from "lucide-react";

import { Badge, Button, Card, SectionTitle } from "@/components/ui";
import { ErrorState, LoadingState } from "@/components/ui/states";
import { OpsTooltip } from "@/components/ui/tooltip";
import type {
  NodeDetailTab,
  NodeObservability,
  RuHistoryRange,
  RuLatest,
  RuRunHistory,
  RuUploaderStatus
} from "@/lib/admin-api/nodes";

import { NodeSourceSummary, opsStatusFromSource, reasonText } from "./node-source-summary";
import { RuHistory } from "./ru-history";
import { UploaderStatus } from "./uploader-status";

const TABS: Array<{ id: NodeDetailTab; label: string }> = [
  { id: "overview", label: "Обзор" },
  { id: "ru", label: "Проверки из РФ" },
  { id: "load", label: "Нагрузка" },
  { id: "clients", label: "Клиенты" },
  { id: "transport", label: "Транспорт" },
  { id: "alerts", label: "Алерты" },
  { id: "technical", label: "Технические детали" }
];

function finiteNumber(value: number | null | undefined): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function numberText(value: number | null | undefined, suffix = "", digits = 1): string {
  const number = finiteNumber(value);
  if (number === null) return "—";
  return `${number.toLocaleString("ru-RU", { maximumFractionDigits: digits })}${suffix}`;
}

function ratioText(used: number | null | undefined, total: number | null | undefined, unit: string): string {
  const usedValue = finiteNumber(used);
  const totalValue = finiteNumber(total);
  if (usedValue === null || totalValue === null || totalValue <= 0) return "—";
  return `${numberText(usedValue, ` ${unit}`)} / ${numberText(totalValue, ` ${unit}`)}`;
}

function yesNoUnknown(value: boolean | null | undefined): string {
  if (value === true) return "Да";
  if (value === false) return "Нет";
  return "—";
}

function lifecycleText(data: NodeObservability): string {
  if (!data.lifecycle.enabled) return "Отключена";
  if (data.lifecycle.is_draining || !data.lifecycle.accepting_new_clients) return "Выводится из контура";
  return "Включена";
}

function healthText(value: string | null): string {
  const normalized = String(value || "").toLowerCase();
  if (["ok", "healthy", "pass"].includes(normalized)) return "Норма";
  if (["failed", "fail", "critical"].includes(normalized)) return "Сбой";
  if (["degraded", "warning"].includes(normalized)) return "Требует внимания";
  if (normalized === "stale") return "Устарело";
  if (normalized === "unavailable") return "Недоступно";
  return "Нет данных";
}

function Metric({
  label,
  value,
  explanation,
  sampledAt,
  threshold = null,
  icon
}: {
  label: string;
  value: string;
  explanation: string;
  sampledAt: string | null;
  threshold?: string | null;
  icon?: ReactNode;
}) {
  const id = useId();
  return (
    <div className="rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2 text-xs font-semibold text-[color:var(--atlas-text-soft)]">{icon}{label}</div>
        <OpsTooltip id={`${id}-metric`} content={explanation} source={label} sampledAt={sampledAt} threshold={threshold} />
      </div>
      <div className="mt-3 text-lg font-semibold tabular-nums text-[color:var(--atlas-text)]">{value}</div>
    </div>
  );
}

function DefinitionGrid({ children }: { children: ReactNode }) {
  return <dl className="grid gap-x-5 gap-y-3 text-xs sm:grid-cols-2 xl:grid-cols-3">{children}</dl>;
}

function Definition({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <dt className="text-[color:var(--atlas-text-muted)]">{label}</dt>
      <dd className={`mt-1 font-semibold text-[color:var(--atlas-text)] ${mono ? "font-mono" : ""}`}>{value}</dd>
    </div>
  );
}

function OverviewTab({ data }: { data: NodeObservability }) {
  return (
    <div className="space-y-3">
      <NodeSourceSummary data={data} />
      <Card className="min-h-0">
        <SectionTitle title="Паспорт ноды" description="Публичные операционные признаки и текущее состояние ноды." />
        <DefinitionGrid>
          <Definition label="Название" value={data.node.name || "—"} />
          <Definition label="Состояние" value={lifecycleText(data)} />
          <Definition label="Вес" value={numberText(data.node.weight, "", 0)} />
          <Definition label="Хостер" value={data.node.hoster_family || "—"} />
          <Definition label="Автономная система (ASN)" value={data.node.hoster_asn || "—"} />
          <Definition label="Подсеть" value={data.node.subnet || "—"} />
        </DefinitionGrid>
      </Card>
      <Card className="min-h-0">
        <SectionTitle title="Текущий контур и наблюдатель" description="Наблюдатель показан отдельно: зелёная панель не скрывает устаревший пакет данных." />
        <div className="grid gap-3 sm:grid-cols-2">
          <Metric label="Состояние ёмкости" value={healthText(data.capacity.state)} explanation="Рассчитанная сервером возможность принимать новые размещения." sampledAt={data.sources.runtime.sampled_at} icon={<Gauge size={15} />} />
          <Metric label="Наблюдатель" value={reasonText(data.sources.observer.reason_code)} explanation="Свежесть последнего обработанного пакета наблюдателя." sampledAt={data.sources.observer.sampled_at} threshold={`Порог: ${data.sources.observer.threshold_seconds} сек`} icon={<Radio size={15} />} />
        </div>
      </Card>
    </div>
  );
}

function LoadTab({ data }: { data: NodeObservability }) {
  const brain = data.sources.brain_metrics;
  const details = brain.details;
  return (
    <div className="space-y-3">
      <Card className="min-h-0">
        <SectionTitle title="Ресурсы" description="Отсутствующий общий объём не превращается в 0%: в этом случае показан прочерк." />
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          <Metric label="Процессор (CPU)" value={numberText(details.cpu_percent, "%")} explanation="Последняя загрузка процессора из Brain-origin." sampledAt={brain.sampled_at} icon={<Cpu size={15} />} />
          <Metric label="Оперативная память" value={ratioText(details.memory_used_mb, details.memory_total_mb, "МиБ")} explanation="Использовано и всего по одному снимку Brain-origin." sampledAt={brain.sampled_at} />
          <Metric label="Диск" value={ratioText(details.disk_used_gb, details.disk_total_gb, "ГиБ")} explanation="Использовано и всего; без общего объёма процент не вычисляется." sampledAt={brain.sampled_at} />
        </div>
      </Card>
      <Card className="min-h-0">
        <SectionTitle title="Сеть и политика порта" description="Текущие скорости и серверная доля от политики порта." />
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          <Metric label="Приём" value={numberText(details.network_rx_mbps, " Мбит/с")} explanation="Текущая входящая скорость из Brain-origin." sampledAt={brain.sampled_at} icon={<Network size={15} />} />
          <Metric label="Передача" value={numberText(details.network_tx_mbps, " Мбит/с")} explanation="Текущая исходящая скорость из Brain-origin." sampledAt={brain.sampled_at} icon={<Network size={15} />} />
          <Metric label="Загрузка порта" value={data.capacity.tx_ratio === null ? "—" : numberText(data.capacity.tx_ratio * 100, "%")} explanation="Доля исходящей скорости от индивидуальной либо серверной политики порта." sampledAt={data.sources.runtime.sampled_at} icon={<Gauge size={15} />} />
        </div>
      </Card>
    </div>
  );
}

function ClientsTab({ data }: { data: NodeObservability }) {
  return (
    <Card className="min-h-0">
      <SectionTitle title="Клиентская нагрузка" description="Подготовленные клиенты и оценка онлайн — разные величины из разных срезов." />
      <div className="grid gap-3 sm:grid-cols-3">
        <Metric label="Привязанные пользователи" value={numberText(data.lifecycle.mapped_users, "", 0)} explanation="Уникальные локальные привязки пользователей к ноде." sampledAt={data.generated_at} icon={<Boxes size={15} />} />
        <Metric label="Подготовленные клиенты" value={numberText(data.capacity.provisioned_clients_count, "", 0)} explanation="Клиенты, подготовленные на ноде; это не онлайн." sampledAt={data.sources.runtime.sampled_at} icon={<Boxes size={15} />} />
        <Metric label="Оценка онлайн" value={numberText(data.capacity.online_connections_hint, "", 0)} explanation="Оперативная оценка соединений; не уникальные пользователи." sampledAt={data.sources.runtime.sampled_at} icon={<Radio size={15} />} />
      </div>
    </Card>
  );
}

function TransportTab({ data }: { data: NodeObservability }) {
  return (
    <div className="space-y-3">
      <Card className="min-h-0">
        <SectionTitle title="IP и контур передачи данных" description="IPv4, IPv6 и контур передачи данных не объединяются в один зелёный сигнал." />
        <DefinitionGrid>
          <Definition label="IPv4" value={healthText(data.network.ipv4_health)} />
          <Definition label="IPv6" value={healthText(data.network.ipv6_health)} />
          <Definition label="Контур передачи отвечает" value={yesNoUnknown(data.network.dataplane_ok)} />
          <Definition label="Задержка контура (RTT)" value={numberText(data.network.dataplane_rtt_ms, " мс")} />
          <Definition label="Потеря пакетов" value={numberText(data.network.packet_loss_percent, "%")} />
          <Definition label="Повторные TCP-передачи" value={numberText(data.network.tcp_retrans_percent, "%")} />
        </DefinitionGrid>
      </Card>
      <Card className="min-h-0">
        <SectionTitle title="Транспортные профили" description="Первый слой показывает только наличие и состояние; машинные имена скрыты ниже." />
        {data.transports.length ? (
          <div className="divide-y divide-[color:var(--atlas-border)] rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)]">
            {data.transports.map((transport, index) => (
              <div key={`${transport.name}-${index}`} className="flex flex-wrap items-center justify-between gap-2 px-3 py-3 text-xs">
                <span className="font-semibold">Профиль {index + 1}</span>
                <Badge tone={transport.enabled ? "success" : "neutral"}>{transport.enabled ? "Включён" : "Отключён"}</Badge>
              </div>
            ))}
          </div>
        ) : <p className="text-xs text-[color:var(--atlas-text-soft)]">Транспортные профили не получены.</p>}
        <details className="mt-3 text-xs text-[color:var(--atlas-text-soft)]">
          <summary className="cursor-pointer select-none font-semibold text-[color:var(--atlas-text)]">Технические имена транспортов</summary>
          <ul className="mt-2 space-y-1 font-mono text-[11px]">
            {data.transports.map((transport) => <li key={transport.name}>{transport.name} · {transport.kind} · port {transport.port ?? "—"}</li>)}
          </ul>
        </details>
      </Card>
    </div>
  );
}

function AlertsTab({ data }: { data: NodeObservability }) {
  return (
    <Card className="min-h-0">
      <SectionTitle title="Активные алерты" description="Причина, источник и время остаются привязаны к конкретному алерту." />
      {data.alerts.length ? (
        <div className="divide-y divide-[color:var(--atlas-border)] rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)]">
          {data.alerts.map((alert) => (
            <article key={alert.id} className="grid gap-2 px-3 py-3 sm:grid-cols-[1fr_auto] sm:items-center">
              <div>
                <h3 className="text-sm font-semibold">{alert.title}</h3>
                <p className="mt-1 text-xs text-[color:var(--atlas-text-soft)]">Последний сигнал: {alert.last_seen_at ? new Date(alert.last_seen_at).toLocaleString("ru-RU") : "Нет данных"}</p>
              </div>
              <Badge tone={alert.severity === "critical" ? "danger" : "warning"}>{alert.severity === "critical" ? "Критично" : "Предупреждение"}</Badge>
            </article>
          ))}
        </div>
      ) : <p className="text-xs text-[color:var(--atlas-text-soft)]">Активных алертов для этой ноды нет.</p>}
    </Card>
  );
}

function TechnicalTab({ data }: { data: NodeObservability }) {
  return (
    <Card className="min-h-0">
      <SectionTitle title="Технические детали" description="Машинные коды скрыты по умолчанию и нужны только для точного расследования." />
      <details className="rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 py-3 text-xs">
        <summary className="cursor-pointer select-none font-semibold">Показать технические коды ноды</summary>
        <dl className="mt-3 grid gap-2 font-mono text-[11px] text-[color:var(--atlas-text-soft)]">
          <Definition label="node_code" value={data.node.code} mono />
          <Definition label="brain_reason" value={data.sources.brain_metrics.reason_code} mono />
          <Definition label="runtime_reason" value={data.sources.runtime.reason_code} mono />
          <Definition label="observer_reason" value={data.sources.observer.reason_code} mono />
          <Definition label="ru_reason" value={data.sources.ru_origin.reason_code} mono />
          <Definition label="probe_stage" value={data.network.last_probe_stage || "—"} mono />
          <Definition label="probe_error_kind" value={data.network.last_probe_error_kind || "—"} mono />
          <Definition label="probe_classification" value={data.network.probe_classification || "—"} mono />
        </dl>
      </details>
    </Card>
  );
}

export function NodeDetail({
  data,
  tab,
  onTabChange,
  onBack,
  ruLatest,
  history,
  historyLoading,
  historyError,
  uploader,
  uploaderLoading,
  uploaderError,
  range,
  onRangeChange
}: {
  data: NodeObservability;
  tab: NodeDetailTab;
  onTabChange: (tab: NodeDetailTab) => void;
  onBack: () => void;
  ruLatest: RuLatest | null;
  history: RuRunHistory | null;
  historyLoading: boolean;
  historyError: string | null;
  uploader: RuUploaderStatus | null;
  uploaderLoading: boolean;
  uploaderError: string | null;
  range: RuHistoryRange;
  onRangeChange: (range: RuHistoryRange) => void;
}) {
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <Button tone="ghost" className="mb-2 lg:hidden" onClick={onBack}><ArrowLeft size={15} /> Назад к нодам</Button>
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-xl font-semibold tracking-tight">Нода {data.node.code.toUpperCase()}</h2>
            <Badge tone={data.lifecycle.enabled ? data.lifecycle.is_draining ? "warning" : "success" : "neutral"}>{lifecycleText(data)}</Badge>
            <Badge tone={opsStatusFromSource(data.sources.ru_origin.status) === "ok" ? "success" : opsStatusFromSource(data.sources.ru_origin.status) === "failed" ? "danger" : "warning"}>RU: {healthText(data.sources.ru_origin.status)}</Badge>
          </div>
          <p className="mt-1 text-xs text-[color:var(--atlas-text-soft)]">{data.node.name || "Без названия"} · снимок {new Date(data.generated_at).toLocaleString("ru-RU")}</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-[color:var(--atlas-text-soft)]"><ShieldCheck size={15} /> Только чтение</div>
      </div>

      <div role="tablist" aria-label="Разделы карточки ноды" className="ops-scrollbar flex gap-1 overflow-x-auto border-b border-[color:var(--atlas-border)] pb-2">
        {TABS.map((item) => (
          <button
            key={item.id}
            type="button"
            role="tab"
            aria-selected={tab === item.id}
            onClick={() => onTabChange(item.id)}
            className={`shrink-0 rounded-[var(--pokrov-radius-control)] border px-3 text-xs font-semibold ${tab === item.id ? "border-[color:var(--atlas-border-strong)] bg-[color:var(--pokrov-nav-active-bg)] text-[color:var(--atlas-text)]" : "border-transparent text-[color:var(--atlas-text-soft)] hover:bg-[color:var(--pokrov-table-row-hover-bg)]"}`}
          >
            {item.label}
          </button>
        ))}
      </div>

      <div role="tabpanel">
        {tab === "overview" ? <OverviewTab data={data} /> : null}
        {tab === "load" ? <LoadTab data={data} /> : null}
        {tab === "clients" ? <ClientsTab data={data} /> : null}
        {tab === "transport" ? <TransportTab data={data} /> : null}
        {tab === "alerts" ? <AlertsTab data={data} /> : null}
        {tab === "technical" ? <TechnicalTab data={data} /> : null}
        {tab === "ru" ? (
          <div className="space-y-3">
            {ruLatest && history ? <RuHistory latest={ruLatest} nodeStatus={data.sources.ru_origin} history={history} range={range} onRangeChange={onRangeChange} /> : null}
            {historyLoading && !history ? <LoadingState title="Загружаем историю RU-origin" description="История запрашивается только для выбранной ноды и активной вкладки." /> : null}
            {historyError ? <ErrorState title="История RU-origin недоступна" description={historyError} /> : null}
            {!ruLatest && !historyLoading && !historyError ? <ErrorState title="RU-origin недоступен" description="Сводный источник не ответил; Brain и текущий контур остаются отдельными." /> : null}
            {uploader ? <UploaderStatus data={uploader} /> : null}
            {uploaderLoading && !uploader ? <LoadingState title="Проверяем доставку результатов" description="Ждём отдельный служебный сигнал загрузчика." className="min-h-24" /> : null}
            {uploaderError ? <ErrorState title="Статус загрузчика недоступен" description={uploaderError} className="min-h-24" /> : null}
          </div>
        ) : null}
      </div>
    </div>
  );
}
