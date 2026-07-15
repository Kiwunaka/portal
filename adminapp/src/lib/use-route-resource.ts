"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { AdminApiError } from "@/lib/admin-api/client";

export type RouteResourceState<T> = {
  data: T | null;
  error: AdminApiError | null;
  loading: boolean;
  refreshing: boolean;
  updatedAt: string | null;
  reload: () => void;
};

function isAbortError(error: unknown): boolean {
  return Boolean(error && typeof error === "object" && "name" in error && error.name === "AbortError");
}

function asAdminApiError(error: unknown): AdminApiError {
  if (error instanceof AdminApiError) return error;
  const message = error instanceof Error && error.message.trim()
    ? error.message
    : "Источник не ответил. Повторите загрузку.";
  return new AdminApiError(message, 0, null, null);
}

export function useRouteResource<T>(
  key: string,
  load: (signal: AbortSignal) => Promise<T>,
  options: { pollMs?: number; enabled?: boolean }
): RouteResourceState<T> {
  const enabled = options.enabled ?? true;
  const pollMs = options.pollMs;
  const loadRef = useRef(load);
  const generationRef = useRef(0);
  const successfulKeyRef = useRef<string | null>(null);
  const [reloadVersion, setReloadVersion] = useState(0);
  const [state, setState] = useState<Omit<RouteResourceState<T>, "reload">>({
    data: null,
    error: null,
    loading: enabled,
    refreshing: false,
    updatedAt: null
  });

  useEffect(() => {
    loadRef.current = load;
  }, [load]);

  const reload = useCallback(() => {
    setReloadVersion((version) => version + 1);
  }, []);

  useEffect(() => {
    const generation = ++generationRef.current;
    const controller = new AbortController();

    if (!enabled) {
      queueMicrotask(() => {
        if (generation !== generationRef.current) return;
        setState((current) => ({ ...current, error: null, loading: false, refreshing: false }));
      });
      return () => {
        controller.abort();
        generationRef.current += 1;
      };
    }

    queueMicrotask(() => {
      if (generation !== generationRef.current) return;
      setState((current) => {
        const canRefresh = successfulKeyRef.current === key && current.data !== null;
        return {
          data: canRefresh ? current.data : null,
          error: null,
          loading: !canRefresh,
          refreshing: canRefresh,
          updatedAt: canRefresh ? current.updatedAt : null
        };
      });
    });

    void loadRef.current(controller.signal)
      .then((data) => {
        if (controller.signal.aborted || generation !== generationRef.current) return;
        successfulKeyRef.current = key;
        setState({
          data,
          error: null,
          loading: false,
          refreshing: false,
          updatedAt: new Date().toISOString()
        });
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted || generation !== generationRef.current || isAbortError(error)) return;
        setState((current) => ({
          ...current,
          error: asAdminApiError(error),
          loading: false,
          refreshing: false
        }));
      });

    return () => {
      controller.abort();
      generationRef.current += 1;
    };
  }, [enabled, key, reloadVersion]);

  useEffect(() => {
    if (!enabled || !pollMs || pollMs <= 0) return;

    let timer: number | null = null;
    const clearTimer = () => {
      if (timer === null) return;
      window.clearTimeout(timer);
      timer = null;
    };
    const schedule = () => {
      clearTimer();
      if (document.visibilityState !== "visible") return;
      timer = window.setTimeout(() => {
        reload();
        schedule();
      }, pollMs);
    };
    const handleVisibilityChange = () => {
      if (document.visibilityState !== "visible") {
        clearTimer();
        return;
      }
      reload();
      schedule();
    };

    schedule();
    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () => {
      clearTimer();
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [enabled, key, pollMs, reload]);

  return { ...state, reload };
}
