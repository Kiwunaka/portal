"use client";

import type { LucideIcon } from "lucide-react";
import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import {
  CheckCircle2,
  ChevronDown,
  CircleAlert,
  Download,
  FileText,
  Hourglass,
  LifeBuoy,
  MonitorSmartphone,
  RefreshCw,
  Smartphone,
  TabletSmartphone,
} from "lucide-react";

import { InstructionSteps } from "@/components/cabinet/instructions";
import { StatusHero } from "@/components/cabinet/status-hero";
import { Button } from "@/components/ui/button";
import { GroupedSection, Row } from "@/components/ui/grouped";
import { cn } from "@/components/utils";
import { fetchClientApps, type ClientAppsPayload } from "@/lib/api";
import { getCopyText, getPortalPublicConfig } from "@/lib/portal";
import { userFacingErrorMessage } from "@/lib/public-error-messages";

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);
const SHA256_PATTERN = /^[a-f0-9]{64}$/i;

type HostPlatform = "android" | "windows" | "apple" | "unknown";
type ArtifactState = "complete" | "partial" | "missing";

type ReleaseArtifact = {
  key: string;
  platform: "android" | "windows";
  icon: LucideIcon;
  label: string;
  architecture: string;
  format: "APK" | "EXE";
  href: string;
  version: string;
  channel: string;
  publishedAt: string;
  size: number;
  sha256: string;
  releaseNotes: string;
  releaseNotesUrl: string;
  state: ArtifactState;
  missing: string[];
};

function detectHostPlatform(): HostPlatform {
  if (typeof navigator === "undefined") return "unknown";
  const value = `${navigator.userAgent || ""} ${navigator.platform || ""}`.toLowerCase();
  if (value.includes("android")) return "android";
  if (value.includes("windows") || value.includes("win32") || value.includes("win64")) return "windows";
  if (/iphone|ipad|ipod|macintosh|macintel/.test(value)) return "apple";
  return "unknown";
}

function subscribeHostPlatform(): () => void {
  return () => undefined;
}

function formatDate(value?: string | null): string {
  if (!value) return "не указана";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "не указана";
  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(parsed);
}

function formatBytes(value: number): string {
  if (!Number.isFinite(value) || value <= 0) return "не указан";
  const mebibytes = value / (1024 * 1024);
  return `${new Intl.NumberFormat("ru-RU", { maximumFractionDigits: mebibytes >= 10 ? 0 : 1 }).format(mebibytes)} МиБ`;
}

function channelLabel(value: string): string {
  switch (value.trim().toLowerCase()) {
    case "stable":
      return "Стабильный";
    case "beta":
      return "Бета";
    default:
      return value.trim() || "не указан";
  }
}

function artifactState(artifact: Omit<ReleaseArtifact, "state" | "missing">): Pick<ReleaseArtifact, "state" | "missing"> {
  const missing: string[] = [];
  if (!artifact.version.trim()) missing.push("версия");
  if (!artifact.channel.trim()) missing.push("канал");
  if (!artifact.publishedAt.trim() || Number.isNaN(new Date(artifact.publishedAt).getTime())) missing.push("дата");
  if (!Number.isInteger(artifact.size) || artifact.size <= 0) missing.push("размер");
  if (!SHA256_PATTERN.test(artifact.sha256.trim())) missing.push("SHA-256");
  if (!artifact.releaseNotes.trim()) missing.push("release notes");
  if (!artifact.releaseNotesUrl.trim()) missing.push("ссылка на release notes");
  return {
    state: !artifact.href ? "missing" : missing.length ? "partial" : "complete",
    missing,
  };
}

function finalizeArtifact(artifact: Omit<ReleaseArtifact, "state" | "missing">): ReleaseArtifact {
  return { ...artifact, ...artifactState(artifact) };
}

function androidArtifactCopy(abi: string): Pick<ReleaseArtifact, "label" | "architecture"> {
  switch (abi) {
    case "arm64-v8a":
      return { label: "Приложение для Android", architecture: "ARM64 · большинство телефонов" };
    case "armeabi-v7a":
      return { label: "Android для старых устройств", architecture: "ARMv7" };
    case "x86_64":
      return { label: "Android для эмулятора", architecture: "x86_64" };
    case "universal":
      return { label: "Приложение для Android", architecture: "Universal" };
    default:
      return { label: "Приложение для Android", architecture: abi || "архитектура не указана" };
  }
}

function buildArtifacts(payload: ClientAppsPayload | null): ReleaseArtifact[] {
  const android = payload?.android;
  const androidVersion = String(android?.version || android?.update?.latest_version || "").trim();
  const androidChannel = String(android?.update?.channel || "").trim();
  const androidPublishedAt = String(android?.published_at || android?.update?.published_at || "").trim();
  const androidVariants = (android?.apk_variants || []).filter((item) => item.url);
  const variants = androidVariants.length
    ? androidVariants
    : [{ abi: "universal", label: "Android Universal", url: android?.apk_url || "", sha256: android?.sha256, size: android?.size }];
  const artifacts = variants.map((variant) => {
    const primaryMetadata = variant.url === android?.apk_url;
    const copy = androidArtifactCopy(variant.abi);
    return finalizeArtifact({
      key: `android-${variant.abi || "apk"}`,
      platform: "android" as const,
      icon: Smartphone,
      label: copy.label,
      architecture: copy.architecture,
      format: "APK" as const,
      href: String(variant.url || "").trim(),
      version: androidVersion,
      channel: androidChannel,
      publishedAt: androidPublishedAt,
      size: Number(variant.size || (primaryMetadata ? android?.size || android?.update?.size : 0) || 0),
      sha256: String(variant.sha256 || (primaryMetadata ? android?.sha256 || android?.update?.sha256 : "") || "").trim(),
      releaseNotes: String(android?.release_notes || android?.update?.release_notes || "").trim(),
      releaseNotesUrl: String(android?.release_notes_url || android?.update?.release_notes_url || "").trim(),
    });
  });

  const windows = payload?.windows;
  artifacts.push(finalizeArtifact({
    key: "windows-x64",
    platform: "windows",
    icon: MonitorSmartphone,
    label: "Приложение для Windows",
    architecture: "x64",
    format: "EXE",
    href: String(windows?.exe_url || "").trim(),
    version: String(windows?.version || windows?.update?.latest_version || "").trim(),
    channel: String(windows?.update?.channel || "").trim(),
    publishedAt: String(windows?.published_at || windows?.update?.published_at || "").trim(),
    size: Number(windows?.size || windows?.update?.size || 0),
    sha256: String(windows?.sha256 || windows?.update?.sha256 || "").trim(),
    releaseNotes: String(windows?.release_notes || windows?.update?.release_notes || "").trim(),
    releaseNotesUrl: String(windows?.release_notes_url || windows?.update?.release_notes_url || "").trim(),
  }));

  return artifacts;
}

function primaryArtifact(artifacts: ReleaseArtifact[], platform: HostPlatform): ReleaseArtifact | null {
  if (platform === "windows") return artifacts.find((item) => item.platform === "windows") || null;
  if (platform !== "android") return null;
  return artifacts.find((item) => item.key === "android-arm64-v8a")
    || artifacts.find((item) => item.key === "android-universal")
    || artifacts.find((item) => item.platform === "android")
    || null;
}

function stateCopy(state: ArtifactState): { label: string; className: string } {
  if (state === "complete") return { label: "Метаданные полные", className: "bg-ok-bg text-ok-text" };
  if (state === "partial") return { label: "Метаданные неполные", className: "bg-warn-bg text-warn-text" };
  return { label: "Файл недоступен", className: "bg-danger-bg text-danger-text" };
}

function ReleaseCard({ artifact, primary }: { artifact: ReleaseArtifact; primary: boolean }) {
  const Icon = artifact.icon;
  const status = stateCopy(artifact.state);
  return (
    <article
      data-testid={`release-card-${artifact.platform}`}
      className={cn(
        "flex min-w-0 flex-col gap-4 rounded-card border bg-surface p-4 shadow-soft",
        primary ? "border-brand/40 ring-1 ring-brand/15" : "border-line",
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <span className="grid size-11 shrink-0 place-items-center rounded-[12px] bg-brand-soft text-brand">
          <Icon size={22} strokeWidth={1.9} aria-hidden="true" />
        </span>
        <span className={cn("rounded-full px-2.5 py-1 text-xs font-bold", status.className)}>{status.label}</span>
      </div>
      <div>
        <h3 className="text-sm font-semibold text-ink">{artifact.label}</h3>
        <p className="mt-1 text-[13px] leading-5 text-ink-soft">{artifact.architecture} · {artifact.format}</p>
      </div>
      <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-2 text-[13px] leading-5">
        <dt className="text-ink-soft">Версия</dt><dd className="min-w-0 text-right font-semibold text-ink">{artifact.version || "не указана"}</dd>
        <dt className="text-ink-soft">Канал</dt><dd className="min-w-0 text-right font-semibold text-ink">{channelLabel(artifact.channel)}</dd>
        <dt className="text-ink-soft">Опубликовано</dt><dd className="min-w-0 text-right font-semibold text-ink">{formatDate(artifact.publishedAt)}</dd>
        <dt className="text-ink-soft">Размер</dt><dd className="min-w-0 text-right font-semibold text-ink">{formatBytes(artifact.size)}</dd>
      </dl>
      {artifact.state === "complete" ? (
        <>
          <div className="rounded-control border border-line bg-canvas-alt p-3">
            <p className="text-xs font-semibold text-ink-soft">Что нового</p>
            <p className="mt-1 text-[13px] leading-5 text-ink">{artifact.releaseNotes}</p>
            <a
              href={artifact.releaseNotesUrl}
              target="_blank"
              rel="noreferrer"
              className="mt-2 inline-flex min-h-11 items-center text-xs font-semibold text-brand hover:underline"
            >
              Полные заметки о релизе
            </a>
          </div>
          <div className="rounded-control border border-line bg-canvas-alt p-3">
            <p className="text-xs font-semibold text-ink-soft">SHA-256</p>
            <code className="mt-1 block break-all font-mono text-[11px] leading-4 text-ink">{artifact.sha256.toLowerCase()}</code>
          </div>
        </>
      ) : (
        <p className="flex items-start gap-2 rounded-control border border-warn-line bg-warn-bg p-3 text-[13px] leading-5 text-warn-text">
          <CircleAlert size={16} className="mt-0.5 shrink-0" aria-hidden="true" />
          {artifact.state === "missing"
            ? "Ссылка на файл не опубликована. Кабинет не подставляет файл другой платформы."
            : `Не хватает: ${artifact.missing.join(", ")}. Скачивание скрыто до полного release-контракта.`}
        </p>
      )}
      {artifact.state === "complete" ? (
        <Button href={artifact.href} target="_blank" rel="noreferrer" block data-testid={`download-${artifact.platform}`}>
          Скачать {artifact.format}
        </Button>
      ) : (
        <Button href="/support/" variant="secondary" block>Открыть поддержку</Button>
      )}
    </article>
  );
}

export function CabinetDownloadsSurface() {
  const [payload, setPayload] = useState<ClientAppsPayload | null>(null);
  const [error, setError] = useState("");
  const [selectedPlatform, setSelectedPlatform] = useState<HostPlatform | null>(null);
  const detectedPlatform = useSyncExternalStore<HostPlatform>(
    subscribeHostPlatform,
    detectHostPlatform,
    () => "unknown",
  );
  const platform = selectedPlatform || detectedPlatform;

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const next = await fetchClientApps();
        if (!cancelled) {
          setPayload(next);
          setError("");
        }
      } catch (nextError) {
        if (!cancelled) setError(userFacingErrorMessage(nextError, "Проверьте соединение и обновите страницу."));
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const artifacts = useMemo(() => buildArtifacts(payload), [payload]);
  const androidPrimary = primaryArtifact(artifacts, "android");
  const windowsPrimary = primaryArtifact(artifacts, "windows");
  const selectedArtifact = primaryArtifact(artifacts, platform);
  const extraAndroid = artifacts.filter((item) => item.platform === "android" && item !== androidPrimary);
  const docsUrl = payload?.docs_url || config.docsUrl;
  const appleSelected = platform === "apple";
  const unknownSelected = platform === "unknown";

  const heroMeta = unknownSelected
    ? "Платформа не определена"
    : appleSelected
      ? "Ручная настройка"
      : selectedArtifact?.state === "complete"
        ? `${selectedArtifact.version} · ${channelLabel(selectedArtifact.channel)}`
        : selectedArtifact?.state === "partial"
          ? "Release-контракт неполный"
          : "Файл временно недоступен";
  const heroBody = unknownSelected
    ? "Выберите устройство: кабинет не назначает APK или EXE наугад."
    : appleSelected
      ? "Для iPhone, iPad и Mac доступна отдельная ручная настройка внутри аккаунта. Нативный Apple-релиз не заявлен."
      : selectedArtifact?.state === "complete"
        ? `${selectedArtifact.label}: ${selectedArtifact.architecture}, ${formatBytes(selectedArtifact.size)}. Сверьте SHA-256 после загрузки.`
        : "Скачивание этой платформы скрыто, пока ссылка и обязательные метаданные релиза не станут полными.";

  return (
    <main className="mx-auto flex w-full max-w-[900px] flex-col gap-5">
      <StatusHero
        title={getCopyText("webapp.downloads.title", "Загрузки")}
        meta={heroMeta}
        body={heroBody}
        tone={selectedArtifact?.state === "complete" || appleSelected ? "success" : selectedArtifact?.state === "partial" ? "warning" : "neutral"}
        icon={Download}
        action={
          selectedArtifact?.state === "complete" ? (
            <Button href={selectedArtifact.href} target="_blank" rel="noreferrer" className="w-full sm:w-auto" data-testid="primary-download">
              Скачать для {platform === "windows" ? "Windows" : "Android"}
            </Button>
          ) : appleSelected ? (
            <Button href="/subscription/#manual-setup" className="w-full sm:w-auto">Настроить Apple</Button>
          ) : unknownSelected ? (
            <Button disabled className="w-full sm:w-auto">Выберите платформу</Button>
          ) : (
            <Button href="/support/" variant="secondary" className="w-full sm:w-auto">Открыть поддержку</Button>
          )
        }
      />

      <section className="flex flex-col gap-2.5">
        <h2 className="px-1 text-xs font-bold tracking-[0.08em] text-ink-soft uppercase">Ваше устройство</h2>
        <div className="grid grid-cols-3 gap-2 rounded-card border border-line bg-surface p-2 shadow-soft" role="group" aria-label="Выбор платформы">
          {([
            ["android", "Android", Smartphone],
            ["windows", "Windows", MonitorSmartphone],
            ["apple", "Apple", TabletSmartphone],
          ] as const).map(([value, label, Icon]) => (
            <button
              key={value}
              type="button"
              aria-pressed={platform === value}
              data-testid={`platform-${value}`}
              onClick={() => setSelectedPlatform(value)}
              className={cn(
                "flex min-h-12 items-center justify-center gap-2 rounded-control px-2 text-sm font-semibold outline-none transition-colors focus-visible:ring-2 focus-visible:ring-brand motion-reduce:transition-none",
                platform === value ? "bg-brand text-brand-contrast" : "text-ink-soft hover:bg-canvas-alt hover:text-ink",
              )}
            >
              <Icon size={17} aria-hidden="true" />
              <span>{label}</span>
            </button>
          ))}
        </div>
      </section>

      <section className="flex flex-col gap-2.5">
        <h2 className="px-1 text-xs font-bold tracking-[0.08em] text-ink-soft uppercase">Сборки</h2>
        {payload ? (
          <div className="grid gap-3 md:grid-cols-2">
            {androidPrimary ? <ReleaseCard artifact={androidPrimary} primary={platform === "android"} /> : null}
            {windowsPrimary ? <ReleaseCard artifact={windowsPrimary} primary={platform === "windows"} /> : null}
          </div>
        ) : (
          <GroupedSection>
            <Row icon={Hourglass} label="Метаданные загружаются" hint="Кабинет проверяет ссылки и контрольные суммы" />
          </GroupedSection>
        )}

        <article className={cn("flex flex-col gap-3 rounded-card border bg-surface p-4 shadow-soft", platform === "apple" ? "border-brand/40 ring-1 ring-brand/15" : "border-line")}>
          <div className="flex items-center gap-3">
            <span className="grid size-11 shrink-0 place-items-center rounded-[12px] bg-brand-soft text-brand">
              <TabletSmartphone size={22} strokeWidth={1.9} aria-hidden="true" />
            </span>
            <div>
              <h3 className="text-sm font-semibold text-ink">iPhone, iPad и Mac</h3>
              <p className="mt-1 text-[13px] leading-5 text-ink-soft">Ручная настройка · без заявления о нативном релизе</p>
            </div>
          </div>
          <Button href="/subscription/#manual-setup" variant="secondary" block>Настроить</Button>
        </article>
      </section>

      {extraAndroid.length ? (
        <details className="group overflow-hidden rounded-card border border-line bg-surface shadow-soft">
          <summary className="flex min-h-12 cursor-pointer list-none items-center justify-between gap-3 px-4 py-3 text-sm font-semibold text-ink outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-inset">
            Другие варианты Android
            <ChevronDown className="shrink-0 text-ink-muted transition-transform group-open:rotate-180 motion-reduce:transition-none" size={18} strokeWidth={2} aria-hidden="true" />
          </summary>
          <div className="border-t border-line">
            <GroupedSection>
              {extraAndroid.map((artifact) => (
                <Row
                  key={artifact.key}
                  icon={artifact.icon}
                  label={artifact.label}
                  hint={`${artifact.architecture} · ${artifact.state === "complete" ? `${artifact.version}, ${formatBytes(artifact.size)}` : "метаданные неполные"}`}
                  value={artifact.format}
                  action={artifact.state === "complete" ? (
                    <a href={artifact.href} target="_blank" rel="noreferrer" className="inline-flex min-h-12 items-center rounded-control px-2 text-sm font-semibold text-brand hover:bg-brand-soft hover:text-brand-strong">Скачать</a>
                  ) : undefined}
                />
              ))}
            </GroupedSection>
          </div>
        </details>
      ) : null}

      {error ? (
        <p className="flex items-start gap-2 rounded-control border border-warn-line bg-warn-bg p-3 text-sm text-warn-text" role="status">
          <CircleAlert size={17} className="mt-0.5 shrink-0" aria-hidden="true" />
          Метаданные не обновились: {error}
        </p>
      ) : null}

      <details className="group overflow-hidden rounded-card border border-line bg-surface shadow-soft">
        <summary className="flex min-h-12 cursor-pointer list-none items-center justify-between gap-3 px-4 py-3 text-sm font-semibold text-ink outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-inset">
          Android и Windows: подключение за 3 шага
          <ChevronDown className="shrink-0 text-ink-muted transition-transform group-open:rotate-180 motion-reduce:transition-none" size={18} strokeWidth={2} aria-hidden="true" />
        </summary>
        <div className="border-t border-line p-3">
          <InstructionSteps
            steps={[
              { art: "download", title: "Скачайте и установите", description: "Берите файл только на этой странице и сверяйте SHA-256." },
              { art: "login", title: "Войдите в тот же аккаунт", description: "Почта или Telegram. Доступ подтянется сам." },
              { art: "connect", title: "Нажмите «Подключить»", description: "Настраивать профиль вручную не нужно." },
            ]}
          />
        </div>
      </details>

      <GroupedSection title="После скачивания">
        <Row icon={CheckCircle2} label="Проверить устройство" hint="После входа оно появится в списке" href="/devices/" />
        {docsUrl ? <Row icon={FileText} label="Инструкция" hint="Установка и первый вход" action={<a href={docsUrl} target="_blank" rel="noreferrer" className="inline-flex min-h-12 items-center rounded-control px-2 text-sm font-semibold text-brand hover:bg-brand-soft">Открыть</a>} /> : null}
        <Row icon={LifeBuoy} label="Поддержка" hint="Если файл не открылся или вход не прошёл" href="/support/" />
        <Row icon={RefreshCw} label="Метаданные обновлены" hint="По данным release-контракта" value={formatDate(payload?.updated_at)} />
      </GroupedSection>
    </main>
  );
}

export default CabinetDownloadsSurface;
