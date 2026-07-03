"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";

import { POKROV_LEGACY_THEME_STORAGE_KEYS, POKROV_THEME_STORAGE_KEY } from "./branding";

type TelegramThemeParams = {
  bg_color?: string;
  secondary_bg_color?: string;
  text_color?: string;
  hint_color?: string;
  link_color?: string;
  button_color?: string;
  button_text_color?: string;
};

type TelegramInsets = {
  top?: number;
  bottom?: number;
  left?: number;
  right?: number;
};

type TelegramBackButton = {
  show: () => void;
  hide: () => void;
  onClick: (handler: () => void) => void;
  offClick?: (handler: () => void) => void;
};

type TelegramWebApp = {
  initData?: string;
  platform?: string;
  colorScheme?: "light" | "dark";
  themeParams?: TelegramThemeParams;
  viewportHeight?: number;
  viewportStableHeight?: number;
  safeAreaInset?: TelegramInsets;
  contentSafeAreaInset?: TelegramInsets;
  BackButton?: TelegramBackButton;
  ready: () => void;
  expand: () => void;
  disableVerticalSwipes?: () => void;
  setHeaderColor?: (color: string) => void;
  setBackgroundColor?: (color: string) => void;
  enableClosingConfirmation?: () => void;
  onEvent: (eventType: string, handler: () => void) => void;
  offEvent?: (eventType: string, handler: () => void) => void;
  HapticFeedback?: {
    impactOccurred: (style: "light" | "medium" | "heavy" | "rigid" | "soft") => void;
  };
};

declare global {
  interface Window {
    Telegram?: {
      WebApp?: TelegramWebApp;
    };
  }
}

function setRootVar(name: string, value: string): void {
  document.documentElement.style.setProperty(name, value);
}

function applyInsets(webApp: TelegramWebApp): void {
  const inset = webApp.safeAreaInset || webApp.contentSafeAreaInset || {};
  setRootVar("--tg-safe-area-top", `${inset.top || 0}px`);
  setRootVar("--tg-safe-area-bottom", `${inset.bottom || 0}px`);
  setRootVar("--tg-safe-area-left", `${inset.left || 0}px`);
  setRootVar("--tg-safe-area-right", `${inset.right || 0}px`);
}

function applyViewport(webApp: TelegramWebApp): void {
  const height = webApp.viewportStableHeight || webApp.viewportHeight || window.innerHeight;
  setRootVar("--tg-viewport-height", `${Math.round(height)}px`);
}

function applyTheme(webApp: TelegramWebApp): void {
  const theme = webApp.themeParams || {};
  if (theme.bg_color) setRootVar("--tg-theme-bg", theme.bg_color);
  if (theme.text_color) setRootVar("--tg-theme-text", theme.text_color);
  if (theme.secondary_bg_color) setRootVar("--tg-theme-bg-secondary", theme.secondary_bg_color);
  if (theme.button_color) setRootVar("--tg-theme-button", theme.button_color);

  if (theme.secondary_bg_color) webApp.setHeaderColor?.(theme.secondary_bg_color);
  if (theme.bg_color) webApp.setBackgroundColor?.(theme.bg_color);
}

function resolveBackFallback(pathname: string): string | null {
  if (pathname === "/" || pathname === "/dashboard") return null;

  if (pathname === "/pricing") {
    return "/subscription";
  }

  if (pathname.startsWith("/subscription/checkout")) {
    return "/subscription";
  }

  if (pathname === "/redeem") {
    return "/subscription";
  }

  if (pathname === "/downloads" || pathname.startsWith("/downloads/")) {
    return "/dashboard";
  }

  if (
    pathname === "/subscription" ||
    pathname === "/devices" ||
    pathname === "/statistics" ||
    pathname === "/settings" ||
    pathname === "/profile" ||
    pathname === "/support"
  ) {
    return "/dashboard";
  }

  if (pathname === "/support/legal") return "/support";
  if (pathname.startsWith("/support/")) return "/support";

  if (pathname.startsWith("/dashboard/")) return "/dashboard";

  return "/";
}

function detectHapticStyle(element: Element): "light" | "medium" | "heavy" | "rigid" | "soft" {
  if (element.closest('[data-haptic="heavy"]')) return "heavy";
  if (element.closest('[data-haptic="rigid"]')) return "rigid";
  if (element.closest('[data-haptic="soft"]')) return "soft";
  if (element.closest(".btn-primary")) return "medium";
  if (element.closest(".cab-btn--primary")) return "medium";
  return "light";
}

function readStoredThemePreference(): "light" | "dark" | null {
  for (const key of [POKROV_THEME_STORAGE_KEY, ...POKROV_LEGACY_THEME_STORAGE_KEYS]) {
    const value = window.localStorage.getItem(key);
    if (value === "light" || value === "dark") {
      if (key !== POKROV_THEME_STORAGE_KEY) {
        window.localStorage.setItem(POKROV_THEME_STORAGE_KEY, value);
      }
      return value;
    }
  }
  return null;
}

export default function TelegramWebAppInit() {
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    const webApp = window.Telegram?.WebApp;
    if (!webApp) return;
    const inTelegramContext = Boolean(webApp.initData);

    if (inTelegramContext) {
      document.documentElement.classList.add("tg-webapp");
      document.body.classList.add("tg-webapp");
    }

    webApp.ready();
    if (inTelegramContext) {
      webApp.expand();
      webApp.disableVerticalSwipes?.();
      webApp.enableClosingConfirmation?.();
    }

    const savedTheme = readStoredThemePreference();
    if (!savedTheme && webApp.colorScheme) {
      document.documentElement.classList.toggle("dark", webApp.colorScheme === "dark");
    }

    applyTheme(webApp);
    applyInsets(webApp);
    applyViewport(webApp);

    const onThemeChanged = (): void => {
      applyTheme(webApp);
      if (!savedTheme && webApp.colorScheme) {
        document.documentElement.classList.toggle("dark", webApp.colorScheme === "dark");
      }
    };

    const onViewportChanged = (): void => {
      applyInsets(webApp);
      applyViewport(webApp);
    };

    webApp.onEvent("themeChanged", onThemeChanged);
    webApp.onEvent("viewportChanged", onViewportChanged);

    const onKeyboardResize = (): void => {
      const vv = window.visualViewport;
      const currentHeight = vv?.height || window.innerHeight;
      const delta = window.innerHeight - currentHeight;
      document.body.classList.toggle("tg-keyboard-open", delta > 140);
    };

    if (inTelegramContext) {
      window.visualViewport?.addEventListener("resize", onKeyboardResize);
      window.addEventListener("resize", onKeyboardResize);
      onKeyboardResize();
    }

    let lastHapticTime = 0;
    const onPointerUp = (event: PointerEvent): void => {
      if (!inTelegramContext) return;
      const target = event.target as HTMLElement | null;
      if (!target) return;
      const interactive = target.closest("button,a,[role='button'],.haptic-tap");
      if (!interactive) return;
      const now = Date.now();
      if (now - lastHapticTime < 40) return;
      lastHapticTime = now;
      webApp.HapticFeedback?.impactOccurred(detectHapticStyle(interactive));
    };

    if (inTelegramContext) {
      document.addEventListener("pointerup", onPointerUp, { capture: true, passive: true });
    }

    return () => {
      webApp.offEvent?.("themeChanged", onThemeChanged);
      webApp.offEvent?.("viewportChanged", onViewportChanged);
      if (inTelegramContext) {
        window.visualViewport?.removeEventListener("resize", onKeyboardResize);
        window.removeEventListener("resize", onKeyboardResize);
        document.removeEventListener("pointerup", onPointerUp, true);
        document.documentElement.classList.remove("tg-webapp");
        document.body.classList.remove("tg-webapp");
      }
    };
  }, []);

  useEffect(() => {
    const webApp = window.Telegram?.WebApp;
    const backButton = webApp?.BackButton;
    if (!webApp || !backButton || !webApp.initData) return;

    const fallback = resolveBackFallback(pathname);
    if (!fallback) {
      backButton.hide();
      return;
    }

    const onBack = (): void => {
      webApp.HapticFeedback?.impactOccurred("light");
      router.push(fallback);
    };

    backButton.onClick(onBack);
    backButton.show();

    return () => {
      backButton.offClick?.(onBack);
      backButton.hide();
    };
  }, [pathname, router]);

  return null;
}
