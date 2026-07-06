"use client";

import { useEffect } from "react";

import { CabinetBoundary } from "@/components/cabinet-boundary";
import { Button } from "@/components/ui/button";

type ErrorProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function DashboardGroupError({ error, reset }: ErrorProps) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <CabinetBoundary
      kind="error"
      title="Кабинет не смог открыть этот раздел"
      description="Это обычно временная проблема сети или данных. Повторите попытку или вернитесь на главную кабинета."
      actions={
        <>
          <Button onClick={reset}>Повторить</Button>
          <Button href="/dashboard/" variant="secondary">В кабинет</Button>
        </>
      }
    />
  );
}
