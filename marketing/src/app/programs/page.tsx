import JsonLd from "../../components/json-ld";
import { PageShell } from "../../components/layout/page-shell";
import { Button } from "../../components/ui/button";
import { Card } from "../../components/ui/card";
import { buildBreadcrumbJsonLd, buildMarketingMetadata } from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND, CANONICAL_WEBAPP_URL } from "../../lib/pokrov";

export const metadata = buildMarketingMetadata(
  "Программы POKROV | Переход, исследования и команды",
  "Ручная проверка предложений при переходе от другого VPN, полезных исследований и запросов для команд.",
  { path: "/programs/" },
);

const programs = [
  {
    title: "Переход от другого VPN",
    state: "Заявки открыты",
    body: "Расскажите, каким сервисом пользуетесь сейчас и что мешает перейти. Условия определяются после проверки — автоматического бонуса за одно название нет.",
  },
  {
    title: "Исследования и баг-репорты",
    state: "Заявки открыты",
    body: "Нужны приватные интервью и воспроизводимые отчёты, которые реально улучшают продукт. За подтверждённый вклад оператор может начислить 1, 3 или 7 дней.",
  },
  {
    title: "POKROV для команды",
    state: "2–50 устройств",
    body: "Опишите размер команды и задачу. Мы подготовим предложение вручную; форма не подключает автоплатёж и не меняет текущий доступ.",
  },
  {
    title: "Партнёрская программа",
    state: "Пока закрыта",
    body: "Технический фундамент предусмотрен, но заявки, кабинеты и начисления не включены. Мы не изображаем работающую программу до готовности учёта и выплат.",
  },
] as const;

export default function ProgramsPage() {
  return (
    <PageShell>
      <JsonLd
        data={buildBreadcrumbJsonLd([
          { name: CANONICAL_PLATFORM_BRAND, path: "/" },
          { name: "Программы", path: "/programs/" },
        ])}
      />
      <section className="mx-auto flex max-w-5xl flex-col gap-4 px-4 pt-12 pb-10 sm:px-6 sm:pt-16">
        <span className="text-[0.8125rem] font-semibold tracking-[0.08em] text-brand uppercase">Ручная проверка · без автосписаний</span>
        <h1 className="font-display text-[2.25rem] leading-[1.1] font-extrabold tracking-[-0.01em] text-ink">
          Перейти, помочь исследованию или подключить команду
        </h1>
        <p className="max-w-3xl text-base leading-relaxed text-ink-soft">
          Заявка ничего не начисляет автоматически. Решение и возможная награда появляются только после проверки в
          личном кабинете. Оценка в магазине всегда добровольна и никогда не оплачивается.
        </p>
      </section>

      <section className="mx-auto grid max-w-5xl gap-4 px-4 pb-10 sm:px-6 lg:grid-cols-2">
        {programs.map((program) => (
          <Card key={program.title} className="flex flex-col gap-3">
            <span className="text-xs font-semibold tracking-[0.08em] text-brand uppercase">{program.state}</span>
            <h2 className="font-display text-xl font-bold text-ink">{program.title}</h2>
            <p className="text-[0.9375rem] leading-relaxed text-ink-soft">{program.body}</p>
          </Card>
        ))}
      </section>

      <section className="mx-auto flex max-w-5xl flex-col gap-4 px-4 pb-16 sm:px-6">
        <Card className="border-line bg-canvas-alt">
          <h2 className="font-display text-lg font-bold text-ink">Что нельзя отправлять</h2>
          <p className="mt-2 text-sm leading-relaxed text-ink-soft">
            Не прикладывайте пароли, платёжные данные, приватные ключи, полные VPN-конфиги и чужие персональные данные.
            Для технической диагностики поддержка отдельно запросит только безопасный минимум.
          </p>
        </Card>
        <div className="flex flex-col gap-2 sm:flex-row">
          <Button href={`${CANONICAL_WEBAPP_URL.replace(/\/$/, "")}/programs/`} target="_blank" rel="noopener noreferrer" className="w-full sm:w-auto">
            Открыть заявки в кабинете
          </Button>
          <Button href="/guides/" variant="secondary" className="w-full sm:w-auto">Как работает POKROV</Button>
        </div>
      </section>
    </PageShell>
  );
}
