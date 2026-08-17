"use client";

import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import { CheckCircle2, Clock3, ExternalLink, FilePenLine, RefreshCw, Rss } from "lucide-react";

import { ActionIntentDialog } from "@/components/ops/action-intent-dialog";
import { RouteBoundary } from "@/components/ops/route-boundary";
import type { OpsShellStatus } from "@/components/ops/shell-status";
import { Badge, Button, Card, EmptyState, MetricCell, MetricStrip, SectionTitle } from "@/components/ui";
import type { ActionIntentRequest } from "@/lib/admin-api/actions";
import { fetchNewsDrafts, type NewsDraftRow } from "@/lib/admin-api/control";
import { useRouteResource } from "@/lib/use-route-resource";

type EditorDraft = { title: string; summary: string; link: string };

function formatDate(value: string | null): string {
  if (!value || Number.isNaN(Date.parse(value))) return "—";
  return new Date(value).toLocaleString("ru-RU", { dateStyle: "short", timeStyle: "short" });
}

function editorFrom(row: NewsDraftRow | null): EditorDraft {
  return {
    title: row?.source_title || "",
    summary: "",
    link: row?.source_url || "",
  };
}

export function NewsPage({ onShellStatus }: { onShellStatus?: (status: OpsShellStatus) => void }) {
  const load = useCallback((signal: AbortSignal) => fetchNewsDrafts({ signal }), []);
  const resource = useRouteResource("news-drafts", load, { enabled: true, pollMs: 60_000 });
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [editor, setEditor] = useState<EditorDraft>(editorFrom(null));
  const [formError, setFormError] = useState("");
  const [request, setRequest] = useState<ActionIntentRequest | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  const pending = useMemo(
    () => (resource.data?.drafts || []).filter((row) => row.status === "pending"),
    [resource.data?.drafts],
  );
  const selected = pending.find((row) => row.id === selectedId) || null;

  useEffect(() => {
    onShellStatus?.({
      api: resource.error ? resource.data ? "degraded" : "failed" : resource.loading ? "missing" : "ok",
      session: resource.data ? "ok" : resource.error ? "unavailable" : "missing",
      oldestRequiredSourceAt: resource.data?.freshness_at || null,
    });
  }, [onShellStatus, resource.data, resource.error, resource.loading]);

  function choose(row: NewsDraftRow) {
    setSelectedId(row.id);
    setEditor(editorFrom(row));
    setFormError("");
  }

  function reload() {
    setSelectedId(null);
    setEditor(editorFrom(null));
    resource.reload();
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    if (!selected) return;
    const title = editor.title.trim();
    const summary = editor.summary.trim();
    let validLink = false;
    try {
      validLink = new URL(editor.link).protocol === "https:";
    } catch {
      validLink = false;
    }
    if (title.length < 2 || title.length > 160) {
      setFormError("Заголовок должен содержать от 2 до 160 символов.");
      return;
    }
    if (summary.length < 20 || summary.length > 600) {
      setFormError("Напишите собственную краткую выжимку: от 20 до 600 символов.");
      return;
    }
    if (!validLink) {
      setFormError("Нужна корректная HTTPS-ссылка на источник.");
      return;
    }
    setFormError("");
    setRequest({
      action: "live_update.create",
      target: { type: "live_update", id: "new" },
      payload: {
        source_draft_id: selected.id,
        title,
        summary,
        link: editor.link,
        is_active: true,
        sort_order: 100,
      },
      endpoint: "/api/admin/live-updates",
      method: "POST",
    });
    setDialogOpen(true);
  }

  const latest = resource.data?.latest_run || null;

  return (
    <div className="ops-page space-y-3">
      <div className="ops-route-toolbar">
        <div className="flex flex-wrap items-center gap-2 text-xs text-[color:var(--atlas-text-soft)]">
          <Badge tone={resource.data?.worker.enabled ? "success" : "warning"}>
            {resource.data?.worker.enabled ? "Ежедневный сбор включён" : "Сбор выключен"}
          </Badge>
          <span>Система сохраняет только заголовок и ссылку. Публикация всегда требует ручного L2-подтверждения.</span>
        </div>
        <Button tone="secondary" disabled={resource.loading || resource.refreshing} onClick={resource.reload}>
          <RefreshCw size={15} className={resource.refreshing ? "animate-spin" : ""} /> Обновить
        </Button>
      </div>

      <MetricStrip label="Сбор новостей">
        <MetricCell icon={<FilePenLine aria-hidden="true" size={17} />} label="На проверке" value={resource.data?.counts.pending ?? "—"} detail="Не публиковались" tone="info" />
        <MetricCell icon={<CheckCircle2 aria-hidden="true" size={17} />} label="Подтверждено" value={resource.data?.counts.approved ?? "—"} detail="Созданы публичные карточки" tone="success" />
        <MetricCell icon={<Rss aria-hidden="true" size={17} />} label="Источники" value={resource.data?.worker.sources.length ?? "—"} detail={latest ? `${latest.sources_succeeded}/${latest.sources_total} в последнем запуске` : "Запусков ещё не было"} tone={latest?.sources_failed ? "warning" : "neutral"} />
        <MetricCell icon={<Clock3 aria-hidden="true" size={17} />} label="Свежесть" value={formatDate(resource.data?.freshness_at || null)} detail={latest?.duration_ms === null || latest?.duration_ms === undefined ? "Длительность неизвестна" : `${latest.duration_ms} мс`} tone={latest?.status === "completed" ? "success" : latest ? "warning" : "neutral"} />
      </MetricStrip>

      <section className="ops-workspace xl:grid-cols-[minmax(0,1.25fr)_minmax(22rem,0.75fr)]">
        <Card>
          <SectionTitle title="Черновики" description="Заголовок источника — только повод. Перед публикацией нужна собственная русская выжимка." />
          <RouteBoundary loading={resource.loading} refreshing={resource.refreshing} error={resource.error} hasData={resource.data !== null} retryLabel="Повторить загрузку черновиков" onRetry={resource.reload}>
            {pending.length ? (
              <div className="mt-3 space-y-2">
                {pending.map((row) => (
                  <button key={row.id} type="button" onClick={() => choose(row)} className={`w-full rounded-[var(--pokrov-radius-control)] border p-3 text-left transition ${selectedId === row.id ? "border-[color:var(--atlas-accent)] bg-[color:var(--atlas-accent-soft)]" : "border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] hover:border-[color:var(--atlas-border-strong)]"}`}>
                    <span className="block text-xs text-[color:var(--atlas-text-muted)]">{row.source_name} · {formatDate(row.source_published_at)}</span>
                    <span className="mt-1 block text-sm font-semibold">{row.source_title}</span>
                    <span className="mt-1 block text-xs text-[color:var(--atlas-text-soft)]">Обнаружено: {formatDate(row.discovered_at)}</span>
                  </button>
                ))}
              </div>
            ) : resource.data ? <EmptyState title="Новых черновиков нет" description="Следующий сбор проверит источники, но дубликаты повторно не появятся." /> : null}
          </RouteBoundary>
        </Card>

        <aside aria-label="Редактор новости">
          <Card className="xl:sticky xl:top-[7.75rem]">
            <SectionTitle title={selected ? "Редактор публикации" : "Выберите черновик"} description="Источник открывается отдельно; текст не копируется автоматически." />
            {!selected ? <EmptyState description="Выберите заголовок слева." /> : (
              <form className="mt-3 space-y-3" onSubmit={submit}>
                <a href={selected.source_url} target="_blank" rel="noreferrer" className="inline-flex min-h-10 items-center gap-2 text-xs font-semibold text-[color:var(--atlas-accent)] hover:underline">Открыть источник <ExternalLink size={14} /></a>
                {formError ? <p role="alert" className="text-xs text-[color:var(--atlas-status-danger-text)]">{formError}</p> : null}
                <label className="block text-xs font-semibold">Заголовок<input aria-label="Заголовок новости" value={editor.title} maxLength={160} onChange={(event) => setEditor((current) => ({ ...current, title: event.target.value }))} className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3" /></label>
                <label className="block text-xs font-semibold">Собственная выжимка<textarea aria-label="Краткая выжимка новости" value={editor.summary} maxLength={600} rows={7} onChange={(event) => setEditor((current) => ({ ...current, summary: event.target.value }))} className="mt-1 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3" placeholder="Что произошло и почему это важно пользователю POKROV" /></label>
                <label className="block text-xs font-semibold">Ссылка<input aria-label="Ссылка на источник" value={editor.link} onChange={(event) => setEditor((current) => ({ ...current, link: event.target.value }))} className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3" /></label>
                <Button tone="primary" type="submit"><CheckCircle2 size={15} /> Проверить и опубликовать</Button>
              </form>
            )}
          </Card>
        </aside>
      </section>

      <ActionIntentDialog open={dialogOpen} request={request} onOpenChange={(open) => { setDialogOpen(open); if (!open) setRequest(null); }} onKnownOutcome={reload} onCheckState={resource.reload} />
    </div>
  );
}
