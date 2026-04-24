import AppRouteLink from "@/components/app-route-link";

export default function NotFound() {
  return (
    <main className="mx-auto flex min-h-[100dvh] w-full max-w-5xl items-center px-4 py-8 sm:px-6">
      <section className="w-full rounded-[2rem] border border-slate-200/80 bg-white/94 p-6 shadow-[0_28px_80px_-54px_rgba(15,23,42,0.22)] dark:border-white/10 dark:bg-[#101713]/92 sm:p-8">
        <div className="grid gap-6 lg:grid-cols-[1.08fr_0.92fr]">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">
              Адрес не найден
            </p>
            <h1 className="mt-2 font-display text-[clamp(2rem,5vw,3.2rem)] font-semibold leading-[0.96] tracking-[-0.04em] text-slate-950 dark:text-slate-50">
              Такой страницы в кабинете нет
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-600 dark:text-slate-300">
              Возможно, ссылка устарела или в адрес попал лишний символ. Начните с главной кабинета, а если ссылка пришла от нас и все равно не открывается, напишите в поддержку.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <AppRouteLink href="/dashboard/" className="btn-primary rounded-full px-5 py-3 text-sm font-semibold">
                Главная
              </AppRouteLink>
              <AppRouteLink href="/support/" className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
                Поддержка
              </AppRouteLink>
            </div>
          </div>

          <aside className="rounded-[1.6rem] border border-slate-200/80 bg-slate-50/90 p-5 dark:border-white/10 dark:bg-white/[0.04]">
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">
              Рабочие разделы
            </p>
            <div className="mt-4 grid gap-3">
              {[
                { href: "/dashboard/", label: "Главная", body: "Статус, срок и быстрые действия." },
                { href: "/subscription/", label: "Тарифы и оплата", body: "Продление и ключи доступа." },
                { href: "/support/", label: "Поддержка", body: "Один кейс на весь вопрос." },
              ].map((item) => (
                <AppRouteLink
                  key={item.href}
                  href={item.href}
                  className="block rounded-[1.2rem] border border-slate-200/80 bg-white/85 px-4 py-4 dark:border-white/10 dark:bg-white/[0.04]"
                >
                  <span className="block text-sm font-semibold text-slate-950 dark:text-slate-50">{item.label}</span>
                  <span className="mt-1 block text-sm leading-6 text-slate-600 dark:text-slate-300">{item.body}</span>
                </AppRouteLink>
              ))}
            </div>
          </aside>
        </div>
      </section>
    </main>
  );
}
