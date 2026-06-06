"use client";

import AppRouteLink from "@/components/app-route-link";
import { CabinetGroup, CabinetRow, CabinetStatus } from "@/components/cabinet/surface";
import { CANONICAL_MARKETING_SITE_URL } from "@/lib/portal";

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

function icon(name: string) {
  return <span className="material-symbols-rounded text-[20px]">{name}</span>;
}

export default function SupportLegalPage() {
  const offerUrl = marketingDocumentUrl("/offer/");
  const privacyUrl = marketingDocumentUrl("/privacy/");

  return (
    <main className="mx-auto w-full max-w-[840px] space-y-5">
      <CabinetStatus
        title="Документы"
        meta="pokrov.space"
        body="Оферта и политика открываются на публичном сайте. В кабинете оставляем только быстрые входы и поддержку."
        tone="neutral"
        action={
          <AppRouteLink href="/support/" className="outline-btn w-full rounded-full px-5 py-3 text-center text-sm font-semibold sm:w-auto">
            В поддержку
          </AppRouteLink>
        }
      />

      <CabinetGroup title="Ссылки">
        <CabinetRow
          icon={icon("contract")}
          label="Оферта"
          hint="Условия доступа, оплаты и продления"
          value="pokrov.space"
          action={
            <a href={offerUrl} target="_blank" rel="noreferrer" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
              Открыть
            </a>
          }
        />
        <CabinetRow
          icon={icon("privacy_tip")}
          label="Политика"
          hint="Данные аккаунта, оплаты и поддержки"
          value="pokrov.space"
          action={
            <a href={privacyUrl} target="_blank" rel="noreferrer" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
              Открыть
            </a>
          }
        />
      </CabinetGroup>

      <CabinetGroup title="Вопрос по документам">
        <CabinetRow icon={icon("support_agent")} label="Написать в поддержку" hint="Укажите документ или платежный случай" href="/support/" />
        <CabinetRow icon={icon("payments")} label="Оплата и доступ" hint="Вернуться к продлению" href="/subscription/" />
      </CabinetGroup>
    </main>
  );
}
