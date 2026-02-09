import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PORTAL | Network Security",
  description: "Premium network security access with private routing and multi-node architecture.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body>{children}</body>
    </html>
  );
}
