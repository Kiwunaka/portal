import type { Metadata } from "next";
import { Inter, Chakra_Petch, JetBrains_Mono } from "next/font/google";
import Script from "next/script";
import QaOverlay from "./qa-overlay";
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
  title: "PORTAL — VPN кабинет",
  description:
    "Управление VPN-доступом в одном кабинете: статус, ключ подключения, поддержка и оплата в рублях.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru" className="scroll-smooth" suppressHydrationWarning>
      <head>
        <Script src="https://telegram.org/js/telegram-web-app.js" strategy="beforeInteractive" />
        <link
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap"
          rel="stylesheet"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,1,0&display=optional"
          rel="stylesheet"
        />
      </head>
      <body className={`${inter.variable} ${chakra.variable} ${mono.variable} font-body`} suppressHydrationWarning>
        <TelegramWebAppInit />
        <QaOverlay />
        <div className="grain" aria-hidden="true" />
        {children}
      </body>
    </html>
  );
}
