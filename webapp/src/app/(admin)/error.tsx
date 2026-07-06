"use client";

import { useEffect } from "react";

import { CabinetBoundary } from "@/components/cabinet-boundary";
import { Button } from "@/components/ui/button";

type ErrorProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function AdminError({ error, reset }: ErrorProps) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <CabinetBoundary
      kind="error"
      title="Админка не смогла открыть этот экран"
      description="Повторный запрос часто возвращает экран без полного выхода. Если ошибка повторяется, вернитесь к сводке."
      actions={
        <>
          <Button onClick={reset}>Повторить</Button>
          <Button href="/admin/dashboard" variant="secondary">К сводке</Button>
        </>
      }
    />
  );
}
