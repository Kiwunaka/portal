import type { Metadata } from "next";
import { JetBrains_Mono, Manrope, Playfair_Display } from "next/font/google";
import Script from "next/script";

import { CANONICAL_WEBAPP_URL } from "@/lib/portal";

import QaOverlayHost from "./qa-overlay-host";
import TelegramWebAppInit from "./telegram-webapp-init";
import "./globals.css";

const bodyFont = Manrope({ subsets: ["latin", "cyrillic"], variable: "--font-body" });
const displayFont = Playfair_Display({ subsets: ["latin", "cyrillic"], variable: "--font-display" });
const mono = JetBrains_Mono({ subsets: ["latin", "cyrillic"], variable: "--font-mono" });

export const metadata: Metadata = {
  metadataBase: new URL(CANONICAL_WEBAPP_URL),
  title: "POKROV Network - Личный кабинет",
  description: "Управление скоростью в одном кабинете: статус, ключи оптимизации, служба заботы и оплата в рублях.",
  robots: {
    index: false,
    follow: false,
  },
};

const QA_OVERLAY_ENABLED = String(process.env.NEXT_PUBLIC_ENABLE_QA_OVERLAY || "").toLowerCase() === "true";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru" className="scroll-smooth" suppressHydrationWarning>
      <body className={`${bodyFont.variable} ${displayFont.variable} ${mono.variable} font-body`} suppressHydrationWarning>
        <Script src="https://telegram.org/js/telegram-web-app.js" strategy="beforeInteractive" />
        <Script
          id="material-symbols-fonts"
          strategy="beforeInteractive"
          dangerouslySetInnerHTML={{
            __html: `(function(){var hrefs=["https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap","https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,1,0&display=swap"];for(var i=0;i<hrefs.length;i++){if(!document.querySelector('link[href="'+hrefs[i]+'"]')){var l=document.createElement('link');l.rel='stylesheet';l.href=hrefs[i];document.head.appendChild(l);}}})();`,
          }}
        />
        <TelegramWebAppInit />
        <QaOverlayHost enabled={QA_OVERLAY_ENABLED} />
        <div className="grain" aria-hidden="true" />
        {children}
      </body>
    </html>
  );
}
