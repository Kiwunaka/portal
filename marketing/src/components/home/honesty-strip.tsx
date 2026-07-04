import { Stagger } from "../motion/reveal";
import { CANONICAL_GITHUB_RELEASES_URL, getCopyText } from "../../lib/pokrov";

type HonestyItem = {
  href?: string;
  text: string;
  title: string;
};

function ItemIcon({ index }: { index: number }) {
  const icons = [
    // card crossed out (no card needed)
    <svg key="0" width="18" height="18" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <rect x="2" y="4.5" width="16" height="11" rx="2" stroke="var(--pokrov-accent)" strokeWidth="1.6" />
      <path d="M2 8h16" stroke="var(--pokrov-accent)" strokeWidth="1.6" />
      <path d="m4 17 12-14" stroke="var(--pokrov-status-green)" strokeWidth="1.8" strokeLinecap="round" />
    </svg>,
    // key (one-time)
    <svg key="1" width="18" height="18" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <circle cx="7" cy="13" r="3.4" stroke="var(--pokrov-accent)" strokeWidth="1.6" />
      <path d="m9.6 10.4 6.8-6.8m-2.3 2.3 2.3 2.3m-4.6 0 2.3 2.3" stroke="var(--pokrov-accent)" strokeWidth="1.6" strokeLinecap="round" />
    </svg>,
    // github-ish box
    <svg key="2" width="18" height="18" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <path d="M10 2.5 17 6v8l-7 3.5L3 14V6l7-3.5Z" stroke="var(--pokrov-accent)" strokeWidth="1.6" strokeLinejoin="round" />
      <path d="M3 6.2 10 10m0 0 7-3.8M10 10v7" stroke="var(--pokrov-accent)" strokeWidth="1.4" />
    </svg>,
    // chat
    <svg key="3" width="18" height="18" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <path d="M3 4.5h14v9H8l-3.5 3v-3H3v-9Z" stroke="var(--pokrov-accent)" strokeWidth="1.6" strokeLinejoin="round" />
      <path d="M6.5 9h7" stroke="var(--pokrov-status-green)" strokeWidth="1.8" strokeLinecap="round" />
    </svg>,
  ];
  return <>{icons[index]}</>;
}

export function HonestyStrip() {
  const items: HonestyItem[] = [
    {
      title: getCopyText("marketing.home.honesty.trial.title", "Триал без карты"),
      text: getCopyText("marketing.home.honesty.trial.text", "5 дней бесплатно — карту не спрашиваем вообще"),
    },
    {
      title: getCopyText("marketing.home.honesty.no_autopay.title", "Без автосписаний"),
      text: getCopyText(
        "marketing.home.honesty.no_autopay.text",
        "Оплата разовым ключом: ничего не продлевается само",
      ),
    },
    {
      title: getCopyText("marketing.home.honesty.releases.title", "Файлы на GitHub"),
      text: getCopyText(
        "marketing.home.honesty.releases.text",
        "Релизы приложения лежат на GitHub Releases — у всех на виду",
      ),
      href: CANONICAL_GITHUB_RELEASES_URL,
    },
    {
      title: getCopyText("marketing.home.honesty.support.title", "Живая поддержка"),
      text: getCopyText("marketing.home.honesty.support.text", "Отвечаем в Telegram, без ботов-заглушек"),
    },
  ];

  return (
    <section className="border-y border-line bg-canvas-alt">
      <div className="mx-auto grid max-w-6xl gap-6 px-4 py-10 sm:grid-cols-2 sm:px-6 lg:grid-cols-4">
        <Stagger>
          {items.map((item, index) => {
            const body = (
              <span className="flex items-start gap-3">
                <span className="mt-0.5 flex size-9 shrink-0 items-center justify-center rounded-full bg-brand-soft">
                  <ItemIcon index={index} />
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
