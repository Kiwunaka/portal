"use client";

import {
  AdminConfirmDialog,
  AdminBadge,
  AdminEmptyState,
  AdminInlineNote,
  AdminKpiCard,
  AdminPanelHeader,
  AdminSurfaceHeader,
  adminButtonClass,
  adminFieldClass,
  adminInsetPanelClass,
  adminPanelClass,
  adminTextAreaClass,
} from "@/components/admin/admin-shell";
import {
  adminNetworkRolloutConfig,
  adminNetworkRolloutConfigUpdate,
  type AdminNetworkRolloutConfig,
  type AdminNetworkRolloutOverride,
} from "@/lib/api";
import { AlertTriangle, Loader2, RefreshCw, Save } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

function stringifyConfig(config: AdminNetworkRolloutConfig | null): string {
  return config ? JSON.stringify(config, null, 2) : "";
}

function countList(value?: unknown[] | null): number {
  return Array.isArray(value) ? value.filter((item) => String(item ?? "").trim()).length : 0;
}

function joinList(value?: unknown[] | null): string {
  if (!Array.isArray(value) || value.length === 0) return "none";
  return value.map((item) => String(item)).join(" · ");
}

function feedLabel(value: unknown): string {
  if (value == null) return "not configured";
  if (typeof value === "string") return value || "not configured";
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  if (typeof value === "object") {
    const data = value as Record<string, unknown>;
    const preferred = data.version ?? data.name ?? data.feed ?? data.url ?? data.id;
    return preferred == null ? JSON.stringify(data) : String(preferred);
  }
  return String(value);
}

function profileDisplay(value?: string | null): string {
  const raw = String(value || "").trim();
  if (!raw) return "По умолчанию";
  if (raw === "legacy_reality_fallback") return "Стабильный совместимый путь";
  if (raw === "grpc_443_primary") return "Основной app-first путь";
  if (raw === "reserve_xhttp_cdn") return "Резервный контур";
  if (raw === "operator_lab") return "Операторский тест";
  return "Настроенный путь";
}

function overrideEntries(value?: Record<string, AdminNetworkRolloutOverride> | null): Array<[string, AdminNetworkRolloutOverride]> {
  return Object.entries(value || {});
}

function overrideSize(value?: Record<string, AdminNetworkRolloutOverride> | null): number {
  return overrideEntries(value).length;
}

function parseDraft(text: string): { value: AdminNetworkRolloutConfig | null; error: string } {
  try {
    return { value: JSON.parse(text) as AdminNetworkRolloutConfig, error: "" };
  } catch (err) {
    return { value: null, error: String((err as { message?: string })?.message || err) };
  }
}

function linesToList(value: string): string[] {
  return value
    .split(/\r?\n|,/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function listToLines(value?: unknown[] | null): string {
  return Array.isArray(value) ? value.map((item) => String(item)).join("\n") : "";
}

function OverrideCard({ title, rows }: { title: string; rows: Array<[string, AdminNetworkRolloutOverride]> }) {
  return (
    <article className={adminPanelClass("neutral")}>
      <h3 className="sr-only">Targeting selectors</h3>
      <AdminPanelHeader eyebrow="Targeting selectors" title={title} description="Операторский preview изменений из сохраненного JSON." />
      {rows.length ? (
        <div className="space-y-2">
          {rows.map(([key, value]) => (
            <div key={key} className={adminInsetPanelClass}>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h3 className="text-sm font-semibold text-slate-100">{key}</h3>
                <AdminBadge tone="accent">{profileDisplay(value.transport_profile)}</AdminBadge>
              </div>
              <dl className="mt-3 grid gap-2 text-xs leading-5 text-slate-400 sm:grid-cols-2">
                <div>
                  <dt className="text-slate-500">routing</dt>
                  <dd className="font-medium text-slate-200">{value.routing_mode_default || "default"}</dd>
                </div>
                <div>
                  <dt className="text-slate-500">DNS</dt>
                  <dd className="font-medium text-slate-200">{value.dns_policy || "default"}</dd>
                </div>
                <div>
                  <dt className="text-slate-500">install IDs</dt>
                  <dd className="font-medium text-slate-200">{joinList(value.install_ids)}</dd>
                </div>
                <div>
                  <dt className="text-slate-500">Telegram IDs</dt>
                  <dd className="font-medium text-slate-200">{joinList(value.tg_ids || value.linked_tg_ids)}</dd>
                </div>
                <div className="sm:col-span-2">
                  <dt className="sr-only">platforms</dt>
                  <dd className="font-medium text-slate-200">platforms: {joinList(value.platforms)}</dd>
                </div>
              </dl>
            </div>
          ))}
        </div>
      ) : (
        <AdminEmptyState title="No overrides" description="This selector group currently inherits the global defaults." />
      )}
    </article>
  );
}

export default function AdminNetworkPage() {
  const [config, setConfig] = useState<AdminNetworkRolloutConfig | null>(null);
  const [jsonText, setJsonText] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [reason, setReason] = useState("");

  const draft = useMemo(() => parseDraft(jsonText), [jsonText]);
  const preview = draft.value || config;
  const carrierRows = overrideEntries(preview?.carrier_overrides);
  const cohortRows = overrideEntries(preview?.cohort_overrides);

  const updateDraft = (mutate: (draft: AdminNetworkRolloutConfig) => void): void => {
    const base = draft.value || preview || config;
    if (!base) return;
    const next = JSON.parse(JSON.stringify(base)) as AdminNetworkRolloutConfig;
    next.defaults = next.defaults || {
      routing_mode_default: "all_except_ru",
      transport_profile: "legacy_reality_fallback",
      dns_policy: "ru_direct_split",
      ip_version_preference: "ipv4_only",
    };
    next.operator_lab = next.operator_lab || {
      enabled: false,
      allowlist_install_ids: [],
      allowlist_tg_ids: [],
      allowlist_node_codes: [],
      expires_at: null,
    };
    mutate(next);
    setJsonText(stringifyConfig(next));
  };

  const load = async (): Promise<void> => {
    setLoading(true);
    setError("");
    setNotice("");
    try {
      const out = await adminNetworkRolloutConfig();
      setConfig(out.network_rollout_config);
      setJsonText(stringifyConfig(out.network_rollout_config));
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Could not load network rollout config."));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const save = async (): Promise<void> => {
    const parsed = parseDraft(jsonText);
    if (!parsed.value) {
      setError(`Invalid JSON: ${parsed.error}`);
      return;
    }
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const out = await adminNetworkRolloutConfigUpdate(parsed.value, reason.trim());
      setConfig(out.network_rollout_config);
      setJsonText(stringifyConfig(out.network_rollout_config));
      setNotice(`Сетевой rollout сохранен. Причина: ${reason.trim()}`);
      setConfirmOpen(false);
      setReason("");
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Could not save network rollout config."));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="space-y-5">
      <AdminSurfaceHeader
        title="Сетевой rollout"
        description="Плотная консоль сетевого rollout: путь подключения, группы пользователей, версии фидов и тестовые allowlist."
        meta={
          <>
            <AdminBadge tone={draft.error ? "danger" : "success"}>{draft.error ? "draft invalid" : "draft valid"}</AdminBadge>
            <AdminBadge tone="neutral">version {preview?.version || "unknown"}</AdminBadge>
          </>
        }
        actions={
          <>
            <button type="button" className={adminButtonClass("secondary", "sm")} onClick={load} disabled={loading || busy}>
              <RefreshCw size={14} /> Обновить
            </button>
            <button
              type="button"
              data-testid="network-save"
              className={adminButtonClass("primary", "sm")}
              onClick={() => setConfirmOpen(true)}
              disabled={loading || busy || Boolean(draft.error)}
            >
              {busy ? <Loader2 className="animate-spin" size={14} /> : <Save size={14} />} Сохранить
            </button>
          </>
        }
      />

      {error ? <AdminInlineNote tone="danger">{error}</AdminInlineNote> : null}
      {notice ? <AdminInlineNote tone="success">{notice}</AdminInlineNote> : null}

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <AdminKpiCard label="Путь по умолчанию" value={profileDisplay(preview?.defaults?.transport_profile)} hint={preview?.defaults?.routing_mode_default || "режим не задан"} />
        <AdminKpiCard label="Исключения" value={overrideSize(preview?.carrier_overrides) + overrideSize(preview?.cohort_overrides)} hint={`${overrideSize(preview?.carrier_overrides)} оператор связи · ${overrideSize(preview?.cohort_overrides)} пользовательских групп`} />
        <AdminKpiCard
          label="Тестовый контур"
          value={preview?.operator_lab?.enabled ? "Enabled" : "Disabled"}
          hint={`${countList(preview?.operator_lab?.allowlist_install_ids)} installs · ${countList(preview?.operator_lab?.allowlist_tg_ids)} Telegram IDs`}
          tone={preview?.operator_lab?.enabled ? "accent" : "neutral"}
        />
        <AdminKpiCard label="Recovery order" value={countList(preview?.support_recovery_order)} hint={joinList(preview?.support_recovery_order)} />
      </div>

      <article className={adminPanelClass("neutral")}>
        <AdminPanelHeader
          eyebrow="structured editor"
          title="Структурированный редактор сети"
          description="Быстрые поля меняют тот же rollout-объект, который ниже остается доступен как исходный JSON для проверки и редких полей."
        />
        <div className="grid gap-3 xl:grid-cols-[1fr,1fr,1fr,1fr]">
          <label className="text-xs font-semibold text-slate-500">
            Транспорт по умолчанию
            <select
              data-testid="network-default-transport"
              value={preview?.defaults?.transport_profile || "legacy_reality_fallback"}
              onChange={(event) => updateDraft((next) => { next.defaults.transport_profile = event.target.value; })}
              className={`mt-1 ${adminFieldClass}`}
            >
              <option value="legacy_reality_fallback">legacy_reality_fallback</option>
              <option value="grpc_443_primary">grpc_443_primary</option>
              <option value="reserve_xhttp_cdn">reserve_xhttp_cdn</option>
              <option value="operator_lab">operator_lab</option>
            </select>
          </label>
          <label className="text-xs font-semibold text-slate-500">
            Маршрутизация
            <select
              data-testid="network-default-routing"
              value={preview?.defaults?.routing_mode_default || "all_except_ru"}
              onChange={(event) => updateDraft((next) => { next.defaults.routing_mode_default = event.target.value; })}
              className={`mt-1 ${adminFieldClass}`}
            >
              <option value="all_except_ru">all_except_ru</option>
              <option value="full_tunnel">full_tunnel</option>
              <option value="global">global</option>
              <option value="blocked_only">blocked_only</option>
            </select>
          </label>
          <label className="text-xs font-semibold text-slate-500">
            DNS policy
            <select
              data-testid="network-default-dns"
              value={preview?.defaults?.dns_policy || "ru_direct_split"}
              onChange={(event) => updateDraft((next) => { next.defaults.dns_policy = event.target.value; })}
              className={`mt-1 ${adminFieldClass}`}
            >
              <option value="ru_direct_split">ru_direct_split</option>
              <option value="remote_only">remote_only</option>
              <option value="system_direct">system_direct</option>
            </select>
          </label>
          <label className="text-xs font-semibold text-slate-500">
            IP preference
            <select
              value={preview?.defaults?.ip_version_preference || "ipv4_only"}
              onChange={(event) => updateDraft((next) => { next.defaults.ip_version_preference = event.target.value; })}
              className={`mt-1 ${adminFieldClass}`}
            >
              <option value="ipv4_only">ipv4_only</option>
              <option value="prefer_ipv6">prefer_ipv6</option>
              <option value="dual_stack">dual_stack</option>
            </select>
          </label>
        </div>

        <div className="mt-3 grid gap-3 xl:grid-cols-[1fr,1fr,1fr]">
          <label className="text-xs font-semibold text-slate-500">
            Порядок проверок восстановления
            <textarea
              data-testid="network-recovery-order"
              rows={5}
              value={listToLines(preview?.support_recovery_order)}
              onChange={(event) => updateDraft((next) => { next.support_recovery_order = linesToList(event.target.value); })}
              className={`mt-1 ${adminTextAreaClass} min-h-[128px] font-mono text-xs`}
            />
          </label>
          <label className="text-xs font-semibold text-slate-500">
            Operator lab install IDs
            <textarea
              rows={5}
              value={listToLines(preview?.operator_lab?.allowlist_install_ids)}
              onChange={(event) => updateDraft((next) => { next.operator_lab.allowlist_install_ids = linesToList(event.target.value); })}
              className={`mt-1 ${adminTextAreaClass} min-h-[128px] font-mono text-xs`}
            />
          </label>
          <label className="text-xs font-semibold text-slate-500">
            Operator lab node codes
            <textarea
              rows={5}
              value={listToLines(preview?.operator_lab?.allowlist_node_codes)}
              onChange={(event) => updateDraft((next) => { next.operator_lab.allowlist_node_codes = linesToList(event.target.value); })}
              className={`mt-1 ${adminTextAreaClass} min-h-[128px] font-mono text-xs`}
            />
          </label>
        </div>
      </article>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_420px]">
        <article className={adminPanelClass("neutral")}>
          <AdminPanelHeader
            eyebrow="source"
            title="Исходный JSON"
            description="Оставлен для проверки и редких полей; обычные изменения пути подключения, DNS, транспорта и allowlist делайте через структурированный редактор выше."
          />
          <textarea
            data-testid="network-source-json"
            className={`${adminTextAreaClass} min-h-[520px] font-mono text-xs leading-5`}
            value={jsonText}
            spellCheck={false}
            onChange={(event) => setJsonText(event.target.value)}
          />
          {draft.error ? (
            <div className="mt-3 flex items-start gap-2 rounded-xl border border-rose-900/60 bg-rose-950/35 p-3 text-xs leading-5 text-rose-100">
              <AlertTriangle className="mt-0.5 shrink-0" size={14} />
              <span>Invalid JSON: {draft.error}</span>
            </div>
          ) : null}
        </article>

        <div className="space-y-4">
          <article className={adminPanelClass("accent")}>
            <AdminPanelHeader eyebrow="defaults" title="Routing/status cards" description="Что получают новые назначения, если не сработала отдельная группа." />
            <dl className="space-y-3 text-sm">
              <div className={adminInsetPanelClass}>
                <dt className="text-xs text-slate-500">Путь подключения</dt>
                <dd className="mt-1 font-semibold text-slate-50">{profileDisplay(preview?.defaults?.transport_profile)}</dd>
              </div>
              <div className={adminInsetPanelClass}>
                <dt className="text-xs text-slate-500">Routing mode</dt>
                <dd className="mt-1 font-semibold text-slate-50">{preview?.defaults?.routing_mode_default || "not set"}</dd>
              </div>
              <div className={adminInsetPanelClass}>
                <dt className="text-xs text-slate-500">DNS / IP preference</dt>
                <dd className="mt-1 font-semibold text-slate-50">
                  {preview?.defaults?.dns_policy || "not set"} · {preview?.defaults?.ip_version_preference || "default"}
                </dd>
              </div>
            </dl>
          </article>

          <article className={adminPanelClass("neutral")}>
            <h3 className="sr-only">Allowlist</h3>
            <AdminPanelHeader eyebrow="Feeds" title="Allowlist" description="Feed objects are preserved as structured JSON; preview shows their operator labels." />
            <div className="space-y-2 text-sm">
              <div className={adminInsetPanelClass}>
                <p className="text-xs text-slate-500">Package catalog</p>
                <p className="mt-1 font-semibold text-slate-100">{feedLabel(preview?.package_catalog_feed)}</p>
              </div>
              <div className={adminInsetPanelClass}>
                <p className="text-xs text-slate-500">Routing rules</p>
                <p className="mt-1 font-semibold text-slate-100">{feedLabel(preview?.routing_rules_feed)}</p>
              </div>
            </div>
          </article>

          <article className={adminPanelClass(preview?.operator_lab?.enabled ? "warning" : "neutral")}>
            <AdminPanelHeader eyebrow="test lane" title="Safe test lane" description="Только для устройств оператора и выбранных узлов; не должен становиться тихим production default." />
            <div className="grid gap-2 text-xs leading-5 text-slate-300">
              <p><strong>Install IDs:</strong> {joinList(preview?.operator_lab?.allowlist_install_ids)}</p>
              <p><strong>Telegram IDs:</strong> {joinList(preview?.operator_lab?.allowlist_tg_ids)}</p>
              <p><strong>Node codes:</strong> {joinList(preview?.operator_lab?.allowlist_node_codes)}</p>
              <p><strong>Expires:</strong> {preview?.operator_lab?.expires_at || "not set"}</p>
            </div>
          </article>
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <OverrideCard title="Carrier overrides" rows={carrierRows} />
        <OverrideCard title="Audience overrides" rows={cohortRows} />
      </div>

      <AdminConfirmDialog
        open={confirmOpen}
        title="Подтвердить сохранение rollout"
        description="Это может изменить путь подключения у реальных пользователей. Добавьте причину перед сохранением."
        reason={reason}
        onReasonChange={setReason}
        onCancel={() => setConfirmOpen(false)}
        onConfirm={() => void save()}
        confirmLabel={busy ? "Сохраняем..." : "Сохранить"}
        busy={busy}
      />
    </section>
  );
}
