"use client";

import { useEffect } from "react";

import { ShellBoundary } from "@/components/shell-boundary";

type ErrorProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function RootError({ error, reset }: ErrorProps) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <ShellBoundary
      eyebrow="восстановление"
      title="Кабинет не открыл страницу"
      description="Обычно помогает повторить попытку или открыть поддержку."
      badgeLabel={error.digest ? `Код ошибки: ${error.digest.slice(0, 8)}` : "Ошибка интерфейса"}
      badgeTone="danger"
      primaryAction={{ label: "Повторить", onClick: reset }}
      secondaryAction={{ label: "Открыть кабинет", href: "/dashboard/" }}
      metrics={[
        { label: "Состояние", value: "ошибка", hint: "Кабинет не открыл эту страницу.", tone: "rose" },
        { label: "Раздел", value: "кабинет", hint: "Повторите попытку или откройте главную страницу." },
      ]}
      steps={[
        { title: "Повторите попытку", description: "Мы заново загрузим страницу.", tone: "info" },
        { title: "Откройте кабинет заново", description: "Если ошибка осталась, начните с чистого входа в личный кабинет.", tone: "warning" },
        { title: "Напишите в поддержку", description: "Команда увидит ситуацию и поможет восстановить доступ.", tone: "success" },
      ]}
      icon="error_outline"
    />
  );
}
