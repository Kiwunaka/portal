"use client";

import { useEffect } from "react";

import { CabinetBoundary } from "@/components/cabinet-boundary";
import { Button } from "@/components/ui/button";

type ErrorProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function DashboardError({ error, reset }: ErrorProps) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <CabinetBoundary
      kind="error"
      title="Кабинет не открыл эту страницу"
      description="Повторная загрузка часто восстанавливает раздел. Если ошибка повторяется, откройте главную кабинета."
      actions={
        <>
          <Button onClick={reset}>Повторить</Button>
          <Button href="/dashboard/" variant="secondary">На главную кабинета</Button>
        </>
      }
    />
  );
}
