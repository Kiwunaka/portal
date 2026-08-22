"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode
} from "react";

type RefreshHandler = () => void;

type RefreshRegistry = {
  scope: string;
  register: (handler: RefreshHandler) => () => void;
  canRefresh: boolean;
  refresh: () => void;
};

const RouteRefreshContext = createContext<RefreshRegistry | null>(null);

export function RouteRefreshProvider({
  scope,
  children
}: {
  scope: string;
  children: ReactNode;
}) {
  const handlersRef = useRef(new Map<number, { scope: string; handler: RefreshHandler }>());
  const nextIdRef = useRef(1);
  const [counts, setCounts] = useState<Record<string, number>>({});

  const register = useCallback((handler: RefreshHandler) => {
    const id = nextIdRef.current++;
    handlersRef.current.set(id, { scope, handler });
    setCounts((current) => ({ ...current, [scope]: (current[scope] || 0) + 1 }));
    return () => {
      if (!handlersRef.current.delete(id)) return;
      setCounts((current) => ({ ...current, [scope]: Math.max(0, (current[scope] || 0) - 1) }));
    };
  }, [scope]);

  const refresh = useCallback(() => {
    for (const registration of handlersRef.current.values()) {
      if (registration.scope === scope) registration.handler();
    }
  }, [scope]);

  const canRefresh = (counts[scope] || 0) > 0;
  const value = useMemo<RefreshRegistry>(
    () => ({ scope, register, canRefresh, refresh }),
    [canRefresh, refresh, register, scope]
  );

  return (
    <RouteRefreshContext.Provider value={value}>
      {children}
    </RouteRefreshContext.Provider>
  );
}

export function useRouteRefreshControls(): Pick<RefreshRegistry, "canRefresh" | "refresh"> {
  const registry = useContext(RouteRefreshContext);
  return registry
    ? { canRefresh: registry.canRefresh, refresh: registry.refresh }
    : { canRefresh: false, refresh: () => undefined };
}

export function useRouteRefreshRegistration(handler: RefreshHandler, enabled = true): void {
  const registry = useContext(RouteRefreshContext);

  useEffect(() => {
    if (!registry || !enabled) return;
    return registry.register(handler);
  }, [enabled, handler, registry]);
}
