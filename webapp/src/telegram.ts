export type TgUser = { id: number; username?: string | null };

declare global {
  interface Window {
    Telegram?: any;
  }
}

export function tgReady() {
  const tg = window.Telegram?.WebApp;
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
  const tg = window.Telegram?.WebApp;
  const u = tg?.initDataUnsafe?.user;
  if (!u?.id) return null;
  return { id: u.id, username: u.username ?? null };
}

export function getInitData(): string {
  return window.Telegram?.WebApp?.initData || "";
}

export function haptic(type: "success" | "error") {
  const tg = window.Telegram?.WebApp;
  if (!tg?.HapticFeedback) return;
  tg.HapticFeedback.notificationOccurred(type);
}

export function openLink(url: string) {
  const tg = window.Telegram?.WebApp;
  if (tg?.openLink) {
    tg.openLink(url, { try_instant_view: false });
    return;
  }
  window.open(url, "_blank");
}

