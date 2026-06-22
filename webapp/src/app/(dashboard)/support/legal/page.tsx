"use client";

import { icon } from "@/components/cabinet/icon";
import { CabinetGroup, CabinetRow, CabinetStatus } from "@/components/cabinet/surface";
import { Button } from "@/components/cabinet/ui";
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

export default function SupportLegalPage() {
  const offerUrl = marketingDocumentUrl("/offer/");
  const privacyUrl = marketingDocumentUrl("/privacy/");

  return (
    <main className="cab-page">
      <CabinetStatus
        title="Документы"
        meta="pokrov.space"
        body="Оферта и политика открываются на публичном сайте. В кабинете оставляем только быстрые входы и поддержку."
        tone="neutral"
        action={
          <Button variant="secondary" href="/support/" className="w-full sm:w-auto">
            В поддержку
          </Button>
        }
      />

      <CabinetGroup title="Ссылки">
        <CabinetRow
          icon={icon("contract")}
          label="Оферта"
          hint="Условия доступа, оплаты и продления"
          value="pokrov.space"
          action={
            <a href={offerUrl} target="_blank" rel="noreferrer" className="cab-link">
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
            <a href={privacyUrl} target="_blank" rel="noreferrer" className="cab-link">
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
