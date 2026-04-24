import type { CSSProperties } from "react";
import type { Metadata, Viewport } from "next";
import { JetBrains_Mono, Manrope } from "next/font/google";
import Script from "next/script";

import { CANONICAL_WEBAPP_URL, getDesignTokenCssVariables } from "@/lib/portal";

import { POKROV_LEGACY_THEME_STORAGE_KEYS, POKROV_THEME_STORAGE_KEY, pokrovBranding } from "./branding";
import QaOverlayHost from "./qa-overlay-host";
import TelegramWebAppInit from "./telegram-webapp-init";
import "./globals.css";

const bodyFont = Manrope({ subsets: ["latin", "cyrillic"], variable: "--font-body" });
const displayFont = Manrope({ subsets: ["latin", "cyrillic"], variable: "--font-display" });
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
    { media: "(prefers-color-scheme: light)", color: "#f7f3eb" },
    { media: "(prefers-color-scheme: dark)", color: "#111715" },
  ],
};

const QA_OVERLAY_ENABLED = String(process.env.NEXT_PUBLIC_ENABLE_QA_OVERLAY || "").toLowerCase() === "true";
const THEME_STORAGE_KEYS = [POKROV_THEME_STORAGE_KEY, ...POKROV_LEGACY_THEME_STORAGE_KEYS];
const THEME_INIT_SCRIPT = `(function(){try{var keys=${JSON.stringify(THEME_STORAGE_KEYS)};var saved=null;for(var i=0;i<keys.length;i++){var value=window.localStorage.getItem(keys[i]);if(value==="light"||value==="dark"){saved=value;break;}}if(saved&&window.localStorage.getItem(keys[0])!==saved){window.localStorage.setItem(keys[0],saved);}var prefersDark=window.matchMedia("(prefers-color-scheme: dark)").matches;document.documentElement.classList.toggle("dark",saved?saved==="dark":prefersDark);}catch(e){}})();`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const designTokenVars = getDesignTokenCssVariables("cabinet") as CSSProperties;

  return (
    <html lang="ru" className="scroll-smooth" suppressHydrationWarning>
      <body
        className={`${bodyFont.variable} ${displayFont.variable} ${mono.variable} relative min-h-screen overflow-x-hidden bg-[var(--bg)] font-body text-[var(--text)] antialiased selection:bg-emerald-700/12 selection:text-slate-950 dark:bg-[#111715] dark:text-[var(--text-dark)] dark:selection:bg-emerald-300/18 dark:selection:text-slate-50`}
        style={designTokenVars}
        suppressHydrationWarning
      >
        <Script id="pokrov-theme-init" strategy="beforeInteractive" dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }} />
        <Script src="https://telegram.org/js/telegram-web-app.js" strategy="afterInteractive" />
        <Script
          id="material-symbols-fonts"
          strategy="afterInteractive"
          dangerouslySetInnerHTML={{
            __html: `(function(){var hrefs=["https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap","https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,1,0&display=swap"];for(var i=0;i<hrefs.length;i++){if(!document.querySelector('link[href="'+hrefs[i]+'"]')){var l=document.createElement('link');l.rel='stylesheet';l.href=hrefs[i];document.head.appendChild(l);}}})();`,
          }}
        />
        <TelegramWebAppInit />
        <QaOverlayHost enabled={QA_OVERLAY_ENABLED} />
        <div
          className="pointer-events-none fixed inset-0 -z-20 bg-[radial-gradient(circle_at_top_left,_rgba(32,103,79,0.05),_transparent_28%),linear-gradient(180deg,_rgba(255,255,255,0.34),_rgba(247,243,235,0.96))] dark:bg-[radial-gradient(circle_at_top_left,_rgba(45,129,101,0.1),_transparent_26%),linear-gradient(180deg,_rgba(17,23,21,0.98),_rgba(14,18,17,1))]"
          aria-hidden="true"
        />
        <div className="grain" aria-hidden="true" />
        {children}
      </body>
    </html>
  );
}
