import type { ReactNode } from "react";
import { Gift, KeyRound, MessagesSquare, Package } from "lucide-react";

import { Stagger } from "../motion/reveal";
import { CANONICAL_GITHUB_RELEASES_URL, getCopyText } from "../../lib/pokrov";

type HonestyItem = {
  href?: string;
  icon: ReactNode;
  text: string;
  title: string;
};

const ICON_PROPS = { size: 18, strokeWidth: 1.8, className: "text-brand", "aria-hidden": true } as const;

export function HonestyStrip() {
  const items: HonestyItem[] = [
    {
      icon: <Gift {...ICON_PROPS} />,
      title: getCopyText("marketing.home.honesty.trial.title", "Триал без карты"),
      text: getCopyText("marketing.home.honesty.trial.text", "5 дней бесплатно — карту не спрашиваем вообще"),
    },
    {
      icon: <KeyRound {...ICON_PROPS} />,
      title: getCopyText("marketing.home.honesty.no_autopay.title", "Без автосписаний"),
      text: getCopyText(
        "marketing.home.honesty.no_autopay.text",
        "Оплата разовым ключом: ничего не продлевается само",
      ),
    },
    {
      icon: <Package {...ICON_PROPS} />,
      title: getCopyText("marketing.home.honesty.releases.title", "Файлы на GitHub"),
      text: getCopyText(
        "marketing.home.honesty.releases.text",
        "Релизы приложения лежат на GitHub Releases — у всех на виду",
      ),
      href: CANONICAL_GITHUB_RELEASES_URL,
    },
    {
      icon: <MessagesSquare {...ICON_PROPS} />,
      title: getCopyText("marketing.home.honesty.support.title", "Живая поддержка"),
      text: getCopyText("marketing.home.honesty.support.text", "Отвечаем в Telegram, без ботов-заглушек"),
    },
  ];

  return (
    <section className="border-y border-line bg-canvas-alt">
      <div className="mx-auto grid max-w-6xl gap-6 px-4 py-10 sm:grid-cols-2 sm:px-6 lg:grid-cols-4">
        <Stagger>
          {items.map((item) => {
            const body = (
              <span className="flex items-start gap-3">
                <span className="mt-0.5 flex size-9 shrink-0 items-center justify-center rounded-full bg-brand-soft">
                  {item.icon}
                </span>
                <span className="flex flex-col gap-0.5">
                  <span className="text-[0.9375rem] font-bold text-ink">{item.title}</span>
                  <span className="text-[0.8125rem] leading-snug text-ink-soft">{item.text}</span>
                </span>
              </span>
            );
            return item.href ? (
              <a
                key={item.title}
                href={item.href}
                target="_blank"
                rel="noopener noreferrer"
                className="no-underline"
              >
                {body}
              </a>
            ) : (
              <div key={item.title}>{body}</div>
            );
          })}
        </Stagger>
      </div>
    </section>
  );
}
