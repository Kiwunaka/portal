import type { Metadata } from "next";
import { getCopyText } from "../lib/portal";
import "./globals.css";

export const metadata: Metadata = {
  title: getCopyText("marketing.meta.title", "PORTAL - цифровой доступ без лишних шагов"),
  description: getCopyText(
    "marketing.meta.description",
    "Быстрый запуск через Telegram, оплата в рублях и спокойный личный кабинет без перегруза деталями.",
  )
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html:
              "(function(){try{var t=localStorage.getItem('portal-theme');if(t==='light'||t==='dark'){document.documentElement.setAttribute('data-theme',t);}}catch(_e){}})();"
          }}
        />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body>
        <a href="#main-content" className="skip-link">Skip to content</a>
        {children}
      </body>
    </html>
  );
}
