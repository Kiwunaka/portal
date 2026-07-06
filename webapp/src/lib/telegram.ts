/* eslint-disable @typescript-eslint/no-explicit-any */
export type TgUser = { id: number; username?: string | null };

function getWebApp(): any {
  if (typeof window === "undefined") return undefined;
  return (window as any)?.Telegram?.WebApp;
}

export function tgReady() {
  const tg = getWebApp();
  if (!tg) return;
  tg.ready();
  tg.expand();
  try {
    tg.setHeaderColor("#0b0b0e");
    tg.setBackgroundColor("#0b0b0e");
  } catch {
    // ignore
  }
}

export function getTgUser(): TgUser | null {
  const tg = getWebApp();
  const u = tg?.initDataUnsafe?.user;
  if (!u?.id) return null;
  return { id: u.id, username: u.username ?? null };
}

export function getInitData(): string {
  return getWebApp()?.initData || "";
}

export function haptic(type: "success" | "error") {
  const tg = getWebApp();
  if (!tg?.HapticFeedback) return;
  tg.HapticFeedback.notificationOccurred(type);
}

export function hapticImpact(style: "light" | "medium" | "rigid" = "light") {
  const tg = getWebApp();
  if (!tg?.HapticFeedback?.impactOccurred) return;
  tg.HapticFeedback.impactOccurred(style);
}

export function openLink(url: string) {
  const tg = getWebApp();
  if (tg?.openLink) {
    tg.openLink(url, { try_instant_view: false });
    return;
  }
  window.open(url, "_blank");
}
