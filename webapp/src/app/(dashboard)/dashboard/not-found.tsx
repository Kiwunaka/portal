import AppRouteLink from "@/components/app-route-link";
import { EmptyState, Timeline } from "@/components/shell-primitives";

export default function DashboardRouteNotFound() {
  return (
    <main className="relative mx-auto flex min-h-[calc(100vh-2rem)] w-[min(96vw,1060px)] items-center justify-center px-4 py-8 sm:px-6 lg:py-10">
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top_left,_rgba(11,72,50,0.12),_transparent_34%),radial-gradient(circle_at_bottom_right,_rgba(197,138,42,0.1),_transparent_30%)]" />
      <section className="glass-card w-full overflow-hidden border border-white/70 p-6 dark:border-[#243129]/80 sm:p-8">
        <EmptyState
          icon={<span className="material-symbols-rounded text-3xl">explore_off</span>}
          title="Маршрут дашборда не найден"
          description="Такой путь не существует внутри главного кабинета. Вернитесь на старт или откройте поддержку, если пришли по старой ссылке."
          actions={
            <>
              <AppRouteLink href="/dashboard/" className="btn-primary rounded-2xl px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em]">
                В дашборд
              </AppRouteLink>
              <AppRouteLink href="/support/" className="outline-btn rounded-2xl px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em]">
                В поддержку
              </AppRouteLink>
            </>
          }
        />

        <div className="mt-6 rounded-[1.5rem] border border-white/70 bg-white/62 p-5 dark:border-white/10 dark:bg-white/[0.04]">
          <Timeline
            items={[
              { title: "Откройте дашборд", description: "Главная страница показывает активный доступ, срок и быстрые действия.", tone: "success" },
              { title: "Проверьте путь", description: "Возможно, ссылка в закладке устарела после обновления кабинета.", tone: "warning" },
              { title: "Попросите помощь", description: "Если экран нужен срочно, поддержка подскажет точный маршрут.", tone: "info" },
            ]}
          />
        </div>
      </section>
    </main>
  );
}
