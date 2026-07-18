"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ArrowLeft, RefreshCw } from "lucide-react";

import { adminApiErrorText, RouteBoundary } from "@/components/ops/route-boundary";
import type { OpsShellStatus } from "@/components/ops/shell-status";
import { Badge, Button, Card, SectionTitle } from "@/components/ui";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/states";
import type { AdminApiError } from "@/lib/admin-api/client";
import { fetchOnlineUsers } from "@/lib/admin-api/support";
import { fetchUserDetail, fetchUserInvestigation, fetchUsers, type UserListSort, type UserListStatus } from "@/lib/admin-api/users";
import { pushUrlState, readUrlState, replaceUrlState, subscribeToUrlState, type UrlStateCodec, type UrlStateCodecs } from "@/lib/url-state";
import { useRouteResource } from "@/lib/use-route-resource";

import { UserDetail, USER_DETAIL_TABS, type UserDetailTab } from "./user-detail";
import { UserList, type UserListFilters } from "./user-list";

const USER_STATUSES = ["all", "active", "inactive", "expired", "blocked", "manual"] as const;
const USER_SORTS = ["created_desc", "created_asc", "expiry_asc", "expiry_desc", "name_asc", "name_desc"] as const;

type UsersUrlState = UserListFilters & {
  selected: number | null;
  tab: UserDetailTab;
};

function cleanStringCodec(defaultValue = ""): UrlStateCodec<string> {
  return {
    parse: (value) => value?.trim() || defaultValue,
    serialize: (value) => value.trim() || null,
  };
}

function cleanEnumCodec<T extends string>(values: readonly T[], defaultValue: T): UrlStateCodec<T> {
  const allowed = new Set(values);
  return {
    parse: (value) => value && allowed.has(value as T) ? value as T : defaultValue,
    serialize: (value) => value === defaultValue ? null : value,
  };
}

const signedUserIdCodec: UrlStateCodec<number | null> = {
  parse: (value) => {
    if (!value || !/^-?[1-9]\d*$/.test(value)) return null;
    const parsed = Number(value);
    return Number.isSafeInteger(parsed) ? parsed : null;
  },
  serialize: (value) => value !== null && Number.isSafeInteger(value) && value !== 0 ? String(value) : null,
};

const USERS_URL_CODECS: UrlStateCodecs<UsersUrlState> = {
  q: cleanStringCodec(),
  status: cleanEnumCodec<UserListStatus>(USER_STATUSES, "all"),
  sort: cleanEnumCodec<UserListSort>(USER_SORTS, "created_desc"),
  selected: signedUserIdCodec,
  tab: cleanEnumCodec<UserDetailTab>(USER_DETAIL_TABS, "overview"),
};

function isAccessDenied(error: AdminApiError | null): boolean {
  return Boolean(error && (error.status === 401 || error.status === 403));
}

export function UsersPage({ onShellStatus }: { onShellStatus?: (status: OpsShellStatus) => void }) {
  const [urlState, setUrlState] = useState<UsersUrlState>(() => readUrlState(USERS_URL_CODECS));
  const selected = urlState.selected;
  const investigationActive = selected !== null && urlState.tab === "investigation";
  const listScrollRef = useRef<HTMLDivElement | null>(null);
  const openedFromListRef = useRef(false);

  useEffect(() => subscribeToUrlState<UsersUrlState>(USERS_URL_CODECS, setUrlState), []);

  const loadUsers = useCallback((signal: AbortSignal) => fetchUsers({
    q: urlState.q,
    status: urlState.status,
    sort: urlState.sort,
    limit: 80,
  }, { signal }), [urlState.q, urlState.sort, urlState.status]);
  const loadOnline = useCallback((signal: AbortSignal) => fetchOnlineUsers({ limit: 200 }, { signal }), []);
  const loadDetail = useCallback((signal: AbortSignal) => {
    if (selected === null) throw new Error("Пользователь не выбран");
    return fetchUserDetail(selected, { signal });
  }, [selected]);
  const loadInvestigation = useCallback((signal: AbortSignal) => {
    if (selected === null) throw new Error("Пользователь не выбран");
    return fetchUserInvestigation(selected, { signal });
  }, [selected]);

  const users = useRouteResource(`users:${urlState.q}:${urlState.status}:${urlState.sort}`, loadUsers, { enabled: true });
  const online = useRouteResource("users-online-snapshot", loadOnline, { enabled: true });
  const detail = useRouteResource(`user-detail:${selected ?? "none"}`, loadDetail, { enabled: selected !== null });
  const investigation = useRouteResource(`user-investigation:${selected ?? "none"}`, loadInvestigation, { enabled: investigationActive });

  const onlineByTgId = useMemo(() => new Map((online.data?.rows || []).flatMap((row) => row.tgId === null ? [] : [[row.tgId, row] as const])), [online.data]);
  const panelDegraded = Boolean(selected !== null && detail.data && detail.data.summary.panelState !== "ok");
  const onlineDegraded = Boolean(online.data?.summary.nodesWithPanelErrors);
  const embeddedSourceDegraded = panelDegraded || onlineDegraded;

  useEffect(() => {
    const errors = [users.error, online.error, selected !== null ? detail.error : null, investigationActive ? investigation.error : null].filter((error): error is AdminApiError => error !== null);
    const successCount = Number(users.data !== null) + Number(online.data !== null) + Number(selected !== null && detail.data !== null) + Number(investigationActive && investigation.data !== null);
    const sourceTimes = [users.updatedAt, online.updatedAt, selected !== null ? detail.updatedAt : null, investigationActive ? investigation.updatedAt : null]
      .filter((value): value is string => Boolean(value))
      .sort();
    onShellStatus?.({
      api: errors.length ? successCount ? "degraded" : "failed" : embeddedSourceDegraded ? "degraded" : users.loading ? "missing" : "ok",
      session: errors.some(isAccessDenied) ? "failed" : successCount ? "ok" : errors.length ? "unavailable" : "missing",
      oldestRequiredSourceAt: sourceTimes.at(0) || null,
    });
  }, [detail.data, detail.error, detail.updatedAt, embeddedSourceDegraded, investigation.data, investigation.error, investigation.updatedAt, investigationActive, onShellStatus, online.data, online.error, online.updatedAt, selected, users.data, users.error, users.loading, users.updatedAt]);

  useEffect(() => {
    if (selected !== null) return;
    const scrollTop = Number((window.history.state as { pokrovUsersListScroll?: unknown } | null)?.pokrovUsersListScroll);
    if (!Number.isFinite(scrollTop) || scrollTop <= 0) return;
    window.requestAnimationFrame(() => listScrollRef.current?.scrollTo({ top: scrollTop }));
  }, [selected, users.data]);

  function updateFilters(patch: Partial<UserListFilters>) {
    replaceUrlState<UsersUrlState>({ ...patch, selected: null, tab: "overview" }, USERS_URL_CODECS);
  }

  function selectUser(tgId: number) {
    const currentState = window.history.state && typeof window.history.state === "object" ? window.history.state : {};
    window.history.replaceState({ ...currentState, pokrovUsersListScroll: listScrollRef.current?.scrollTop || 0 }, "");
    openedFromListRef.current = true;
    pushUrlState<UsersUrlState>({ selected: tgId, tab: "overview" }, USERS_URL_CODECS);
  }

  function backToUsers() {
    if (openedFromListRef.current) {
      window.history.back();
      return;
    }
    pushUrlState<UsersUrlState>({ selected: null, tab: "overview" }, USERS_URL_CODECS);
  }

  const refreshing = users.refreshing || online.refreshing || detail.refreshing || investigation.refreshing;
  const hasError = Boolean(users.error || online.error || (selected !== null && detail.error) || (investigationActive && investigation.error) || embeddedSourceDegraded);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2 text-xs text-[color:var(--atlas-text-soft)]">
          <Badge tone={hasError ? "warning" : users.data && online.data ? "success" : "neutral"}>{hasError ? "Есть сбой источника" : users.data && online.data ? "Источники отвечают" : "Ожидаем источники"}</Badge>
          <span>{users.data ? `${users.data.total} пользователей по текущему фильтру` : "Список ещё не получен"}</span>
          {refreshing ? <Badge tone="info">Обновляем</Badge> : null}
        </div>
        <Button tone="secondary" disabled={users.loading || refreshing} onClick={() => {
          users.reload();
          online.reload();
          if (selected !== null) detail.reload();
          if (investigationActive) investigation.reload();
        }}>
          <RefreshCw size={15} className={refreshing ? "animate-spin" : ""} /> Обновить
        </Button>
      </div>

      {online.error ? (
        <ErrorState title="Оперативный снимок пользователей недоступен" description={`${adminApiErrorText(online.error, "Повторите запрос оперативного снимка.")} Основной список пользователей остаётся доступен.`} action={<Button tone="secondary" onClick={online.reload}>Повторить снимок</Button>} className="min-h-0" />
      ) : null}

      <div className="grid min-w-0 gap-4 xl:grid-cols-[minmax(0,1.05fr)_minmax(0,1.35fr)]">
        <section aria-label="Список пользователей" className={`min-w-0 ${selected !== null ? "max-xl:hidden" : ""}`}>
          <Card className="min-h-[420px] p-3">
            <SectionTitle title="Пользователи" description="Доступ, срок, план и текущий сигнал присутствия в сети видны до открытия карточки." />
            <RouteBoundary loading={users.loading} refreshing={users.refreshing} error={users.error} hasData={users.data !== null} retryLabel="Повторить загрузку пользователей" onRetry={users.reload}>
              {users.data ? (
                <UserList
                  rows={users.data.users}
                  total={users.data.total}
                  onlineByTgId={onlineByTgId}
                  onlineSampledAt={online.data?.generatedAt || null}
                  filters={urlState}
                  selected={selected}
                  onFiltersChange={updateFilters}
                  onSelect={selectUser}
                  scrollRef={listScrollRef}
                />
              ) : null}
            </RouteBoundary>
          </Card>
        </section>

        <section aria-label="Карточка пользователя" className={`min-w-0 ${selected !== null ? "" : "max-xl:hidden"}`}>
          {selected === null ? (
            <Card className="hidden min-h-[420px] xl:block"><EmptyState title="Выберите пользователя" description="Карточка загрузится отдельным запросом. Исходный IP-адрес не запрашивается до открытия вкладки «Расследование»." /></Card>
          ) : null}
          {selected !== null ? <Button tone="ghost" className="mb-2 xl:hidden" onClick={backToUsers}><ArrowLeft size={15} /> Назад к пользователям</Button> : null}
          {selected !== null && detail.loading && !detail.data ? <LoadingState title="Загружаем карточку пользователя" description="Список остаётся доступен, карточка запрашивается отдельно." /> : null}
          {selected !== null && detail.error && !detail.data ? <ErrorState title="Карточка пользователя недоступна" description={adminApiErrorText(detail.error, "Повторите запрос выбранного пользователя.")} action={<Button tone="secondary" onClick={detail.reload}>Повторить карточку</Button>} /> : null}
          {selected !== null && detail.data ? (
            <UserDetail
              data={detail.data}
              loadedAt={detail.updatedAt}
              tab={urlState.tab}
              onTabChange={(tab) => pushUrlState<UsersUrlState>({ tab }, USERS_URL_CODECS)}
              investigation={investigation.data}
              investigationLoading={investigation.loading}
              investigationError={investigation.error ? adminApiErrorText(investigation.error, "Повторите запрос расследования.") : null}
              onInvestigationRetry={investigation.reload}
              onRefresh={() => {
                users.reload();
                online.reload();
                detail.reload();
                if (investigationActive) investigation.reload();
              }}
            />
          ) : null}
        </section>
      </div>
    </div>
  );
}
