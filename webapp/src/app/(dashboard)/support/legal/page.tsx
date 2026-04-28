"use client";

import AppRouteLink from "@/components/app-route-link";
import { CabinetCardGrid, CabinetHero, CabinetRoute, CabinetSection } from "@/components/cabinet/surface";
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
    <CabinetRoute
      eyebrow="Документы"
      title="Юридическая информация"
      description="Актуальные публичные документы POKROV: оферта и политика конфиденциальности. Кабинет только ведет к ним, не дублируя отдельную версию текста."
      actions={
        <AppRouteLink href="/support/" className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
          Назад в поддержку
        </AppRouteLink>
      }
      metrics={[
        {
          label: "Оферта",
          value: "Публичный документ",
          hint: "Условия доступа, оплаты, продления и ответственности сторон.",
          tone: "neutral",
        },
        {
          label: "Конфиденциальность",
          value: "Публичный документ",
          hint: "Как используются данные аккаунта, оплаты и поддержки.",
          tone: "neutral",
        },
        {
          label: "Где открывается",
          value: "pokrov.space",
          hint: "Юридические документы живут на публичной поверхности.",
          tone: "neutral",
        },
        {
          label: "Если есть вопрос",
          value: "Один кейс",
          hint: "Поддержка быстрее передаст запрос нужному специалисту.",
          tone: "info",
        },
      ]}
    >
      <CabinetHero
        eyebrow="Коротко"
        badge="Документы на публичном сайте"
        badgeTone="info"
        title="Откройте нужный документ или вернитесь в поддержку"
        description="Если вопрос касается оплаты, условий или данных аккаунта, создайте обращение в кабинете и укажите тему. Так запрос не потеряется."
        actions={
          <>
            <a href={offerUrl} target="_blank" rel="noreferrer" className="btn-primary rounded-full px-5 py-3 text-sm font-semibold">
              Открыть оферту
            </a>
            <a href={privacyUrl} target="_blank" rel="noreferrer" className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
              Открыть политику
            </a>
          </>
        }
        details={[
          {
            label: "Оплата и продление",
            value: "Оферта",
            hint: "Начните с нее, если вопрос финансовый.",
            tone: "neutral",
          },
          {
            label: "Данные аккаунта",
            value: "Политика",
            hint: "Там описана работа с данными.",
            tone: "neutral",
          },
          {
            label: "Спорный случай",
            value: "Поддержка",
            hint: "Лучше открыть один кейс с коротким описанием.",
            tone: "info",
          },
        ]}
      />

      <CabinetSection
        eyebrow="Документы"
        title="Что можно открыть"
        description="Обе ссылки ведут на публичную поверхность POKROV."
      >
        <CabinetCardGrid
          items={[
            {
              key: "offer",
              title: "Публичная оферта",
              body: "Условия предоставления доступа, оплаты, продления и ответственности сторон.",
              badge: "Оферта",
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
            {
              key: "support",
              title: "Вопрос по документам",
              body: "Создайте обращение и укажите, какой документ или платежный случай нужно проверить.",
              badge: "Кейс",
              tone: "info",
              action: (
                <AppRouteLink href="/support/" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
                  Поддержка
                </AppRouteLink>
              ),
            },
          ]}
        />
      </CabinetSection>
    </CabinetRoute>
  );
}
