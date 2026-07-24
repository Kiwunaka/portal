import { ArrowLeft, BookOpenCheck } from "lucide-react";
import Link from "next/link";

import { Card } from "@/components/ui/card";
import {
  POKROV_ATLAS_CAPTURE,
  POKROV_SCREEN_ATLAS,
} from "../../../../../../shared/pokrov-screen-atlas";
import { CabinetPokrovAtlasClient } from "./atlas-client";

export default function CabinetPokrovAtlasPage() {
  return (
    <main className="mx-auto flex w-full max-w-[1040px] flex-col gap-5">
      <Link
        href="/guides/"
        className="inline-flex min-h-11 w-fit items-center gap-2 rounded-control px-2 text-sm font-semibold text-brand outline-none hover:bg-brand-soft focus-visible:ring-2 focus-visible:ring-brand"
      >
        <ArrowLeft size={17} aria-hidden="true" />
        Все инструкции
      </Link>

      <Card className="flex items-start gap-3">
        <span className="grid size-11 shrink-0 place-items-center rounded-[14px] bg-brand text-white">
          <BookOpenCheck size={22} strokeWidth={2} aria-hidden="true" />
        </span>
        <div>
          <p className="text-xs font-bold tracking-[0.08em] text-brand uppercase">
            {POKROV_SCREEN_ATLAS.length} экранов · Android{" "}
            {POKROV_ATLAS_CAPTURE.appVersion}
          </p>
          <h1 className="mt-1 text-xl font-bold text-ink">
            Весь POKROV по экранам и кнопкам
          </h1>
          <p className="mt-1 max-w-3xl text-sm leading-6 text-ink-muted">
            Реальные снимки от {POKROV_ATLAS_CAPTURE.date}. Красная рамка
            показывает точную зону, а номер и объяснение вынесены под
            изображение, поэтому интерфейс не закрыт.
          </p>
          <p className="mt-2 max-w-3xl text-xs leading-5 text-ink-muted">
            {POKROV_ATLAS_CAPTURE.privacy}
          </p>
        </div>
      </Card>

      <CabinetPokrovAtlasClient />
    </main>
  );
}
