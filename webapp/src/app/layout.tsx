import type { Metadata } from "next";
import { Inter, Chakra_Petch, JetBrains_Mono } from "next/font/google";
import Script from "next/script";
import QaOverlayHost from "./qa-overlay-host";
import TelegramWebAppInit from "./telegram-webapp-init";
import "./globals.css";

const inter = Inter({ subsets: ["latin", "cyrillic"], variable: "--font-body" });
const chakra = Chakra_Petch({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-display",
});
const mono = JetBrains_Mono({ subsets: ["latin", "cyrillic"], variable: "--font-mono" });

export const metadata: Metadata = {
  title: "PORTAL - Личный кабинет",
  description: "Управление доступом в одном кабинете: статус, ключ подключения, поддержка и оплата в рублях.",
};

const QA_OVERLAY_ENABLED = String(process.env.NEXT_PUBLIC_ENABLE_QA_OVERLAY || "").toLowerCase() === "true";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru" className="scroll-smooth" suppressHydrationWarning>
      <body className={`${inter.variable} ${chakra.variable} ${mono.variable} font-body`} suppressHydrationWarning>
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
