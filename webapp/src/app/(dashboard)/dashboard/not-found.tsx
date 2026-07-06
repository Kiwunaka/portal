import { CabinetBoundary } from "@/components/cabinet-boundary";
import { Button } from "@/components/ui/button";

export default function DashboardNotFound() {
  return (
    <CabinetBoundary
      kind="not-found"
      title="Страница кабинета не найдена"
      description="Проверьте адрес или вернитесь на главную кабинета — активные разделы доступны из навигации."
      actions={
        <>
          <Button href="/dashboard/">На главную кабинета</Button>
          <Button href="/support/" variant="secondary">В поддержку</Button>
        </>
      }
    />
  );
}
