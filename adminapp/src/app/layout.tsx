import type { Metadata, Viewport } from "next";
import { Golos_Text } from "next/font/google";

import { getDesignTokenThemeCss } from "@/lib/portal";

import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://admin.pokrov.space"),
  title: "POKROV Admin",
  description: "POKROV operator dashboard",
  applicationName: "POKROV Admin",
  robots: {
    index: false,
    follow: false
  }
};

export const viewport: Viewport = {
  themeColor: "#ffffff"
};

const fontBody = Golos_Text({
  subsets: ["latin", "cyrillic"],
  variable: "--font-golos",
  display: "swap"
});

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const designTokenThemeCss = getDesignTokenThemeCss("admin");

  return (
    <html lang="ru" className={fontBody.variable}>
      <body>
        <style id="pokrov-design-tokens" dangerouslySetInnerHTML={{ __html: designTokenThemeCss }} />
        {children}
      </body>
    </html>
  );
}
