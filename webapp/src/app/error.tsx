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
      eyebrow="root recovery"
      title="Кабинет столкнулся с ошибкой"
      description="Это редкий сбой оболочки кабинета. Обычно помогает повторить попытку или открыть поддержку."
      badgeLabel={error.digest ? `digest ${error.digest.slice(0, 8)}` : "runtime error"}
      badgeTone="danger"
      primaryAction={{ label: "Повторить", onClick: reset }}
      secondaryAction={{ label: "Открыть кабинет", href: "/dashboard/" }}
      metrics={[
        { label: "Состояние", value: "ошибка", hint: "Оболочка не смогла собрать экран.", tone: "rose" },
        { label: "Маршрут", value: "root", hint: "Сбой произошёл на верхнем уровне приложения." },
      ]}
      steps={[
        { title: "Повторите попытку", description: "После повторного рендера Next вернёт вас в рабочий маршрут.", tone: "info" },
        { title: "Откройте кабинет заново", description: "Если ошибка осталась, начните с чистого входа в личный кабинет.", tone: "warning" },
        { title: "Напишите в поддержку", description: "Команда увидит ситуацию и поможет восстановить доступ.", tone: "success" },
      ]}
      icon="error_outline"
    />
  );
}
