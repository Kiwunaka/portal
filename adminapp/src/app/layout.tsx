import type { Metadata, Viewport } from "next";

import { getDesignTokenThemeCss } from "@/lib/portal";

import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://admin.pokrov.space"),
  title: "Центр управления POKROV",
  description: "Операционная админка POKROV: ноды, клиенты, сеть, деньги и управление релизом.",
  applicationName: "Центр управления POKROV",
  robots: {
    index: false,
    follow: false
  }
};

export const viewport: Viewport = {
  colorScheme: "light",
  themeColor: "#ffffff"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const designTokenThemeCss = getDesignTokenThemeCss("admin");

  return (
    <html lang="ru">
      <body>
        <style id="pokrov-design-tokens" dangerouslySetInnerHTML={{ __html: designTokenThemeCss }} />
        {children}
      </body>
    </html>
  );
}
