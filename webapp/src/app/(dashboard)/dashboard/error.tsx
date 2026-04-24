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
      eyebrow="восстановление кабинета"
      title="Главная не смогла открыть этот экран"
      description="Сбой внутри кабинета обычно лечится повтором запроса. Если нет, вернитесь на старт и попробуйте снова."
      badgeLabel={error.digest ? `код ${error.digest.slice(0, 8)}` : "ошибка экрана"}
      badgeTone="warning"
      primaryAction={{ label: "Повторить", onClick: reset }}
      secondaryAction={{ label: "На главную", href: "/dashboard/" }}
      metrics={[
        { label: "Область", value: "Главная", hint: "Ошибка произошла в основном кабинете." },
        { label: "Поведение", value: "Повтор", hint: "Повторный запрос часто восстанавливает страницу." },
      ]}
      steps={[
        { title: "Повторите попытку", description: "Эта кнопка попросит кабинет заново собрать экран.", tone: "info" },
        { title: "Откройте главную", description: "Если конкретный экран не открылся, возвращение в начало безопаснее.", tone: "warning" },
        { title: "Свяжитесь с поддержкой", description: "Так мы быстрее найдём экран, который не открывается.", tone: "success" },
      ]}
      icon="report_problem"
    />
  );
}
