"use client";

import { useEffect } from "react";

import AppRouteLink from "@/components/app-route-link";

type ErrorProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function RootError({ error, reset }: ErrorProps) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <main className="mx-auto flex min-h-[100dvh] w-full max-w-5xl items-center px-4 py-8 sm:px-6">
      <section className="w-full rounded-[2rem] border border-slate-200/80 bg-white/94 p-6 shadow-[0_28px_80px_-54px_rgba(15,23,42,0.22)] dark:border-white/10 dark:bg-[#101713]/92 sm:p-8">
        <div className="grid gap-6 lg:grid-cols-[1.12fr_0.88fr]">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-rose-600 dark:text-rose-300">
              Кабинет не открыл экран
            </p>
            <h1 className="mt-2 font-display text-[clamp(2rem,5vw,3.2rem)] font-semibold leading-[0.96] tracking-[-0.04em] text-slate-950 dark:text-slate-50">
              Что-то пошло не так
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-600 dark:text-slate-300">
              Обычно помогает повторить загрузку. Если ошибка вернется, откройте поддержку: там можно продолжить один кейс и не объяснять все заново.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <button type="button" onClick={reset} className="btn-primary rounded-full px-5 py-3 text-sm font-semibold">
                Повторить
              </button>
              <AppRouteLink href="/dashboard/" className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
                В кабинет
              </AppRouteLink>
              <AppRouteLink href="/support/" className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
                Поддержка
              </AppRouteLink>
            </div>
          </div>

          <aside className="rounded-[1.6rem] border border-slate-200/80 bg-slate-50/90 p-5 dark:border-white/10 dark:bg-white/[0.04]">
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">
              Что можно сделать
            </p>
            <div className="mt-4 space-y-3">
              {[
                "Повторите открытие страницы.",
                "Если не помогло, вернитесь на главную кабинета.",
                "Для повторяющейся ошибки создайте обращение в поддержке.",
              ].map((step, index) => (
                <div key={step} className="flex gap-3 rounded-[1.15rem] border border-slate-200/80 bg-white/85 p-3 dark:border-white/10 dark:bg-white/[0.04]">
                  <span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-emerald-50 text-xs font-semibold text-emerald-800 dark:bg-emerald-400/10 dark:text-emerald-200">
                    {index + 1}
                  </span>
                  <p className="text-sm leading-6 text-slate-700 dark:text-slate-200">{step}</p>
                </div>
              ))}
            </div>
          </aside>
        </div>
      </section>
    </main>
  );
}
