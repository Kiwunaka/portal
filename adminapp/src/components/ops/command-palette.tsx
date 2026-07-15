"use client";

import { Search } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import { Dialog } from "@/components/ui/dialog";
import { AdminApiError, apiFetch } from "@/lib/api";
import { OPS_SECTIONS } from "@/lib/sections";

export type AdminSearchResult = {
  kind: "user" | "order" | "node" | "key";
  id: string;
  title: string;
  subtitle: string;
  href: string;
};

type SearchState = "idle" | "loading" | "ready" | "unavailable" | "error";

const SEARCH_KINDS = new Set<AdminSearchResult["kind"]>(["user", "order", "node", "key"]);
const SEARCH_RESULT_FIELDS = new Set(["kind", "id", "title", "subtitle", "href"]);
const ADMIN_ORIGIN = "https://admin.pokrov.space";
const RAW_IP_PATTERN = /\b(?:\d{1,3}\.){3}\d{1,3}\b/;
const PROTOCOL_RELATIVE_URL_PATTERN = /(?:^|[\s([{'"`])\/\/[^\s]+/;
const BARE_DOMAIN_PATTERN = /\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}(?::\d{1,5})?(?:\/[^\s]*)?/i;
const SCHEME_MARKER_PATTERN = /(?:^|[^a-z0-9+.-])[a-z][a-z0-9+.-]*:/i;
const SENSITIVE_WORD_PATTERN = /(?:^|[^a-zа-яё0-9])(?:token|токен(?:а|у|ом|е|ы|ов|ами|ах)?|subscription|подписк(?:а|и|е|у|ой|ою|ам|ами|ах)?|private|secret|authorization|bearer|password|парол(?:ь|я|ю|ем|и)?|секрет(?:а|у|ом|е|ы|ов|ами|ах)?)(?=$|[^a-zа-яё0-9])/i;
const SECRET_QUERY_KEY = /(?:token|secret|subscription|private|config|raw[_-]?ip)/i;

function hasIpv6(value: string): boolean {
  const candidates = value.match(/[0-9a-f:]*:[0-9a-f:]*/gi) || [];
  return candidates.some((candidate) => {
    if (candidate.length < 2) return false;
    const parts = candidate.split(":");
    const validParts = parts.filter(Boolean);
    if (!validParts.every((part) => /^[0-9a-f]{1,4}$/i.test(part))) return false;
    if (candidate.includes("::")) {
      return candidate.indexOf("::") === candidate.lastIndexOf("::") && validParts.length <= 7;
    }
    return parts.length === 8;
  });
}

function hasUnsafeVisibleValue(value: string): boolean {
  return (
    RAW_IP_PATTERN.test(value) ||
    hasIpv6(value) ||
    PROTOCOL_RELATIVE_URL_PATTERN.test(value) ||
    BARE_DOMAIN_PATTERN.test(value) ||
    SCHEME_MARKER_PATTERN.test(value) ||
    SENSITIVE_WORD_PATTERN.test(value) ||
    value.includes("\\")
  );
}

function canonicalHref(value: string): string | null {
  if (!value.startsWith("/") || value.startsWith("//") || value.includes("\\")) return null;
  let url: URL;
  try {
    url = new URL(value, ADMIN_ORIGIN);
  } catch {
    return null;
  }
  if (url.origin !== ADMIN_ORIGIN || url.hash) return null;
  const pathname = url.pathname === "/" ? "/" : url.pathname.replace(/\/+$/, "");
  if (!OPS_SECTIONS.some((section) => section.href === pathname)) return null;
  for (const [key, queryValue] of url.searchParams) {
    if (SECRET_QUERY_KEY.test(key) || hasUnsafeVisibleValue(key) || hasUnsafeVisibleValue(queryValue)) return null;
  }
  return `${pathname}${url.search}`;
}

function normalizeResult(value: unknown): AdminSearchResult | null {
  if (!value || typeof value !== "object") return null;
  const record = value as Record<string, unknown>;
  const fields = Object.keys(record);
  if (fields.length !== SEARCH_RESULT_FIELDS.size || fields.some((field) => !SEARCH_RESULT_FIELDS.has(field))) return null;
  if (![record.kind, record.id, record.title, record.subtitle, record.href].every((field) => typeof field === "string")) return null;
  const kind = record.kind as AdminSearchResult["kind"];
  const id = (record.id as string).trim();
  const title = (record.title as string).trim();
  const subtitle = (record.subtitle as string).trim();
  const href = canonicalHref((record.href as string).trim());
  if (!SEARCH_KINDS.has(kind) || !id || !title || !subtitle || !href) return null;
  if ([id, title, subtitle].some(hasUnsafeVisibleValue)) return null;
  return { kind, id, title, subtitle, href };
}

function resultsFromPayload(payload: unknown): AdminSearchResult[] {
  const raw = Array.isArray(payload)
    ? payload
    : payload && typeof payload === "object" && Array.isArray((payload as { results?: unknown }).results)
      ? ((payload as { results: unknown[] }).results)
      : [];
  return raw.map(normalizeResult).filter((item): item is AdminSearchResult => item !== null);
}

const KIND_LABELS: Record<AdminSearchResult["kind"], string> = {
  user: "Пользователь",
  order: "Заказ",
  node: "Нода",
  key: "Ключ"
};

export interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onNavigate: (href: string) => void;
}

export function CommandPalette({ open, onOpenChange, onNavigate }: CommandPaletteProps) {
  const searchInputRef = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<AdminSearchResult[]>([]);
  const [searchState, setSearchState] = useState<SearchState>("idle");
  const trimmedQuery = useMemo(() => query.trim(), [query]);

  useEffect(() => {
    if (!open || trimmedQuery.length < 2) return;

    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      apiFetch<unknown>(`/api/admin/search?q=${encodeURIComponent(trimmedQuery)}`, {
        method: "GET",
        signal: controller.signal
      })
        .then((payload) => {
          if (controller.signal.aborted) return;
          setResults(resultsFromPayload(payload));
          setSearchState("ready");
        })
        .catch((error: unknown) => {
          if (controller.signal.aborted) return;
          setResults([]);
          setSearchState(error instanceof AdminApiError && error.status === 404 ? "unavailable" : "error");
        });
    }, 200);

    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [open, trimmedQuery]);

  function choose(href: string) {
    onNavigate(href);
    onOpenChange(false);
  }

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title="Палитра команд"
      description="Перейдите в раздел или найдите пользователя, заказ, ноду либо ключ."
      className="max-w-3xl"
      initialFocusRef={searchInputRef}
    >
      <label className="relative block">
        <span className="sr-only">Глобальный поиск</span>
        <Search aria-hidden="true" className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[color:var(--atlas-text-muted)]" size={17} />
        <input
          ref={searchInputRef}
          type="search"
          aria-label="Глобальный поиск"
          autoComplete="off"
          value={query}
          onChange={(event) => {
            const nextQuery = event.target.value;
            setQuery(nextQuery);
            setResults([]);
            setSearchState(nextQuery.trim().length >= 2 ? "loading" : "idle");
          }}
          placeholder="Введите ID, имя, заказ, ноду или ключ"
          className="h-11 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] pl-10 pr-3 text-sm outline-none transition focus:border-[color:var(--atlas-focus)] focus:ring-2 focus:ring-[color:var(--atlas-focus)]/30"
        />
      </label>

      <div className="mt-4 max-h-[58vh] space-y-5 overflow-y-auto pr-1">
        <section aria-labelledby="command-navigation-title">
          <h3 id="command-navigation-title" className="mb-2 text-xs font-semibold uppercase tracking-[0.08em] text-[color:var(--atlas-text-muted)]">
            Переходы по разделам
          </h3>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {OPS_SECTIONS.map((section) => (
              <button
                key={section.id}
                type="button"
                onClick={() => choose(section.href)}
                className="min-h-10 rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas-alt)] px-3 text-left text-xs font-semibold text-[color:var(--atlas-text)] transition hover:border-[color:var(--atlas-border-strong)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--atlas-focus)]"
              >
                {section.label}
              </button>
            ))}
          </div>
        </section>

        <section aria-labelledby="command-search-title">
          <h3 id="command-search-title" className="mb-2 text-xs font-semibold uppercase tracking-[0.08em] text-[color:var(--atlas-text-muted)]">
            Результаты поиска
          </h3>
          {trimmedQuery.length < 2 ? (
            <p className="rounded-[var(--pokrov-radius-card)] border border-dashed border-[color:var(--atlas-border)] px-3 py-3 text-xs text-[color:var(--atlas-text-soft)]">
              Введите минимум два символа, чтобы начать поиск.
            </p>
          ) : null}
          {searchState === "loading" ? <p role="status" className="text-xs text-[color:var(--atlas-text-soft)]">Ищем совпадения…</p> : null}
          {searchState === "unavailable" ? (
            <p role="status" className="rounded-[var(--pokrov-radius-card)] border border-[color:var(--command-status-warning-line)] bg-[color:var(--command-status-warning-bg)] px-3 py-3 text-xs text-[color:var(--command-status-warning-text)]">
              Поиск пока недоступен
            </p>
          ) : null}
          {searchState === "error" ? (
            <p role="alert" className="rounded-[var(--pokrov-radius-card)] border border-[color:var(--command-status-danger-line)] bg-[color:var(--command-status-danger-bg)] px-3 py-3 text-xs text-[color:var(--command-status-danger-text)]">
              Не удалось выполнить поиск. Проверьте сессию и повторите.
            </p>
          ) : null}
          {searchState === "ready" && results.length === 0 ? (
            <p role="status" className="rounded-[var(--pokrov-radius-card)] border border-dashed border-[color:var(--atlas-border)] px-3 py-3 text-xs text-[color:var(--atlas-text-soft)]">
              Совпадений нет. Уточните запрос и попробуйте снова.
            </p>
          ) : null}
          {results.length ? (
            <div className="space-y-2">
              {results.map((result) => (
                <button
                  key={`${result.kind}:${result.id}`}
                  type="button"
                  onClick={() => choose(result.href)}
                  className="flex w-full items-start gap-3 rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 py-3 text-left transition hover:border-[color:var(--atlas-border-strong)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--atlas-focus)]"
                >
                  <span className="mt-0.5 rounded-full border border-[color:var(--atlas-border)] px-2 py-0.5 text-[10px] font-semibold text-[color:var(--atlas-text-muted)]">
                    {KIND_LABELS[result.kind]}
                  </span>
                  <span className="min-w-0">
                    <span className="block truncate text-sm font-semibold text-[color:var(--atlas-text)]">{result.title}</span>
                    <span className="mt-1 block truncate text-xs text-[color:var(--atlas-text-soft)]">{result.subtitle}</span>
                  </span>
                </button>
              ))}
            </div>
          ) : null}
        </section>
      </div>
    </Dialog>
  );
}
