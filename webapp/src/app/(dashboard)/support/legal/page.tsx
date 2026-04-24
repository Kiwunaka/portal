import AppRouteLink from "@/components/app-route-link";
import { CabinetCardGrid, CabinetRoute, CabinetSection } from "@/components/cabinet/surface";
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
      return `${CANONICAL_MARKETING_SITE_URL}${pathname}`;
    }
  }
  return pathname;
}

export default function SupportLegalPage() {
  const offerUrl = marketingDocumentUrl("/offer/");
  const privacyUrl = marketingDocumentUrl("/privacy/");

  return (
    <CabinetRoute
      eyebrow="Поддержка"
      title="Документы и условия"
      description="Здесь собраны публичная оферта и политика конфиденциальности. Ссылки открываются отдельно, а вернуться в поддержку можно в один шаг."
      actions={
        <AppRouteLink href="/support/" className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
          К поддержке
        </AppRouteLink>
      }
    >
      <CabinetSection eyebrow="Документы" title="Открыть нужный документ" description="Мы не показываем технические адреса на первом экране: просто выберите документ по смыслу.">
        <CabinetCardGrid
          items={[
            {
              key: "offer",
              title: "Публичная оферта",
              body: "Условия предоставления доступа, оплаты, продления и ответственности сторон.",
              badge: "Условия",
              tone: "neutral",
              action: (
                <a href={offerUrl} target="_blank" rel="noreferrer" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
                  Открыть
                </a>
              ),
            },
            {
              key: "privacy",
              title: "Политика конфиденциальности",
              body: "Какие данные используются для работы аккаунта, оплаты и поддержки.",
              badge: "Данные",
              tone: "neutral",
              action: (
                <a href={privacyUrl} target="_blank" rel="noreferrer" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
                  Открыть
                </a>
              ),
            },
          ]}
          className="xl:grid-cols-2"
        />
      </CabinetSection>

      <CabinetSection
        eyebrow="Если вопрос не про документ"
        title="Лучше открыть кейс"
        description="Если нужно разобраться с оплатой, доступом или конкретной ситуацией в аккаунте, создайте кейс в поддержке и укажите тему."
      >
        <AppRouteLink href="/support/" className="btn-primary inline-flex rounded-2xl px-5 py-3 text-sm font-semibold">
          Открыть поддержку
        </AppRouteLink>
      </CabinetSection>
    </CabinetRoute>
  );
}
