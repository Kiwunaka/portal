"use client";

import { useEffect } from "react";

import { CabinetBoundary } from "@/components/cabinet-boundary";
import { Button } from "@/components/ui/button";

type ErrorProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function RootError({ error, reset }: ErrorProps) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <CabinetBoundary
      kind="error"
      title="Кабинет не открыл страницу"
      description="Это обычно временная проблема. Повторите попытку или откройте главную кабинета — данные аккаунта не теряются."
      actions={
        <>
          <Button onClick={reset}>Повторить</Button>
          <Button href="/dashboard/" variant="secondary">Открыть кабинет</Button>
        </>
      }
    />
  );
}
