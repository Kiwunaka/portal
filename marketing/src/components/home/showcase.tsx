import { ShowcaseScroller, type ShowcaseSlide } from "./showcase-scroller";
import { SectionHeading } from "../ui/section-heading";
import { getCopyText } from "../../lib/pokrov";

export function Showcase() {
  const slides: ShowcaseSlide[] = [
    {
      variant: "connect",
      title: getCopyText("marketing.home.showcase.connect.title", "Одна кнопка"),
      text: getCopyText(
        "marketing.home.showcase.connect.text",
        "Открыли приложение, нажали — подключено. Отключается так же просто.",
      ),
    },
    {
      variant: "locations",
      title: getCopyText("marketing.home.showcase.locations.title", "Маршрут выбирается сам"),
      text: getCopyText(
        "marketing.home.showcase.locations.text",
        "Режим «Авто» держит лучший маршрут. Хотите конкретный — выбирайте вручную.",
      ),
    },
    {
      variant: "account",
      title: getCopyText("marketing.home.showcase.account.title", "Всё по-честному в аккаунте"),
      text: getCopyText(
        "marketing.home.showcase.account.text",
        "Сколько дней осталось, какие устройства подключены, где продлить — видно сразу.",
      ),
    },
    {
      variant: "windows",
      title: getCopyText("marketing.home.showcase.windows.title", "На компьютере — так же"),
      text: getCopyText(
        "marketing.home.showcase.windows.text",
        "Windows-приложение выглядит и работает так же просто, как мобильное.",
      ),
    },
  ];

  const heading = (
    <SectionHeading
      align="left"
      className="mb-0"
      kicker={getCopyText("marketing.home.showcase.kicker", "Приложение")}
      title={getCopyText("marketing.home.showcase.title", "Вот как это выглядит")}
      sub={getCopyText(
        "marketing.home.showcase.sub",
        "Никаких скрытых экранов и мелкого шрифта — всё приложение перед вами.",
      )}
    />
  );

  return <ShowcaseScroller heading={heading} slides={slides} />;
}
