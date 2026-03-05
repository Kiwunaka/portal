"use client";

import { usePortalSession } from "@/lib/session";
import { Shield } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useMemo } from "react";
import { ADMIN_NAV_ITEMS } from "./nav";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { loading, user } = usePortalSession();

  useEffect(() => {
    if (!loading && user && !user.is_admin) {
      router.replace("/dashboard/");
    }
  }, [loading, router, user]);

  const active = useMemo(
    () => ADMIN_NAV_ITEMS.find((item) => item.match(pathname))?.href || "/admin/dashboard",
    [pathname],
  );

  if (loading) {
    return (
      <main className="space-y-4">
        <section className="glass-card p-6">
          <p className="font-mono text-xs uppercase tracking-[0.15em] text-slate-500">админ</p>
          <h1 className="mt-2 font-display text-3xl font-bold">Загрузка админ-панели...</h1>
          <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-slate-200/60 dark:bg-slate-800">
            <div className="h-full w-1/3 animate-pulse rounded-full bg-violet-600" />
          </div>
        </section>
      </main>
    );
  }

  if (!user?.is_admin) {
    return (
      <main className="space-y-4">
        <section className="glass-card p-6">
          <p className="font-mono text-xs uppercase tracking-[0.15em] text-rose-500">доступ закрыт</p>
          <h1 className="mt-2 font-display text-3xl font-bold">Доступ только для администраторов</h1>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">Перенаправляем в пользовательский раздел.</p>
          <div className="mt-4">
            <Link href="/dashboard/" className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold uppercase tracking-[0.12em]">
              Вернуться в кабинет
            </Link>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="space-y-5">
      {/* ── Header ───────────────────────────────────── */}
      <section className="stat-card p-6">
        <div className="flex items-start gap-4">
          <div className="stat-icon stat-icon-violet">
            <Shield size={22} />
          </div>
          <div className="flex-1">
            <p className="font-mono text-xs uppercase tracking-[0.15em] text-violet-500 dark:text-violet-300">админ / портал</p>
            <h1 className="mt-1 font-display text-3xl font-bold">Панель управления</h1>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">Операции, модерация и настройка конфигурации.</p>
          </div>
        </div>
      </section>

      {/* ── Nav tabs ──────────────────────────────────── */}
      <section className="glass-card p-2">
        <nav className="flex flex-wrap gap-1.5">
          {ADMIN_NAV_ITEMS.map((item) => {
            const selected = active === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`haptic-tap inline-flex items-center gap-1.5 rounded-xl px-3.5 py-2 text-xs font-semibold uppercase tracking-[0.1em] transition-all duration-200 ${selected
                    ? "bg-gradient-to-r from-violet-600 to-violet-700 text-white shadow-lg shadow-violet-600/25"
                    : "text-slate-600 hover:bg-white/70 dark:text-slate-300 dark:hover:bg-white/10"
                  }`}
              >
                <span className="material-symbols-rounded text-base" style={{ fontSize: "16px" }}>{item.icon}</span>
                <span className="hidden sm:inline">{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </section>

      {children}
    </main>
  );
}
