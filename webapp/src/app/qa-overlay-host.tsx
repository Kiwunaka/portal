"use client";

import dynamic from "next/dynamic";

const QaOverlay = dynamic(() => import("./qa-overlay"), { ssr: false });

export default function QaOverlayHost({ enabled }: { enabled: boolean }) {
  if (!enabled) return null;
  return <QaOverlay />;
}
