"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { CabinetIcon } from "@/components/cabinet/icon";
import { Button } from "@/components/cabinet/ui";
import { useToast } from "@/components/cabinet/toast";

/*
 * Copy-to-clipboard button with an icon morph (copy → check) and a
 * success toast. The check resets back to the copy icon after 1.6s.
 */

type CopyButtonProps = {
  text: string;
  label?: string;
  copiedLabel?: string;
  toastMessage?: string;
  variant?: "primary" | "secondary" | "ghost";
  size?: "md" | "sm";
  disabled?: boolean;
  className?: string;
};

const RESET_DELAY_MS = 1600;

export default function CopyButton({
  text,
  label = "Скопировать",
  copiedLabel = "Скопировано",
  toastMessage = "Скопировано",
  variant = "primary",
  size = "md",
  disabled,
  className,
}: CopyButtonProps) {
  const { showToast } = useToast();
  const [copied, setCopied] = useState(false);
  const resetTimerRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (resetTimerRef.current !== null) window.clearTimeout(resetTimerRef.current);
    };
  }, []);

  const onCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      showToast(toastMessage, "success");
      if (resetTimerRef.current !== null) window.clearTimeout(resetTimerRef.current);
      resetTimerRef.current = window.setTimeout(() => setCopied(false), RESET_DELAY_MS);
    } catch {
      showToast("Не удалось скопировать автоматически. Выделите текст вручную.", "danger");
    }
  }, [showToast, text, toastMessage]);

  return (
    <span data-haptic="rigid" className="inline-flex">
      <Button variant={variant} size={size} disabled={disabled} onClick={() => void onCopy()} className={className}>
        <CabinetIcon name={copied ? "check" : "content_copy"} className="h-[18px] w-[18px]" />
        {copied ? copiedLabel : label}
      </Button>
    </span>
  );
}
