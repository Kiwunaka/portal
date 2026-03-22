import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "POKROV VPN | Приложение для Android и Windows",
  description:
    "POKROV VPN помогает начать с приложения, получить 5-дневный тест и спокойно перейти к кабинету, продлению и поддержке без лишней суеты.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html:
              "(function(){try{var t=localStorage.getItem('pokrov-theme');if(t==='light'||t==='dark'){document.documentElement.setAttribute('data-theme',t);}}catch(_e){}})();",
          }}
        />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body>
        <a href="#main-content" className="skip-link">
          Перейти к содержимому
        </a>
        {children}
      </body>
    </html>
  );
}
