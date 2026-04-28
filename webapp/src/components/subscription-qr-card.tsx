"use client";

import Image from "next/image";
import { useEffect, useState } from "react";

type Props = {
  value: string;
  active?: boolean;
};

export default function SubscriptionQrCard({ value, active = true }: Props) {
  const [src, setSrc] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    const generate = async () => {
      if (!value || !active) {
        setSrc("");
        setError("");
        return;
      }

      try {
        const { toDataURL } = await import("qrcode");
        const nextSrc = await toDataURL(value, {
          width: 220,
          margin: 1,
          color: {
            dark: "#14211A",
            light: "#F6FAF7",
          },
        });
        if (!cancelled) {
          setSrc(nextSrc);
          setError("");
        }
      } catch (err) {
        if (!cancelled) {
          setSrc("");
          setError(String((err as { message?: string })?.message || err || "Не удалось собрать QR-код для подключения."));
        }
      }
    };

    void generate();
    return () => {
      cancelled = true;
    };
  }, [active, value]);

  if (!value) {
    return <p className="mt-3 text-sm text-slate-500">Ссылка пока недоступна.</p>;
  }

  if (!active) {
    return <p className="mt-3 text-sm text-slate-500">QR-код появится, когда ссылка подключения станет доступна.</p>;
  }

  if (error) {
    return <p className="mt-3 text-sm text-rose-500">{error}</p>;
  }

  if (!src) {
    return <div className="skeleton mt-3 h-[220px] w-[220px] max-w-full rounded-xl border border-white/45 dark:border-white/10" />;
  }

  return (
    <Image
      src={src}
      alt="QR-код ссылки подключения"
      width={220}
      height={220}
      unoptimized
      className="mt-3 h-[220px] w-[220px] max-w-full rounded-xl border border-white/45 bg-white p-2"
    />
  );
}
