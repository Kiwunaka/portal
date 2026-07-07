"use client";

import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { CircleAlert, CircleCheck, Info } from "lucide-react";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { haptic } from "@/lib/telegram";

/*
 * Cabinet toast stack: transient confirmations (copy, save, ticket sent).
 * Persistent form validation stays inline - toasts are for fire-and-forget
 * feedback only. Bottom-center on mobile, bottom-right on desktop;
 * transform/opacity-only motion; auto-dismiss with pause-on-hover;
 * notification haptic inside Telegram.
 */

export type ToastTone = "success" | "danger" | "info";

type ToastItem = {
  id: number;
  tone: ToastTone;
  message: ReactNode;
};

type ToastContextValue = {
  showToast: (message: ReactNode, tone?: ToastTone) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

const TOAST_TTL_MS = 3500;

const TONE_META = {
  success: { icon: CircleCheck, className: "border-ok-line bg-ok-bg text-ok-text" },
  danger: { icon: CircleAlert, className: "border-danger-line bg-danger-bg text-danger-text" },
  info: { icon: Info, className: "border-info-line bg-info-bg text-info-text" },
} as const;

export function useToast(): ToastContextValue {
  const context = useContext(ToastContext);
  if (!context) {
    // Render-safe fallback so pages outside the provider never crash.
    return { showToast: () => {} };
  }
  return context;
}

function ToastCard({ toast, onDismiss }: { toast: ToastItem; onDismiss: (id: number) => void }) {
  const reduceMotion = useReducedMotion();
  const timerRef = useRef<number | null>(null);
  const remainingRef = useRef(TOAST_TTL_MS);
  const startedAtRef = useRef(0);

  const clearTimer = useCallback(() => {
    if (timerRef.current !== null) {
      window.clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const armTimer = useCallback(() => {
    clearTimer();
    startedAtRef.current = Date.now();
    timerRef.current = window.setTimeout(() => onDismiss(toast.id), remainingRef.current);
  }, [clearTimer, onDismiss, toast.id]);

  const pauseTimer = useCallback(() => {
    if (timerRef.current === null) return;
    remainingRef.current = Math.max(600, remainingRef.current - (Date.now() - startedAtRef.current));
    clearTimer();
  }, [clearTimer]);

  useEffect(() => {
    armTimer();
    return clearTimer;
  }, [armTimer, clearTimer]);

  const meta = TONE_META[toast.tone];
  const Icon = meta.icon;

  return (
    <motion.button
      type="button"
      layout={!reduceMotion}
      initial={reduceMotion ? { opacity: 0 } : { opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={reduceMotion ? { opacity: 0 } : { opacity: 0, y: 8 }}
      transition={{ duration: reduceMotion ? 0 : 0.22, ease: [0.22, 1, 0.36, 1] }}
      className={`pointer-events-auto flex max-w-[min(92vw,380px)] items-center gap-2.5 rounded-control border px-4 py-3 text-left text-sm font-semibold shadow-medium ${meta.className}`}
      data-tone={toast.tone}
      onClick={() => onDismiss(toast.id)}
      onMouseEnter={pauseTimer}
      onMouseLeave={armTimer}
    >
      <Icon size={18} strokeWidth={2} className="shrink-0" aria-hidden="true" />
      <span className="min-w-0">{toast.message}</span>
    </motion.button>
  );
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const nextIdRef = useRef(1);

  const dismissToast = useCallback((id: number) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  const showToast = useCallback((message: ReactNode, tone: ToastTone = "success") => {
    const id = nextIdRef.current++;
    setToasts((current) => [...current.slice(-2), { id, tone, message }]);
    if (tone === "success") haptic("success");
    if (tone === "danger") haptic("error");
  }, []);

  const value = useMemo(() => ({ showToast }), [showToast]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div
        role="status"
        aria-live="polite"
        className="pointer-events-none fixed inset-x-0 bottom-[calc(1rem+var(--tg-safe-area-bottom,0px))] z-[70] flex flex-col items-center gap-2 px-4 lg:bottom-6 lg:items-end lg:px-6"
      >
        <AnimatePresence initial={false}>
          {toasts.map((toast) => (
            <ToastCard key={toast.id} toast={toast} onDismiss={dismissToast} />
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}
