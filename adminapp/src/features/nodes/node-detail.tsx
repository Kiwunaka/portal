"use client";

import { useId, useRef, type KeyboardEvent, type ReactNode } from "react";
import { Boxes, Cpu, Gauge, Network, Radio, ShieldCheck } from "lucide-react";

import { Badge, Button, Card, SectionTitle } from "@/components/ui";
import { ErrorState, LoadingState } from "@/components/ui/states";
import { OpsTooltip } from "@/components/ui/tooltip";
import type {
  NodeDetailTab,
  NodeObservability,
  RuHistoryRange,
  RuLatest,
  RuNodeStatus,
  RuRunHistory,
  RuUploaderStatus
} from "@/lib/admin-api/nodes";

import { capacityText, NodeSourceSummary, opsStatusFromSource, reasonText, sourceStatusText } from "./node-source-summary";
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
  if (normalized === "not_in_scope") return "Не входит в контур";
  if (normalized === "blocked_by_access") return "Доступ заблокирован";
  if (normalized === "warm") return "Нагрузка приближается к порогу";
  if (normalized === "drain") return "Вывод из новых размещений";
  if (normalized === "hard_reject") return "Запрет новых размещений";
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

function OverviewTab({ data, ruStatus }: { data: NodeObservability; ruStatus: RuNodeStatus | null }) {
  const observer = data.sources.observer;
  const observerDetails = observer.details;
  return (
    <div className="space-y-3">
      <NodeSourceSummary data={data} ruStatus={ruStatus} />
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
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
          <Metric label="Состояние ёмкости" value={capacityText(data.capacity.state)} explanation="Рассчитанная сервером возможность принимать новые размещения." sampledAt={data.sources.runtime.sampled_at} icon={<Gauge size={15} />} />
          <Metric label="Наблюдатель" value={reasonText(data.sources.observer.reason_code)} explanation="Свежесть последнего обработанного пакета наблюдателя." sampledAt={data.sources.observer.sampled_at} threshold={`Порог: ${data.sources.observer.threshold_seconds} сек`} icon={<Radio size={15} />} />
          <Metric label="Последний пакет Observer" value={observerDetails.last_batch_id || "—"} explanation="Идентификатор последнего обработанного пакета Observer; значение безопасно для операторского сопоставления." sampledAt={observer.sampled_at} threshold={`Порог: ${observer.threshold_seconds} сек`} icon={<Radio size={15} />} />
          <Metric label="Сопоставление Observer" value={`Не сопоставлено: ${numberText(observerDetails.unmatched_count, "", 0)}`} explanation="Количество строк последнего пакета, которые не удалось сопоставить с известными сущностями." sampledAt={observer.sampled_at} threshold="Ожидается 0" />
          <Metric label="Разбор Observer" value={`Ошибки разбора: ${numberText(observerDetails.parse_error_count, "", 0)}`} explanation="Количество ошибок разбора в последнем пакете Observer." sampledAt={observer.sampled_at} threshold="Ожидается 0" />
        </div>
      </Card>
    </div>
  );
}

function LoadTab({ data }: { data: NodeObservability }) {
  const brain = data.sources.brain_metrics;
  const details = brain.details;
  const runtime = data.sources.runtime;
  const runtimeDetails = runtime.details;
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
        <SectionTitle title="Панель" description="Задержка и доля ошибок относятся к тому же снимку Brain-origin и не подменяют dataplane." />
        <div className="grid gap-3 sm:grid-cols-2">
          <Metric label="Задержка панели" value={numberText(details.panel_latency_ms, " мс")} explanation="Время ответа панели в последней проверке Brain-origin." sampledAt={brain.sampled_at} />
          <Metric label="Ошибки панели" value={numberText(details.panel_error_rate, "%")} explanation="Доля ошибок панели из последнего пригодного снимка." sampledAt={brain.sampled_at} threshold="Ожидается 0%" />
        </div>
      </Card>
      <Card className="min-h-0">
        <SectionTitle title="Сеть и политика порта" description="Текущие скорости и серверная доля от политики порта." />
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          <Metric label="Приём" value={numberText(details.network_rx_mbps, " Мбит/с")} explanation="Текущая входящая скорость из Brain-origin." sampledAt={brain.sampled_at} icon={<Network size={15} />} />
          <Metric label="Передача" value={numberText(details.network_tx_mbps, " Мбит/с")} explanation="Текущая исходящая скорость из Brain-origin." sampledAt={brain.sampled_at} icon={<Network size={15} />} />
          <Metric label="Суммарно" value={numberText(details.network_total_mbps, " Мбит/с")} explanation="Сумма текущих входящего и исходящего потоков Brain-origin." sampledAt={brain.sampled_at} icon={<Network size={15} />} />
          <Metric label="Приём · 1 мин" value={numberText(runtimeDetails.network_rx_mbps_1m, " Мбит/с")} explanation="Средняя входящая скорость за одну минуту из current-origin." sampledAt={runtime.sampled_at} icon={<Network size={15} />} />
          <Metric label="Передача · 1 мин" value={numberText(runtimeDetails.network_tx_mbps_1m, " Мбит/с")} explanation="Средняя исходящая скорость за одну минуту из current-origin." sampledAt={runtime.sampled_at} icon={<Network size={15} />} />
          <Metric label="Приём · 5 мин" value={numberText(runtimeDetails.network_rx_mbps_5m, " Мбит/с")} explanation="Средняя входящая скорость за пять минут из current-origin." sampledAt={runtime.sampled_at} icon={<Network size={15} />} />
          <Metric label="Передача · 5 мин" value={numberText(runtimeDetails.network_tx_mbps_5m, " Мбит/с")} explanation="Средняя исходящая скорость за пять минут из current-origin." sampledAt={runtime.sampled_at} icon={<Network size={15} />} />
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

function alertTitle(alert: NodeObservability["alerts"][number]): string {
  const stable = `${alert.source}:${alert.fingerprint}`.toLowerCase();
  if (stable.includes("panel_latency")) return "Высокая задержка панели";
  if (stable.includes("panel_error")) return "Ошибки панели выше порога";
  if (stable.includes("cpu")) return "Высокая загрузка процессора";
  if (stable.includes("memory")) return "Высокая загрузка памяти";
  if (stable.includes("disk")) return "Недостаточно свободного места";
  if (stable.includes("capacity")) return "Ограничение ёмкости ноды";
  if (stable.includes("observer")) return "Отклонение Observer";
  return "Операционный сигнал ноды";
}

function alertSource(source: string): string {
  const normalized = String(source || "").toLowerCase();
  const labels: Record<string, string> = {
    node_metrics: "метрики ноды",
    node_health: "проверка здоровья",
    node_capacity: "политика ёмкости",
    observer: "Observer",
    ru_origin: "RU-origin"
  };
  return labels[normalized] || "операционный контур";
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
                <h3 className="text-sm font-semibold">{alertTitle(alert)}</h3>
                <p className="mt-1 text-xs text-[color:var(--atlas-text-soft)]">Источник: {alertSource(alert.source)}</p>
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

function TechnicalTab({ data, ruStatus }: { data: NodeObservability; ruStatus: RuNodeStatus | null }) {
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
          <Definition label="ru_reason" value={ruStatus?.reason_code || "ru_latest_unavailable"} mono />
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
  ruLatest,
  ruStatus,
  latestLoading,
  latestError,
  onLatestRetry,
  history,
  historyLoading,
  historyError,
  onHistoryRetry,
  historyMoreLoading,
  historyMoreError,
  onHistoryLoadMore,
  uploader,
  uploaderLoading,
  uploaderError,
  onUploaderRetry,
  range,
  onRangeChange
}: {
  data: NodeObservability;
  tab: NodeDetailTab;
  onTabChange: (tab: NodeDetailTab) => void;
  ruLatest: RuLatest | null;
  ruStatus: RuNodeStatus | null;
  latestLoading: boolean;
  latestError: string | null;
  onLatestRetry: () => void;
  history: RuRunHistory | null;
  historyLoading: boolean;
  historyError: string | null;
  onHistoryRetry: () => void;
  historyMoreLoading: boolean;
  historyMoreError: string | null;
  onHistoryLoadMore: () => void;
  uploader: RuUploaderStatus | null;
  uploaderLoading: boolean;
  uploaderError: string | null;
  onUploaderRetry: () => void;
  range: RuHistoryRange;
  onRangeChange: (range: RuHistoryRange) => void;
}) {
  const tabRefs = useRef<Array<HTMLButtonElement | null>>([]);

  function moveTab(event: KeyboardEvent<HTMLButtonElement>, index: number) {
    let next = index;
    if (event.key === "ArrowRight") next = (index + 1) % TABS.length;
    else if (event.key === "ArrowLeft") next = (index - 1 + TABS.length) % TABS.length;
    else if (event.key === "Home") next = 0;
    else if (event.key === "End") next = TABS.length - 1;
    else return;
    event.preventDefault();
    onTabChange(TABS[next].id);
    tabRefs.current[next]?.focus();
  }

  const ruOpsStatus = opsStatusFromSource(ruStatus?.status || "unavailable");
  const ruTone = ruOpsStatus === "ok" ? "success" : ruOpsStatus === "failed" || ruOpsStatus === "BLOCKED_BY_ACCESS" ? "danger" : ruOpsStatus === "degraded" || ruOpsStatus === "stale" ? "warning" : "neutral";

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-xl font-semibold tracking-tight">Нода {data.node.code.toUpperCase()}</h2>
            <Badge tone={data.lifecycle.enabled ? data.lifecycle.is_draining ? "warning" : "success" : "neutral"}>{lifecycleText(data)}</Badge>
            <Badge tone={ruTone}>RU: {sourceStatusText(ruStatus?.status || "unavailable")}</Badge>
          </div>
          <p className="mt-1 text-xs text-[color:var(--atlas-text-soft)]">{data.node.name || "Без названия"} · снимок {new Date(data.generated_at).toLocaleString("ru-RU")}</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-[color:var(--atlas-text-soft)]"><ShieldCheck size={15} /> Только чтение</div>
      </div>

      <div role="tablist" aria-label="Разделы карточки ноды" className="ops-scrollbar flex gap-1 overflow-x-auto border-b border-[color:var(--atlas-border)] pb-2">
        {TABS.map((item, index) => (
          <button
            key={item.id}
            ref={(element) => { tabRefs.current[index] = element; }}
            id={`node-tab-${item.id}`}
            type="button"
            role="tab"
            aria-selected={tab === item.id}
            aria-controls={`node-panel-${item.id}`}
            tabIndex={tab === item.id ? 0 : -1}
            onClick={() => onTabChange(item.id)}
            onKeyDown={(event) => moveTab(event, index)}
            className={`shrink-0 rounded-[var(--pokrov-radius-control)] border px-3 text-xs font-semibold ${tab === item.id ? "border-[color:var(--atlas-border-strong)] bg-[color:var(--pokrov-nav-active-bg)] text-[color:var(--atlas-text)]" : "border-transparent text-[color:var(--atlas-text-soft)] hover:bg-[color:var(--pokrov-table-row-hover-bg)]"}`}
          >
            {item.label}
          </button>
        ))}
      </div>

      <div id={`node-panel-${tab}`} role="tabpanel" aria-labelledby={`node-tab-${tab}`}>
        {tab === "overview" ? <OverviewTab data={data} ruStatus={ruStatus} /> : null}
        {tab === "load" ? <LoadTab data={data} /> : null}
        {tab === "clients" ? <ClientsTab data={data} /> : null}
        {tab === "transport" ? <TransportTab data={data} /> : null}
        {tab === "alerts" ? <AlertsTab data={data} /> : null}
        {tab === "technical" ? <TechnicalTab data={data} ruStatus={ruStatus} /> : null}
        {tab === "ru" ? (
          <div className="space-y-3">
            {ruLatest || history ? (
              <RuHistory
                latest={ruLatest}
                nodeStatus={ruStatus}
                history={history}
                range={range}
                onRangeChange={onRangeChange}
                loadingMore={historyMoreLoading}
                loadMoreError={historyMoreError}
                onLoadMore={onHistoryLoadMore}
              />
            ) : null}
            {latestLoading && !ruLatest ? <LoadingState title="Загружаем текущий RU-origin" description="Текущий статус и карточки попыток запрашиваются отдельно от сохранённой истории." className="min-h-24" /> : null}
            {latestError ? <ErrorState title="Текущий RU-origin недоступен" description={latestError} action={<Button tone="secondary" onClick={onLatestRetry}>Повторить текущий RU-origin</Button>} className="min-h-24" /> : null}
            {historyLoading && !history ? <LoadingState title="Загружаем историю RU-origin" description="История запрашивается только для выбранной ноды и активной вкладки." /> : null}
            {historyError ? <ErrorState title="История RU-origin недоступна" description={historyError} action={<Button tone="secondary" onClick={onHistoryRetry}>Повторить историю</Button>} /> : null}
            {uploader ? <UploaderStatus data={uploader} /> : null}
            {uploaderLoading && !uploader ? <LoadingState title="Проверяем доставку результатов" description="Ждём отдельный служебный сигнал загрузчика." className="min-h-24" /> : null}
            {uploaderError ? <ErrorState title="Статус загрузчика недоступен" description={uploaderError} action={<Button tone="secondary" onClick={onUploaderRetry}>Повторить статус загрузчика</Button>} className="min-h-24" /> : null}
          </div>
        ) : null}
      </div>
    </div>
  );
}
