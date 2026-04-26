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
      title="Дашборд не смог открыть этот экран"
      description="Сбой внутри кабинета обычно лечится повтором запроса. Если нет, вернитесь на старт и попробуйте снова."
      badgeLabel={error.digest ? `digest ${error.digest.slice(0, 8)}` : "dashboard error"}
      badgeTone="warning"
      primaryAction={{ label: "Повторить", onClick: reset }}
      secondaryAction={{ label: "В дашборд", href: "/dashboard/" }}
      metrics={[
        { label: "Область", value: "/dashboard", hint: "Ошибка произошла в основном кабинете." },
        { label: "Поведение", value: "retry", hint: "Повторный рендер часто восстанавливает страницу." },
      ]}
      steps={[
        { title: "Повторите попытку", description: "Эта кнопка попросит Next заново собрать экран.", tone: "info" },
        { title: "Откройте дашборд", description: "Если конкретный путь сломался, возвращение в начало безопаснее.", tone: "warning" },
        { title: "Свяжитесь с поддержкой", description: "Так мы быстрее найдём маршрут, который не открывается.", tone: "success" },
      ]}
      icon="report_problem"
    />
  );
}
