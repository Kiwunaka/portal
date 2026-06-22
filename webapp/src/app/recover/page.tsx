"use client";

import { useEffect } from "react";

function firstValue(params: URLSearchParams, keys: string[]): string {
  for (const key of keys) {
    const value = String(params.get(key) || "").trim();
    if (value) return value;
  }
  return "";
}

export default function RecoverPage() {
  useEffect(() => {
    const current = new URL(window.location.href);
    const token = firstValue(current.searchParams, ["token", "email_reset_token", "reset_token"]);
    const target = new URL("/", window.location.origin);
    target.searchParams.set("clear_web_session", "1");
    target.searchParams.set("email_mode", "recover");
    if (token) target.searchParams.set("email_reset_token", token);
    window.location.replace(`${target.pathname}${target.search}${target.hash}`);
  }, []);

  return (
    <main className="mx-auto flex min-h-[100dvh] w-full max-w-[720px] items-center px-4 py-8 text-[color:var(--atlas-text)] dark:text-slate-100">
      <p className="text-sm leading-6">Открываем восстановление email-доступа...</p>
    </main>
  );
}
