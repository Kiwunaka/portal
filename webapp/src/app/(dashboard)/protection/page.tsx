"use client";

import {
  Activity,
  AppWindow,
  Network,
  ExternalLink,
  Globe2,
  RefreshCcw,
  Route,
  ShieldCheck,
  TriangleAlert,
} from "lucide-react";

import { StatusHero } from "@/components/cabinet/status-hero";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { GroupedSection, Row } from "@/components/ui/grouped";
import { usePortalSession } from "@/lib/session";

export default function ProtectionPage() {
  const { dash } = usePortalSession();
  const activeConnections = Math.max(
    0,
    Number(dash?.connection_snapshot?.active_connections ?? dash?.active_sessions ?? 0),
  );
  const serverObserved = activeConnections > 0;

  return (
    <main className="mx-auto flex w-full max-w-[900px] flex-col gap-5">
      <StatusHero
        title={serverObserved ? "Сервер видит подключение" : "Сервер не видит активную сессию"}
        meta={serverObserved ? `${activeConnections} активн.` : "Последний серверный срез"}
        body={
          serverObserved
            ? "Это подтверждает активную серверную сессию, но не заменяет проверки DNS и маршрутов на устройстве."
            : "Откройте приложение: только оно видит системный туннель, DNS и локальные маршруты."
        }
        tone={serverObserved ? "success" : "warning"}
        icon={serverObserved ? ShieldCheck : TriangleAlert}
        action={<Button href="/downloads/">Открыть приложение</Button>}
      />

      <GroupedSection title="Что проверяется отдельно">
        <Row
          icon={Activity}
          label="Туннель"
          hint="Приложение сверяет фактическое состояние runtime на устройстве."
          value={serverObserved ? "есть server-сигнал" : "проверить в приложении"}
        />
        <Row
          icon={Network}
          label="DNS"
          hint="Отдельный host-check; неизвестное состояние не считается успешным."
          value="в приложении"
        />
        <Row
          icon={Globe2}
          label="Интернет / HTTPS"
          hint="Короткий HTTPS-запрос к сервису POKROV, без показа IP."
          value="в приложении"
        />
        <Row
          icon={Route}
          label="Локальные маршруты"
          hint="Счётчики IPv4/IPv6 не выдаются за внешний leak-тест."
          value="в приложении"
        />
      </GroupedSection>

      <Card className="border-info-line bg-info-bg">
        <div className="flex items-start gap-3">
          <span className="grid size-10 shrink-0 place-items-center rounded-[12px] bg-surface text-brand ring-1 ring-line">
            <AppWindow size={20} aria-hidden="true" />
          </span>
          <div>
            <h2 className="text-base font-semibold text-ink">Почему кабинет не рисует четыре зелёные галочки</h2>
            <p className="mt-1 text-sm leading-6 text-ink-soft">
              Браузер не имеет доступа к VPN runtime телефона или компьютера. Здесь показан только серверный сигнал;
              локальные проверки остаются в приложении.
            </p>
          </div>
        </div>
      </Card>

      <GroupedSection title="Восстановление за один цикл">
        <Row
          icon={RefreshCcw}
          label="1. Остановить текущее соединение"
          hint="Если туннель уже запущен, приложение сначала завершает его."
        />
        <Row
          icon={ExternalLink}
          label="2. Получить свежий профиль"
          hint="Текущий аккаунт, локация и правила разрешаются заново."
        />
        <Row
          icon={ShieldCheck}
          label="3. Запустить и повторить проверки"
          hint="Автоматических бесконечных повторов нет."
        />
      </GroupedSection>

      <div className="flex flex-col gap-2 sm:flex-row">
        <Button href="/downloads/" className="w-full sm:w-auto">
          Скачать или обновить POKROV
        </Button>
        <Button href="/support/" variant="secondary" className="w-full sm:w-auto">
          Написать в поддержку
        </Button>
      </div>
    </main>
  );
}
