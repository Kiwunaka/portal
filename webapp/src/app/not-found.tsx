import { CabinetBoundary } from "@/components/cabinet-boundary";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <CabinetBoundary
      kind="not-found"
      title="Страница не найдена"
      description="Похоже, этот адрес не относится к активным страницам кабинета. Вернитесь в рабочую зону или откройте поддержку."
      actions={
        <>
          <Button href="/dashboard/">В кабинет</Button>
          <Button href="/support/" variant="secondary">В поддержку</Button>
        </>
      }
    />
  );
}
