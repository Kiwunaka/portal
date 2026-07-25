import type { ReactNode } from "react";
import Link from "next/link";
import { Infinity as InfinityIcon, Sparkles } from "lucide-react";
import { siDiscord, siInstagram, siTiktok, siYoutube } from "simple-icons";

import { Reveal, Stagger } from "../motion/reveal";
import { BrandIcon } from "../ui/brand-icon";
import { Card } from "../ui/card";
import { SectionHeading } from "../ui/section-heading";
import { getCopyText } from "../../lib/pokrov";
import { MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";

type ServiceTile = {
  href: string;
  icon: ReactNode;
  text: string;
  title: string;
};

export function ServicesGrid() {
  const tiles: ServiceTile[] = [
    {
      icon: <BrandIcon icon={siYoutube} />,
      href: MARKETING_CANONICAL_PATHS.youtube,
      title: getCopyText("marketing.home.services.youtube.title", "YouTube через POKROV"),
      text: getCopyText("marketing.home.services.youtube.text", "Смотрите ролики, стримы и длинные видео в нужном качестве"),
    },
    {
      icon: <BrandIcon icon={siTiktok} />,
      href: MARKETING_CANONICAL_PATHS.tiktok,
      title: getCopyText("marketing.home.services.tiktok.title", "TikTok без блокировок"),
      text: getCopyText("marketing.home.services.tiktok.text", "Листайте ленту, ставьте лайки и загружайте ролики"),
    },
    {
      icon: <BrandIcon icon={siInstagram} />,
      href: MARKETING_CANONICAL_PATHS.vpn,
      title: getCopyText("marketing.home.services.social.title", "Instagram и соцсети"),
      text: getCopyText("marketing.home.services.social.text", "Открывайте Instagram, соцсети, звонки и медиа без отдельных профилей"),
    },
    {
      icon: <Sparkles size={18} strokeWidth={1.8} className="text-brand" aria-hidden="true" />,
      href: MARKETING_CANONICAL_PATHS.vpn,
      title: getCopyText("marketing.home.services.ai.title", "ChatGPT без лишних настроек"),
      text: getCopyText("marketing.home.services.ai.text", "Открывайте ChatGPT и другие AI-инструменты одной кнопкой"),
    },
    {
      icon: <BrandIcon icon={siDiscord} />,
      href: MARKETING_CANONICAL_PATHS.vpn,
      title: getCopyText("marketing.home.services.games.title", "Discord и игры"),
      text: getCopyText("marketing.home.services.games.text", "Возвращайтесь в голосовые каналы, игровые магазины и сообщества"),
    },
    {
      icon: <InfinityIcon size={18} strokeWidth={1.8} className="text-brand" aria-hidden="true" />,
      href: MARKETING_CANONICAL_PATHS.compareFreeVpn,
      title: getCopyText("marketing.home.services.rest.title", "Российские сайты — напрямую"),
      text: getCopyText("marketing.home.services.rest.text", "Режим «всё, кроме РУ» оставляет российские сайты на прямом маршруте"),
    },
  ];

  return (
    <section id="features" className="mx-auto max-w-6xl scroll-mt-20 px-4 py-16 sm:px-6 sm:py-24">
      <Reveal>
        <SectionHeading
          kicker={getCopyText("marketing.home.services.kicker", "Интернет без границ")}
          title={getCopyText("marketing.home.services.title", "YouTube, TikTok, ChatGPT — всё в одном VPN")}
          sub={getCopyText(
            "marketing.home.services.sub",
            "Одна кнопка открывает YouTube, TikTok, ChatGPT, соцсети, мессенджеры и игры. Российские сайты идут напрямую в режиме «всё, кроме РУ».",
          )}
        />
      </Reveal>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Stagger>
          {tiles.map((tile) => (
            <Link key={tile.title} href={tile.href} className="block h-full text-inherit no-underline">
              <Card hover className="flex h-full flex-col gap-2.5">
                <span
                  aria-hidden="true"
                  className="flex size-10 items-center justify-center rounded-(--radius-control) bg-canvas-alt"
                >
                  {tile.icon}
                </span>
                <h3 className="text-[1.0625rem] font-semibold text-ink">{tile.title}</h3>
                <p className="text-[0.9375rem] leading-relaxed text-ink-soft">{tile.text}</p>
              </Card>
            </Link>
          ))}
        </Stagger>
      </div>
    </section>
  );
}
