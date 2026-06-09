"use client";

import { useEffect } from "react";

import { ShellBoundary } from "@/components/shell-boundary";

type ErrorProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function DashboardRouteError({ error, reset }: ErrorProps) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <ShellBoundary
      eyebrow="dashboard recovery"
      title="Кабинет не открыл эту страницу"
      description="Сбой внутри кабинета обычно лечится повтором запроса. Если нет, вернитесь на старт и попробуйте снова."
      badgeLabel={error.digest ? `digest ${error.digest.slice(0, 8)}` : "dashboard error"}
      badgeTone="warning"
      primaryAction={{ label: "Повторить", onClick: reset }}
      secondaryAction={{ label: "На главную кабинета", href: "/dashboard/" }}
      metrics={[
        { label: "Область", value: "/dashboard", hint: "Ошибка произошла в основном кабинете." },
        { label: "Поведение", value: "повтор", hint: "Повторная загрузка часто восстанавливает страницу." },
      ]}
      steps={[
        { title: "Повторите попытку", description: "Эта кнопка заново загрузит страницу.", tone: "info" },
        { title: "Откройте главную кабинета", description: "Если конкретный путь сломался, возвращение в начало безопаснее.", tone: "warning" },
        { title: "Свяжитесь с поддержкой", description: "Так мы быстрее найдём экран или действие, которое не открывается.", tone: "success" },
      ]}
      icon="report_problem"
    />
  );
}
