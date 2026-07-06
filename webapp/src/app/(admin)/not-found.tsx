import { Wrench } from "lucide-react";

import { CabinetBoundary } from "@/components/cabinet-boundary";
import { Button } from "@/components/ui/button";

export default function AdminNotFound() {
  return (
    <CabinetBoundary
      kind="not-found"
      icon={Wrench}
      title="Раздел админки не найден"
      description="Такого операторского раздела нет. Вернитесь к сводке или в пользовательский кабинет."
      actions={
        <>
          <Button href="/admin/dashboard">К сводке</Button>
          <Button href="/dashboard/" variant="secondary">В кабинет</Button>
        </>
      }
    />
  );
}
