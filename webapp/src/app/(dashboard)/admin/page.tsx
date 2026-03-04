"use client";

import Link from "next/link";
import { ADMIN_NAV_ITEMS } from "./nav";

export default function AdminHomePage() {
  return (
    <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
      {ADMIN_NAV_ITEMS.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          className="glass-card haptic-tap rounded-2xl px-4 py-4 transition hover:scale-[1.01]"
        >
          <div className="flex items-center gap-2">
            <span className="material-symbols-rounded text-violet-600 dark:text-violet-300">{item.icon}</span>
            <h2 className="font-display text-lg font-semibold">{item.label}</h2>
          </div>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">Открыть раздел {item.label}.</p>
        </Link>
      ))}
    </section>
  );
}
