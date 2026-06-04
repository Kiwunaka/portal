"use client";

import { useEffect } from "react";

import { ShellBoundary } from "@/components/shell-boundary";

type ErrorProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function AdminError({ error, reset }: ErrorProps) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <ShellBoundary
      eyebrow="восстановление админки"
      title="Админка не смогла открыть этот экран"
      description="Это сбой операторского экрана или временная проблема данных. Можно повторить запрос или вернуться к сводке смены."
      badgeLabel={error.digest ? `ошибка ${error.digest.slice(0, 8)}` : "ошибка админки"}
      badgeTone="warning"
      primaryAction={{ label: "Повторить", onClick: reset }}
      secondaryAction={{ label: "К сводке", href: "/admin/dashboard" }}
      metrics={[
        { label: "Область", value: "админка", hint: "Проблема возникла внутри операторского интерфейса." },
        { label: "Действие", value: "повторить", hint: "Повторный запрос часто возвращает экран без полного выхода." },
      ]}
      steps={[
        { title: "Повторите запрос", description: "Это пересоберет текущий экран без смены аккаунта.", tone: "info" },
        { title: "Откройте сводку", description: "Если раздел сломан, сводка смены остается безопасной стартовой точкой.", tone: "warning" },
        { title: "Не меняйте данные вслепую", description: "Если сбой повторяется, проверьте API и логи перед ручными действиями.", tone: "success" },
      ]}
      icon="admin_panel_settings"
    />
  );
}
