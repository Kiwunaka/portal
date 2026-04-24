"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { POKROV_LEGACY_THEME_STORAGE_KEYS, POKROV_THEME_STORAGE_KEY } from "@/app/branding";
import { cn } from "@/components/utils";

export type CabinetThemeMode = "system" | "light" | "dark";

const THEME_EVENT = "pokrov-theme-change";

const THEME_OPTIONS: Array<{
  mode: CabinetThemeMode;
  label: string;
  description: string;
  icon: string;
}> = [
  {
    mode: "system",
    label: "Системная",
    description: "Кабинет повторяет тему устройства.",
    icon: "routine",
  },
  {
    mode: "light",
    label: "Светлая",
    description: "Мягкий светлый кабинет с мятным фоном.",
    icon: "light_mode",
  },
  {
    mode: "dark",
    label: "Темная",
    description: "Темная тема для вечерней работы.",
    icon: "dark_mode",
  },
];

function isThemeMode(value: string | null): value is CabinetThemeMode {
  return value === "system" || value === "light" || value === "dark";
}

function readStoredThemeMode(): CabinetThemeMode {
  if (typeof window === "undefined") return "system";

  for (const key of [POKROV_THEME_STORAGE_KEY, ...POKROV_LEGACY_THEME_STORAGE_KEYS]) {
    const value = window.localStorage.getItem(key);
    if (isThemeMode(value)) {
      if (key !== POKROV_THEME_STORAGE_KEY) {
        window.localStorage.setItem(POKROV_THEME_STORAGE_KEY, value);
      }
      return value;
    }
  }

  return "system";
}

function systemPrefersDark(): boolean {
  return typeof window !== "undefined" && window.matchMedia("(prefers-color-scheme: dark)").matches;
}

function applyThemeMode(mode: CabinetThemeMode, systemDark: boolean): void {
  if (typeof document === "undefined") return;
  document.documentElement.classList.toggle("dark", mode === "dark" || (mode === "system" && systemDark));
}

export function useCabinetTheme() {
  const [mode, setModeState] = useState<CabinetThemeMode>("system");
  const [systemDark, setSystemDark] = useState(false);

  useEffect(() => {
    setModeState(readStoredThemeMode());
    setSystemDark(systemPrefersDark());
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return undefined;

    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => setSystemDark(media.matches);
    media.addEventListener("change", onChange);
    return () => media.removeEventListener("change", onChange);
  }, []);

  useEffect(() => {
    applyThemeMode(mode, systemDark);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(POKROV_THEME_STORAGE_KEY, mode);
    }
  }, [mode, systemDark]);

  useEffect(() => {
    if (typeof window === "undefined") return undefined;

    const onStorage = (event: StorageEvent) => {
      if (event.key === POKROV_THEME_STORAGE_KEY && isThemeMode(event.newValue)) {
        setModeState(event.newValue);
      }
    };
    const onThemeEvent = (event: Event) => {
      const nextMode = (event as CustomEvent<CabinetThemeMode>).detail;
      if (isThemeMode(nextMode)) setModeState(nextMode);
    };

    window.addEventListener("storage", onStorage);
    window.addEventListener(THEME_EVENT, onThemeEvent);
    return () => {
      window.removeEventListener("storage", onStorage);
      window.removeEventListener(THEME_EVENT, onThemeEvent);
    };
  }, []);

  const setMode = useCallback((nextMode: CabinetThemeMode) => {
    setModeState(nextMode);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(POKROV_THEME_STORAGE_KEY, nextMode);
      window.dispatchEvent(new CustomEvent(THEME_EVENT, { detail: nextMode }));
    }
  }, []);

  const activeLabel = useMemo(() => THEME_OPTIONS.find((item) => item.mode === mode)?.label || "Системная", [mode]);
  const activeIcon = useMemo(() => THEME_OPTIONS.find((item) => item.mode === mode)?.icon || "routine", [mode]);

  return {
    mode,
    setMode,
    activeLabel,
    activeIcon,
    options: THEME_OPTIONS,
    resolvedDark: mode === "dark" || (mode === "system" && systemDark),
  };
}

export function CabinetThemeToggle({ className }: { className?: string }) {
  const { mode, setMode, activeLabel, activeIcon, options } = useCabinetTheme();
  const currentIndex = Math.max(0, options.findIndex((item) => item.mode === mode));
  const nextMode = options[(currentIndex + 1) % options.length];

  return (
    <button
      type="button"
      onClick={() => setMode(nextMode.mode)}
      className={cn("outline-btn inline-flex h-11 items-center justify-center gap-2 rounded-2xl px-3 text-sm font-semibold", className)}
      aria-label={`Тема: ${activeLabel}. Переключить на ${nextMode.label.toLowerCase()}`}
      title={`Тема: ${activeLabel}`}
    >
      <span className="material-symbols-rounded text-[20px]">{activeIcon}</span>
      <span className="hidden lg:inline">{activeLabel}</span>
    </button>
  );
}

export function CabinetThemeControl({ className }: { className?: string }) {
  const { mode, setMode, options } = useCabinetTheme();

  return (
    <div className={cn("grid gap-3 md:grid-cols-3", className)}>
      {options.map((item) => {
        const active = item.mode === mode;
        return (
          <button
            key={item.mode}
            type="button"
            onClick={() => setMode(item.mode)}
            aria-label={`${item.label} тема`}
            aria-pressed={active}
            className={cn(
              "min-h-[8.5rem] rounded-[1.25rem] border px-4 py-4 text-left transition",
              active
                ? "border-emerald-300 bg-emerald-50 text-emerald-950 shadow-[0_18px_40px_-32px_rgba(23,107,77,0.45)] dark:border-emerald-400/30 dark:bg-emerald-400/12 dark:text-emerald-50"
                : "border-slate-200/80 bg-white text-slate-800 hover:border-emerald-200 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-100 dark:hover:border-emerald-400/20",
            )}
          >
            <span className="flex items-center justify-between gap-3">
              <span className="text-sm font-semibold">{item.label}</span>
              <span className="material-symbols-rounded text-[21px]">{item.icon}</span>
            </span>
            <span className="mt-3 block text-sm leading-6 text-slate-600 dark:text-slate-300">{item.description}</span>
          </button>
        );
      })}
    </div>
  );
}
