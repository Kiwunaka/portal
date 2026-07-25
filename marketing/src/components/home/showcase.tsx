import { ShowcaseScroller, type ShowcaseSlide } from "./showcase-scroller";
import { SectionHeading } from "../ui/section-heading";
import { getCopyText } from "../../lib/pokrov";

export function Showcase() {
  const slides: ShowcaseSlide[] = [
    {
      variant: "connect",
      title: getCopyText("marketing.home.showcase.connect.title", "Нажали — подключились"),
      text: getCopyText(
        "marketing.home.showcase.connect.text",
        "Откройте POKROV и нажмите «Подключить». Никаких ключей, профилей и получасовых гайдов на старте.",
      ),
    },
    {
      variant: "locations",
      title: getCopyText("marketing.home.showcase.locations.title", "Лучший маршрут — автоматически"),
      text: getCopyText(
        "marketing.home.showcase.locations.text",
        "Режим «Авто» выбирает подходящий маршрут сам. Нужна конкретная локация — переключите вручную.",
      ),
    },
    {
      variant: "account",
      title: getCopyText("marketing.home.showcase.account.title", "Весь доступ под контролем"),
      text: getCopyText(
        "marketing.home.showcase.account.text",
        "Срок, устройства, продление и поддержка собраны в одном аккаунте — без поисков по чатам.",
      ),
    },
    {
      variant: "windows",
      title: getCopyText("marketing.home.showcase.windows.title", "Телефон и компьютер вместе"),
      text: getCopyText(
        "marketing.home.showcase.windows.text",
        "Тот же аккаунт и знакомое подключение на компьютере — без отдельной настройки с нуля.",
      ),
    },
  ];

  const heading = (
    <SectionHeading
      align="left"
      className="mb-0"
      kicker={getCopyText("marketing.home.showcase.kicker", "VPN без лишних действий")}
      title={getCopyText("marketing.home.showcase.title", "Всё сложное уже спрятано под одной кнопкой")}
      sub={getCopyText(
        "marketing.home.showcase.sub",
          "Подключение, маршрут, срок и устройства видны сразу. POKROV делает сложную сетевую часть за вас.",
      )}
    />
  );

  return <ShowcaseScroller heading={heading} slides={slides} />;
}
