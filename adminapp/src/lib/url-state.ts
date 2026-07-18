"use client";

export const URL_STATE_CHANGE_EVENT = "pokrov-admin-url-state";

export type UrlStatePrimitive = string | number | boolean | readonly string[] | null | undefined;
export type UrlStateShape = Record<string, unknown>;

export interface UrlStateCodec<T> {
  parse: (value: string | null) => T;
  serialize: (value: T) => string | null;
}

export type UrlStateCodecs<T extends UrlStateShape> = {
  [K in keyof T]: UrlStateCodec<T[K]>;
};

export const urlCodecs = {
  string(defaultValue = ""): UrlStateCodec<string> {
    return {
      parse: (value) => value ?? defaultValue,
      serialize: (value) => value.trim() || null
    };
  },
  optionalString(): UrlStateCodec<string | null> {
    return {
      parse: (value) => value?.trim() || null,
      serialize: (value) => value?.trim() || null
    };
  },
  number(defaultValue: number | null = null): UrlStateCodec<number | null> {
    return {
      parse: (value) => {
        if (value === null || value.trim() === "") return defaultValue;
        const parsed = Number(value);
        return Number.isFinite(parsed) ? parsed : defaultValue;
      },
      serialize: (value) => (value === null || !Number.isFinite(value) ? null : String(value))
    };
  },
  boolean(defaultValue = false): UrlStateCodec<boolean> {
    return {
      parse: (value) => {
        if (value === null) return defaultValue;
        return value === "1" || value.toLowerCase() === "true";
      },
      serialize: (value) => (value ? "1" : "0")
    };
  },
  enum<T extends string>(values: readonly T[], defaultValue: T): UrlStateCodec<T> {
    const approved = new Set<string>(values);
    return {
      parse: (value) => (value !== null && approved.has(value) ? (value as T) : defaultValue),
      serialize: (value) => (approved.has(value) ? value : defaultValue)
    };
  },
  stringList(separator = ","): UrlStateCodec<string[]> {
    return {
      parse: (value) => value?.split(separator).map((item) => item.trim()).filter(Boolean) ?? [],
      serialize: (value) => value.map((item) => item.trim()).filter(Boolean).join(separator) || null
    };
  }
};

function paramsFrom(search?: string | URLSearchParams): URLSearchParams {
  if (search instanceof URLSearchParams) return new URLSearchParams(search);
  if (typeof search === "string") return new URLSearchParams(search);
  if (typeof window === "undefined") return new URLSearchParams();
  return new URLSearchParams(window.location.search);
}

export function readUrlState<T extends UrlStateShape>(
  codecs?: Partial<UrlStateCodecs<T>>,
  search?: string | URLSearchParams
): T {
  const params = paramsFrom(search);
  const state: Record<string, unknown> = {};

  if (codecs) {
    for (const [key, codec] of Object.entries(codecs) as Array<[keyof T & string, UrlStateCodec<T[keyof T]>]>) {
      state[key] = codec.parse(params.get(key));
    }
    return state as T;
  }

  params.forEach((value, key) => {
    state[key] = value;
  });
  return state as T;
}

function serializePrimitive(value: unknown): string | null {
  if (value === null || value === undefined) return null;
  if (Array.isArray(value)) {
    return value.map((item) => String(item).trim()).filter(Boolean).join(",") || null;
  }
  if (typeof value === "boolean") return value ? "1" : "0";
  if (typeof value === "number") return Number.isFinite(value) ? String(value) : null;
  const text = String(value).trim();
  return text || null;
}

function writeUrlState<T extends UrlStateShape>(
  method: "pushState" | "replaceState",
  patch: Partial<T>,
  codecs?: Partial<UrlStateCodecs<T>>
): URL | null {
  if (typeof window === "undefined") return null;
  const url = new URL(window.location.href);

  const codecMap = codecs as Record<string, UrlStateCodec<unknown>> | undefined;
  for (const [key, value] of Object.entries(patch)) {
    const codec = codecMap?.[key];
    const serialized = codec ? codec.serialize(value) : serializePrimitive(value);
    if (serialized === null) url.searchParams.delete(key);
    else url.searchParams.set(key, serialized);
  }

  const href = `${url.pathname}${url.search}${url.hash}`;
  const currentState = window.history.state && typeof window.history.state === "object" ? window.history.state : {};
  window.history[method]({ ...currentState, pokrovAdminUrlState: true }, "", href);
  window.dispatchEvent(new Event(URL_STATE_CHANGE_EVENT));
  return url;
}

export function replaceUrlState<T extends UrlStateShape>(
  patch: Partial<T>,
  codecs?: Partial<UrlStateCodecs<T>>
): URL | null {
  return writeUrlState("replaceState", patch, codecs);
}

export function pushUrlState<T extends UrlStateShape>(
  patch: Partial<T>,
  codecs?: Partial<UrlStateCodecs<T>>
): URL | null {
  return writeUrlState("pushState", patch, codecs);
}

export function subscribeToUrlState<T extends UrlStateShape>(
  codecs: Partial<UrlStateCodecs<T>>,
  listener: (state: T) => void
): () => void {
  if (typeof window === "undefined") return () => undefined;
  const notify = () => listener(readUrlState(codecs));
  window.addEventListener("popstate", notify);
  window.addEventListener(URL_STATE_CHANGE_EVENT, notify);
  return () => {
    window.removeEventListener("popstate", notify);
    window.removeEventListener(URL_STATE_CHANGE_EVENT, notify);
  };
}

export const listenToUrlState = subscribeToUrlState;
