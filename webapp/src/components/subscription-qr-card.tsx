"use client";

import Image from "next/image";
import { useEffect, useState } from "react";

type Props = {
  value: string;
  active?: boolean;
  alt?: string;
};

export default function SubscriptionQrCard({ value, active = true, alt = "QR-код ссылки подключения" }: Props) {
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
    return <p className="mt-3 text-sm text-[color:var(--atlas-text-soft)]">Ссылка пока недоступна.</p>;
  }

  if (!active) {
    return <p className="mt-3 text-sm text-[color:var(--atlas-text-soft)]">QR-код появится, когда ссылка подключения станет доступна.</p>;
  }

  if (error) {
    return <p className="mt-3 text-sm text-[color:var(--atlas-status-danger-text)]">{error}</p>;
  }

  if (!src) {
    return <div className="skeleton mt-3 h-[220px] w-[220px] max-w-full rounded-xl border border-[color:var(--atlas-border)]" />;
  }

  return (
    <Image
      src={src}
      alt={alt}
      width={220}
      height={220}
      unoptimized
      className="mt-3 h-[220px] w-[220px] max-w-full rounded-xl border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] p-2"
    />
  );
}
