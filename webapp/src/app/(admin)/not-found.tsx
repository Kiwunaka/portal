import { Button } from "@/components/cabinet/ui";
import { CabinetIcon } from "@/components/cabinet/icon";
import { EmptyState, Timeline } from "@/components/shell-primitives";

export default function AdminNotFound() {
  return (
    <main className="relative mx-auto flex min-h-[calc(100vh-2rem)] w-[min(96vw,1060px)] items-center justify-center px-4 py-8 sm:px-6 lg:py-10">
      <section className="glass-card w-full overflow-hidden p-6 sm:p-8">
        <EmptyState
          icon={<CabinetIcon name="admin_panel_settings" className="h-8 w-8" />}
          title="Раздел админки не найден"
          description="Такого операторского экрана нет в текущей админке POKROV. Вернитесь к сводке или проверьте ссылку."
          actions={
            <>
              <Button href="/admin/dashboard">К сводке</Button>
              <Button href="/dashboard/" variant="secondary">В кабинет</Button>
            </>
          }
        />

        <div className="mt-6 rounded-[1.5rem] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] p-5">
          <Timeline
            items={[
              { title: "Откройте рабочий стол", description: "Сводка смены показывает тревоги, очереди и свежесть данных.", tone: "success" },
              { title: "Проверьте ссылку", description: "Если вы пришли по старой закладке, маршрут мог измениться.", tone: "warning" },
              { title: "Вернитесь в кабинет", description: "Кабинет остается отдельным пользовательским маршрутом.", tone: "info" },
            ]}
          />
        </div>
      </section>
    </main>
  );
}
