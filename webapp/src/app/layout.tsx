import type { Metadata, Viewport } from "next";
import { JetBrains_Mono, Manrope, Playfair_Display } from "next/font/google";
import Script from "next/script";

import { CANONICAL_WEBAPP_URL } from "@/lib/portal";

import { POKROV_LEGACY_THEME_STORAGE_KEYS, POKROV_THEME_STORAGE_KEY, pokrovBranding } from "./branding";
import QaOverlayHost from "./qa-overlay-host";
import TelegramWebAppInit from "./telegram-webapp-init";
import "./globals.css";

const bodyFont = Manrope({ subsets: ["latin", "cyrillic"], variable: "--font-body" });
const displayFont = Playfair_Display({ subsets: ["latin", "cyrillic"], variable: "--font-display" });
const mono = JetBrains_Mono({ subsets: ["latin", "cyrillic"], variable: "--font-mono" });

export const metadata: Metadata = {
  metadataBase: new URL(CANONICAL_WEBAPP_URL),
  title: pokrovBranding.metadataTitle,
  description: pokrovBranding.metadataDescription,
  applicationName: pokrovBranding.brandName,
  robots: {
    index: false,
    follow: false,
  },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f2ece1" },
    { media: "(prefers-color-scheme: dark)", color: "#08110d" },
  ],
};

const QA_OVERLAY_ENABLED = String(process.env.NEXT_PUBLIC_ENABLE_QA_OVERLAY || "").toLowerCase() === "true";
const THEME_STORAGE_KEYS = [POKROV_THEME_STORAGE_KEY, ...POKROV_LEGACY_THEME_STORAGE_KEYS];
const THEME_INIT_SCRIPT = `(function(){try{var keys=${JSON.stringify(THEME_STORAGE_KEYS)};var saved=null;for(var i=0;i<keys.length;i++){var value=window.localStorage.getItem(keys[i]);if(value==="light"||value==="dark"){saved=value;break;}}if(saved&&window.localStorage.getItem(keys[0])!==saved){window.localStorage.setItem(keys[0],saved);}var prefersDark=window.matchMedia("(prefers-color-scheme: dark)").matches;document.documentElement.classList.toggle("dark",saved?saved==="dark":prefersDark);}catch(e){}})();`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru" className="scroll-smooth" suppressHydrationWarning>
      <body
        className={`${bodyFont.variable} ${displayFont.variable} ${mono.variable} relative min-h-screen overflow-x-hidden bg-[#f2ece1] font-body text-slate-900 antialiased selection:bg-emerald-700/15 selection:text-slate-950 dark:bg-[#08110d] dark:text-slate-100 dark:selection:bg-emerald-300/20 dark:selection:text-slate-50`}
        suppressHydrationWarning
      >
        <Script src="https://telegram.org/js/telegram-web-app.js" strategy="beforeInteractive" />
        <Script id="pokrov-theme-init" strategy="beforeInteractive" dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }} />
        <Script
          id="material-symbols-fonts"
          strategy="beforeInteractive"
          dangerouslySetInnerHTML={{
            __html: `(function(){var hrefs=["https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap","https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,1,0&display=swap"];for(var i=0;i<hrefs.length;i++){if(!document.querySelector('link[href="'+hrefs[i]+'"]')){var l=document.createElement('link');l.rel='stylesheet';l.href=hrefs[i];document.head.appendChild(l);}}})();`,
          }}
        />
        <TelegramWebAppInit />
        <QaOverlayHost enabled={QA_OVERLAY_ENABLED} />
        <div
          className="pointer-events-none fixed inset-0 -z-20 bg-[radial-gradient(circle_at_top_left,_rgba(11,72,50,0.16),_transparent_33%),radial-gradient(circle_at_bottom_right,_rgba(197,138,42,0.14),_transparent_30%),linear-gradient(180deg,_rgba(255,255,255,0.48),_rgba(242,236,225,0.96))] dark:bg-[radial-gradient(circle_at_top_left,_rgba(36,117,82,0.18),_transparent_28%),radial-gradient(circle_at_bottom_right,_rgba(197,138,42,0.1),_transparent_24%),linear-gradient(180deg,_rgba(8,17,13,0.98),_rgba(7,14,11,1))]"
          aria-hidden="true"
        />
        <div className="grain" aria-hidden="true" />
        {children}
      </body>
    </html>
  );
}
