import { Button } from "@/components/cabinet/ui";
import { CabinetIcon } from "@/components/cabinet/icon";
import { EmptyState, Timeline } from "@/components/shell-primitives";

export default function DashboardRouteNotFound() {
  return (
    <main className="relative mx-auto flex min-h-[calc(100vh-2rem)] w-[min(96vw,1060px)] items-center justify-center px-4 py-8 sm:px-6 lg:py-10">
      <section className="glass-card w-full overflow-hidden p-6 sm:p-8">
        <EmptyState
          icon={<CabinetIcon name="explore_off" className="h-8 w-8" />}
          title="Страница кабинета не найдена"
          description="Такой путь не существует внутри главного кабинета. Вернитесь на старт или откройте поддержку, если пришли по старой ссылке."
          actions={
            <>
              <Button href="/dashboard/">На главную кабинета</Button>
              <Button href="/support/" variant="secondary">В поддержку</Button>
            </>
          }
        />

        <div className="mt-6 rounded-[1.5rem] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] p-5">
          <Timeline
            items={[
              { title: "Откройте главную кабинета", description: "Главная страница показывает активный доступ, срок и быстрые действия.", tone: "success" },
              { title: "Проверьте путь", description: "Возможно, ссылка в закладке устарела после обновления кабинета.", tone: "warning" },
              { title: "Попросите помощь", description: "Если экран нужен срочно, поддержка подскажет точную ссылку.", tone: "info" },
            ]}
          />
        </div>
      </section>
    </main>
  );
}
