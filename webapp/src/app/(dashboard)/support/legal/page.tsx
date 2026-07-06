"use client";

import { CreditCard, FileText, LifeBuoy, ShieldQuestion } from "lucide-react";

import { StatusHero } from "@/components/cabinet/status-hero";
import { Button } from "@/components/ui/button";
import { GroupedSection, Row } from "@/components/ui/grouped";
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

const LINK_CLASS = "text-sm font-semibold text-brand hover:text-brand-strong";

export default function SupportLegalPage() {
  const offerUrl = marketingDocumentUrl("/offer/");
  const privacyUrl = marketingDocumentUrl("/privacy/");

  return (
    <main className="mx-auto flex w-full max-w-[860px] flex-col gap-5">
      <StatusHero
        title="Документы"
        meta="pokrov.space"
        body="Оферта и политика открываются на публичном сайте. В кабинете оставляем только быстрые входы и поддержку."
        tone="neutral"
        icon={FileText}
        action={
          <Button variant="secondary" href="/support/" className="w-full sm:w-auto">
            В поддержку
          </Button>
        }
      />

      <GroupedSection title="Ссылки">
        <Row
          icon={FileText}
          label="Оферта"
          hint="Условия доступа, оплаты и продления"
          value="pokrov.space"
          action={
            <a href={offerUrl} target="_blank" rel="noreferrer" className={LINK_CLASS}>
              Открыть
            </a>
          }
        />
        <Row
          icon={ShieldQuestion}
          label="Политика"
          hint="Данные аккаунта, оплаты и поддержки"
          value="pokrov.space"
          action={
            <a href={privacyUrl} target="_blank" rel="noreferrer" className={LINK_CLASS}>
              Открыть
            </a>
          }
        />
      </GroupedSection>

      <GroupedSection title="Вопрос по документам">
        <Row icon={LifeBuoy} label="Написать в поддержку" hint="Укажите документ или платежный случай" href="/support/" />
        <Row icon={CreditCard} label="Оплата и доступ" hint="Вернуться к продлению" href="/subscription/" />
      </GroupedSection>
    </main>
  );
}
