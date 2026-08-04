import type { Metadata, Viewport } from "next";
import Script from "next/script";

import "@fontsource-variable/golos-text";
import "@fontsource-variable/jetbrains-mono";

import { CANONICAL_WEBAPP_URL, getDesignTokenThemeCss } from "@/lib/portal";

import { POKROV_LEGACY_THEME_STORAGE_KEYS, POKROV_THEME_STORAGE_KEY, pokrovBranding } from "./branding";
import QaOverlayHost from "./qa-overlay-host";
import TelegramWebAppInit from "./telegram-webapp-init";
import "./globals.css";

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
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#111715" },
  ],
};

const QA_OVERLAY_ENABLED = String(process.env.NEXT_PUBLIC_ENABLE_QA_OVERLAY || "").toLowerCase() === "true";
const THEME_STORAGE_KEYS = [POKROV_THEME_STORAGE_KEY, ...POKROV_LEGACY_THEME_STORAGE_KEYS];
const THEME_INIT_SCRIPT = `(function(){try{var keys=${JSON.stringify(THEME_STORAGE_KEYS)};var saved=null;for(var i=0;i<keys.length;i++){var value=window.localStorage.getItem(keys[i]);if(value==="light"||value==="dark"){saved=value;break;}}if(saved&&window.localStorage.getItem(keys[0])!==saved){window.localStorage.setItem(keys[0],saved);}var prefersDark=window.matchMedia("(prefers-color-scheme: dark)").matches;document.documentElement.classList.toggle("dark",saved?saved==="dark":prefersDark);}catch(e){}})();`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const designTokenThemeCss = getDesignTokenThemeCss("cabinet");

  return (
    <html
      lang="ru"
      className="scroll-smooth"
      data-scroll-behavior="smooth"
      suppressHydrationWarning
    >
      <body
        className="relative min-h-screen overflow-x-hidden bg-[var(--bg)] font-body text-[var(--text)] antialiased selection:bg-[color:color-mix(in_srgb,var(--atlas-primary)_16%,transparent)] selection:text-[color:var(--atlas-text)]"
        suppressHydrationWarning
      >
        <style id="pokrov-design-tokens" dangerouslySetInnerHTML={{ __html: designTokenThemeCss }} />
        {/* Official Telegram Mini App SDK v63, mirrored from
            https://telegram.org/js/telegram-web-app.js?63 on 2026-07-21.
            SHA-256: 3549138a7934039fe7dfd1291a4ee739bd2b705a614308053a8b08a87d85c451.
            Self-hosting avoids blocking cabinet hydration when telegram.org is unavailable. */}
        <Script src="/telegram-web-app.js" strategy="beforeInteractive" />
        <Script id="pokrov-theme-init" strategy="beforeInteractive" dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }} />
        <TelegramWebAppInit />
        <QaOverlayHost enabled={QA_OVERLAY_ENABLED} />
        {children}
      </body>
    </html>
  );
}
