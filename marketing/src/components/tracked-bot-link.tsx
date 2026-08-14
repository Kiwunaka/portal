"use client";

import type { ReactNode } from "react";

import { CANONICAL_BOT_URL } from "../lib/pokrov";
import { mintAcquisitionHandoff } from "../lib/acquisition";
import { Button } from "./ui/button";

export function TrackedBotLink({ children }: { children: ReactNode }) {
  const openBot = async (): Promise<void> => {
    const handoff = await mintAcquisitionHandoff("telegram_continue");
    if (!handoff?.handle) {
      window.location.assign(CANONICAL_BOT_URL);
      return;
    }
    const url = new URL(CANONICAL_BOT_URL);
    url.searchParams.set("start", `acq_${handoff.handle}`);
    window.location.assign(url.toString());
  };

  return (
    <Button
      href={CANONICAL_BOT_URL}
      size="lg"
      data-pokrov-cta="open_bot_with_acquisition"
      onClick={(event) => {
        event.preventDefault();
        void openBot();
      }}
    >
      {children}
    </Button>
  );
}
