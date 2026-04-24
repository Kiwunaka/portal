"use client";

import { useEffect } from "react";

import { ShellBoundary } from "@/components/shell-boundary";

type ErrorProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function DashboardError({ error, reset }: ErrorProps) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <ShellBoundary
      eyebrow="cabinet recovery"
      title="Кабинет не смог открыть этот экран"
      description="Это временная проблема экрана или данных. Можно повторить запрос или вернуться в безопасную точку входа."
      badgeLabel="ошибка экрана"
      badgeTone="warning"
      primaryAction={{ label: "Повторить", onClick: reset }}
      secondaryAction={{ label: "В кабинет", href: "/dashboard/" }}
      metrics={[
        { label: "Область", value: "Кабинет", hint: "Проблема возникла внутри пользовательского кабинета." },
        { label: "Следующий шаг", value: "Повторить", hint: "Повторный запрос часто возвращает страницу сразу." },
      ]}
      steps={[
        { title: "Нажмите повтор", description: "Это быстро пересоберёт страницу без полного выхода из кабинета.", tone: "info" },
        { title: "Вернитесь на дашборд", description: "Если текущий маршрут сломан, стартовая точка безопаснее всего.", tone: "warning" },
        { title: "Откройте поддержку", description: "Пришлите скрин и опишите, на каком экране остановилось открытие.", tone: "success" },
      ]}
      icon="report_problem"
    />
  );
}
