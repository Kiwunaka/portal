import { BookOpenText } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Note } from "@/components/ui/note";
import {
  TRUST_CATALOG_LAST_VERIFIED,
  USER_GUIDES,
} from "../../../../../shared/trust-and-guides";
import { CabinetGuidesClient } from "./guides-client";

export default function CabinetGuidesPage() {
  return (
    <main className="mx-auto flex w-full max-w-[1040px] flex-col gap-5">
      <Card className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <span className="grid size-11 shrink-0 place-items-center rounded-[14px] bg-brand-soft text-brand">
            <BookOpenText size={22} strokeWidth={2} aria-hidden="true" />
          </span>
          <div>
            <h1 className="text-xl font-bold text-ink">Инструкции POKROV</h1>
            <p className="mt-1 max-w-2xl text-sm leading-6 text-ink-muted">
              {USER_GUIDES.length} задач с поиском и категориями: точные шаги,
              визуалы, стартовые настройки и отдельные ветки ошибки.
            </p>
          </div>
        </div>
        <Badge tone="neutral">Проверено {TRUST_CATALOG_LAST_VERIFIED}</Badge>
      </Card>

      <Note tone="neutral">
        Видео считается готовым только после записи на чистом эмуляторе без
        аккаунта, IP, токенов и личных ссылок. Для семи fallback-клиентов уже
        доступны 18 реальных экранов с точными действиями.
      </Note>

      <CabinetGuidesClient />
    </main>
  );
}
