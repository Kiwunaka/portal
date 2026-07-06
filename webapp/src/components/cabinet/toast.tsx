"use client";

// Compat shim during the wave-2 migration: single toast context lives in
// components/ui/toast. Delete once no page imports from cabinet/toast.
export { ToastProvider, useToast, type ToastTone } from "@/components/ui/toast";
