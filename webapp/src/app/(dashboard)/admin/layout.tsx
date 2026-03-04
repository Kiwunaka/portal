"use client";

import { usePortalSession } from "@/lib/session";
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
          <p className="font-mono text-xs uppercase tracking-[0.15em] text-slate-500">admin</p>
          <h1 className="mt-2 font-display text-3xl font-bold">Загрузка админ-панели...</h1>
        </section>
      </main>
    );
  }

  if (!user?.is_admin) {
    return (
      <main className="space-y-4">
        <section className="glass-card p-6">
          <p className="font-mono text-xs uppercase tracking-[0.15em] text-rose-500">access denied</p>
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
      <section className="glass-card p-5">
        <p className="font-mono text-xs uppercase tracking-[0.15em] text-violet-500 dark:text-violet-300">admin / portal</p>
        <h1 className="mt-2 font-display text-3xl font-bold">Панель управления</h1>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">Оперативные действия, модерация пользователей и управление конфигурацией.</p>
      </section>

      <section className="glass-card p-3">
        <nav className="grid grid-cols-2 gap-2 md:grid-cols-4 xl:grid-cols-8">
          {ADMIN_NAV_ITEMS.map((item) => {
            const selected = active === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`haptic-tap rounded-xl px-3 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-center transition ${
                  selected ? "bg-violet-600 text-white" : "bg-white/70 text-slate-700 dark:bg-white/10 dark:text-slate-200"
                }`}
              >
                <span className="material-symbols-rounded mr-1 align-[-0.2em] text-base">{item.icon}</span>
                {item.label}
              </Link>
            );
          })}
        </nav>
      </section>

      {children}
    </main>
  );
}
