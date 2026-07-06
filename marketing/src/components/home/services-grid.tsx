import type { ReactNode } from "react";
import { Infinity as InfinityIcon, Sparkles } from "lucide-react";
import { siDiscord, siInstagram, siTiktok, siYoutube } from "simple-icons";

import { Reveal, Stagger } from "../motion/reveal";
import { BrandIcon } from "../ui/brand-icon";
import { Card } from "../ui/card";
import { SectionHeading } from "../ui/section-heading";
import { getCopyText } from "../../lib/pokrov";

type ServiceTile = {
  icon: ReactNode;
  text: string;
  title: string;
};

export function ServicesGrid() {
  const tiles: ServiceTile[] = [
    {
      icon: <BrandIcon icon={siYoutube} />,
      title: getCopyText("marketing.home.services.youtube.title", "YouTube в полном качестве"),
      text: getCopyText("marketing.home.services.youtube.text", "Без замедлений, буферизации и «крутилки» на 480p"),
    },
    {
      icon: <BrandIcon icon={siTiktok} />,
      title: getCopyText("marketing.home.services.tiktok.title", "TikTok снова открывается"),
      text: getCopyText("marketing.home.services.tiktok.text", "Лента, лайки и загрузка роликов работают как раньше"),
    },
    {
      icon: <BrandIcon icon={siInstagram} />,
      title: getCopyText("marketing.home.services.social.title", "Соцсети и мессенджеры"),
      text: getCopyText("marketing.home.services.social.text", "Instagram, звонки и медиа в чатах — без танцев с бубном"),
    },
    {
      icon: <Sparkles size={18} strokeWidth={1.8} className="text-brand" aria-hidden="true" />,
      title: getCopyText("marketing.home.services.ai.title", "ИИ-сервисы"),
      text: getCopyText("marketing.home.services.ai.text", "ChatGPT и другие инструменты открываются напрямую"),
    },
    {
      icon: <BrandIcon icon={siDiscord} />,
      title: getCopyText("marketing.home.services.games.title", "Игры и Discord"),
      text: getCopyText("marketing.home.services.games.text", "Голосовые каналы и магазины игр без обрывов"),
    },
    {
      icon: <InfinityIcon size={18} strokeWidth={1.8} className="text-brand" aria-hidden="true" />,
      title: getCopyText("marketing.home.services.rest.title", "И всё остальное"),
      text: getCopyText("marketing.home.services.rest.text", "Маршрут «всё, кроме РУ»: российские сайты идут напрямую"),
    },
  ];

  return (
    <section id="features" className="mx-auto max-w-6xl scroll-mt-20 px-4 py-16 sm:px-6 sm:py-24">
      <Reveal>
        <SectionHeading
          kicker={getCopyText("marketing.home.services.kicker", "Что снова работает")}
          title={getCopyText("marketing.home.services.title", "Любимые сервисы — как раньше")}
          sub={getCopyText(
            "marketing.home.services.sub",
            "Подключение в приложении открывает то, что тормозит или не открывается, — а российские сайты продолжают работать напрямую.",
          )}
        />
      </Reveal>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Stagger>
          {tiles.map((tile) => (
            <Card key={tile.title} hover className="flex h-full flex-col gap-2.5">
              <span
                aria-hidden="true"
                className="flex size-10 items-center justify-center rounded-(--radius-control) bg-canvas-alt"
              >
                {tile.icon}
              </span>
              <h3 className="text-[1.0625rem] font-semibold text-ink">{tile.title}</h3>
              <p className="text-[0.9375rem] leading-relaxed text-ink-soft">{tile.text}</p>
            </Card>
          ))}
        </Stagger>
      </div>
    </section>
  );
}
