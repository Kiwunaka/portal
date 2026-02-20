"use client";

import { AnimatePresence, motion } from "framer-motion";
import Link from "next/link";
import { useState } from "react";

function downloadMockPdf(name: string, title: string): void {
  const body = `%PDF-1.1
1 0 obj
<<>>
endobj
2 0 obj
<< /Length 58 >>
stream
BT /F1 18 Tf 72 720 Td (${title}) Tj ET
endstream
endobj
trailer
<<>>
%%EOF`;
  const blob = new Blob([body], { type: "application/pdf" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export default function SupportLegalPage() {
  const [toast, setToast] = useState<string | null>(null);

  const onDownload = (fileName: string, title: string): void => {
    downloadMockPdf(fileName, title);
    setToast(`Документ "${fileName}" скачан.`);
    window.setTimeout(() => setToast(null), 1800);
  };

  return (
    <main className="space-y-6">
      <section className="glass-card p-7">
        <Link href="/support" className="inline-flex items-center gap-2 text-xs uppercase tracking-[0.16em] text-slate-500">
          <span className="material-symbols-rounded">arrow_back</span>
          назад в поддержку
        </Link>
        <h1 className="mt-3 font-display text-4xl font-bold">Юридическая информация</h1>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
          Публичная оферта и политика конфиденциальности в актуальной редакции.
        </p>
      </section>

      <section className="grid gap-5 lg:grid-cols-2">
        <article className="glass-card p-6">
          <h2 className="font-display text-2xl font-semibold">Публичная оферта</h2>
          <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
            Документ определяет условия предоставления цифрового сервиса PORTAL, оплаты и ответственности сторон.
            Сервис предоставляется по модели best-effort.
          </p>
          <button
            type="button"
            onClick={() => onDownload("portal-offer.pdf", "PORTAL Public Offer")}
            className="btn-primary mt-5 rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em]"
          >
            Скачать PDF
          </button>
        </article>

        <article className="glass-card p-6">
          <h2 className="font-display text-2xl font-semibold">Политика конфиденциальности</h2>
          <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
            Мы придерживаемся принципа минимизации данных и обрабатываем только то, что нужно для аккаунта, оплаты и поддержки.
          </p>
          <button
            type="button"
            onClick={() => onDownload("portal-privacy.pdf", "PORTAL Privacy Policy")}
            className="outline-btn mt-5 rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em]"
          >
            Скачать PDF
          </button>
        </article>
      </section>

      <section className="glass-card p-6">
        <p className="font-mono text-xs uppercase tracking-[0.16em] text-slate-500">preview</p>
        <h3 className="mt-2 font-display text-2xl font-semibold">Редакция от 15.02.2026</h3>
        <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
          1. Общие положения: сервис определяет порядок предоставления цифрового доступа.
          2. Предмет: доступ предоставляется на выбранный период после подтверждения оплаты.
          3. Оплата: перед подтверждением пользователь видит тариф, период и примененные скидки.
          4. Ограничения: внешние сетевые и регуляторные условия относятся к зонам вне контроля сервиса.
        </p>
      </section>

      <AnimatePresence>
        {toast ? (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 12 }}
            className="fixed bottom-24 left-1/2 z-[220] -translate-x-1/2 rounded-full bg-slate-900 px-4 py-2 text-xs text-white shadow-xl"
          >
            {toast}
          </motion.div>
        ) : null}
      </AnimatePresence>
    </main>
  );
}
