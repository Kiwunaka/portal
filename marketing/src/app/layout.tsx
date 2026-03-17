import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PORTAL VPN через Telegram | Тест 3 дня",
  description:
    "VPN-сервис с bot-first воронкой: сначала тест на 3 дня, потом тарифы, продление и поддержка через Telegram и WebApp.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html:
              "(function(){try{var t=localStorage.getItem('portal-theme');if(t==='light'||t==='dark'){document.documentElement.setAttribute('data-theme',t);}}catch(_e){}})();",
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
