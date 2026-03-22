import { CANONICAL_MARKETING_SITE_URL } from "@/lib/portal";
import Link from "next/link";

function marketingDocumentUrl(pathname: "/offer/" | "/privacy/"): string {
  const marketingSiteUrl = String(CANONICAL_MARKETING_SITE_URL || "").trim();
  if (marketingSiteUrl) {
    try {
      const url = new URL(marketingSiteUrl);
      url.pathname = pathname;
      url.search = "";
      url.hash = "";
      return url.toString();
    } catch {
      // Fall through to domain fallback below.
    }
  }
  return `${CANONICAL_MARKETING_SITE_URL}${pathname}`;
}

export default function SupportLegalPage() {
  const offerUrl = marketingDocumentUrl("/offer/");
  const privacyUrl = marketingDocumentUrl("/privacy/");

  return (
    <main className="space-y-6">
      <section className="glass-card p-7">
        <Link href="/support" className="inline-flex items-center gap-2 text-xs uppercase tracking-[0.16em] text-slate-500">
          <span className="material-symbols-rounded">arrow_back</span>
          назад в поддержку
        </Link>
        <h1 className="mt-3 font-display text-4xl font-bold">Юридическая информация</h1>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
          Ниже находятся актуальные публичные документы POKROV: оферта и политика конфиденциальности.
        </p>
      </section>

      <section className="grid gap-5 lg:grid-cols-2">
        <article className="glass-card p-6">
          <h2 className="font-display text-2xl font-semibold">Публичная оферта</h2>
          <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
            Документ описывает условия предоставления доступа, оплаты, продления и ответственности сторон.
          </p>
          <a
            href={offerUrl}
            target="_blank"
            rel="noreferrer"
            className="btn-primary mt-5 inline-flex rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em]"
          >
            Открыть оферту
          </a>
        </article>

        <article className="glass-card p-6">
          <h2 className="font-display text-2xl font-semibold">Политика конфиденциальности</h2>
          <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
            Документ описывает, какие данные используются для работы аккаунта, оплаты и поддержки.
          </p>
          <a
            href={privacyUrl}
            target="_blank"
            rel="noreferrer"
            className="outline-btn mt-5 inline-flex rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em]"
          >
            Открыть политику
          </a>
        </article>
      </section>

      <section className="glass-card p-6">
        <p className="font-mono text-xs uppercase tracking-[0.16em] text-slate-500">Важно</p>
        <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
          Если у вас есть юридический или финансовый вопрос по оплате, создайте тикет в поддержке и укажите тему обращения.
          Так запрос быстрее попадёт к нужному специалисту.
        </p>
      </section>
    </main>
  );
}
