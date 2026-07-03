import { Button } from "@/components/cabinet/ui";
import { CabinetIcon } from "@/components/cabinet/icon";
import { EmptyState, Timeline } from "@/components/shell-primitives";

export default function NotFound() {
  return (
    <main className="relative mx-auto flex min-h-[calc(100vh-2rem)] w-[min(96vw,1060px)] items-center justify-center px-4 py-8 sm:px-6 lg:py-10">
      <section className="glass-card w-full overflow-hidden p-6 sm:p-8">
        <EmptyState
          icon={<CabinetIcon name="travel_explore" className="h-8 w-8" />}
          title="Страница не найдена"
          description="Похоже, этот адрес не относится к активным страницам кабинета. Вернитесь в рабочую зону или откройте поддержку."
          actions={
            <>
              <Button href="/dashboard/">В кабинет</Button>
              <Button href="/support/" variant="secondary">В поддержку</Button>
            </>
          }
        />

        <div className="mt-6 rounded-[1.5rem] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] p-5">
          <Timeline
            items={[
              { title: "Проверьте адрес", description: "Иногда проблема только в лишнем символе или устаревшей закладке.", tone: "info" },
              { title: "Откройте кабинет", description: "Главная страница доступна на /dashboard/.", tone: "success" },
              { title: "Попросите помощь", description: "Если ссылка пришла извне, поддержку можно открыть сразу отсюда.", tone: "warning" },
            ]}
          />
        </div>
      </section>
    </main>
  );
}
