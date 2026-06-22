"use client";

import AppRouteLink from "@/components/app-route-link";
import {
  AdminBadge,
  AdminEmptyState,
  AdminMetricStrip,
  AdminPanelHeader,
  adminButtonClass,
  adminInsetPanelClass,
  adminPanelClass,
} from "@/components/admin/admin-shell";
import {
  adminMetricsStatus,
  fetchClientApps,
  getEmailAuthStatus,
  getRubPaymentProviders,
  type AdminMetricsStatus,
  type ClientAppsPayload,
  type EmailAuthStatusResult,
  type RubPaymentProvidersResult,
} from "@/lib/api";
import { userFacingErrorMessage } from "@/lib/public-error-messages";
import { useCallback, useEffect, useMemo, useState } from "react";

type GateTone = "success" | "warning" | "danger" | "neutral" | "accent";

type GateItem = {
  key: string;
  label: string;
  value: string;
  detail: string;
  tone: GateTone;
};

type OperatorAction = {
  key: string;
  title: string;
  status: string;
  detail: string;
  command: string;
  tone: GateTone;
};

type ReleaseStatusCheck = {
  name?: string | null;
  status?: string | null;
  missing?: string[] | null;
  note?: string | null;
  source?: string | null;
};

type ReleaseStatusArtifact = {
  source_artifact?: string | null;
  verdict?: string | null;
  classification?: string | null;
  safe_to_publish_public_beta?: boolean | null;
  checks?: ReleaseStatusCheck[] | null;
  safe_public_claims?: string[] | null;
  unsafe_public_claims?: string[] | null;
};

const RUNTIME_SYNC_GO_TEXT = [
  "RUNTIME LINK SYNC GO FOR APP-DOWNLOAD SMOKE",
  "OPERATOR_APPROVED_RUNTIME_LINK_SYNC=true",
  "STAGED GITHUB ASSET REACHABILITY GREEN",
  "NO PUBLIC ANNOUNCEMENT",
  "PAID CHECKOUT REMAINS CLOSED",
].join("\n");

const RUNTIME_SYNC_AUDIT_TEXT = [
  "RUNTIME LINK SYNC AUDIT BEFORE ANNOUNCEMENT",
  "CONFIRM_OPERATOR_GO_WAS_EXACT=true",
  "CONFIRM_NO_PUBLIC_ANNOUNCEMENT_YET=true",
  "CONFIRM_PAID_CHECKOUT_REMAINS_CLOSED=true",
  "IF GO IS MISSING: DO NOT ANNOUNCE; ROLL BACK RUNTIME APP_* LINKS",
].join("\n");

const EMAIL_PROBE_COMMAND = [
  "python scripts\\brain_payment_email_readiness.py --brain-ip 82.21.114.104 --ssh-user root --ssh-port 29374 --post-deploy-live --email-probe-to <probe-email> --output docs\\audit-artifacts\\brain-post-deploy-live-probe-<YYYY-MM-DD>.json",
].join("\n");

const LAVATOP_PROBE_COMMAND = [
  "python scripts\\brain_payment_email_readiness.py --brain-ip 82.21.114.104 --ssh-user root --ssh-port 29374 --post-deploy-live --email-probe-to <probe-email> --lavatop-probe-email <buyer-email> --output docs\\audit-artifacts\\brain-post-deploy-live-probe-<YYYY-MM-DD>.json",
].join("\n");

const TELEGRAM_BUTTON_EMOJI_TEXT = [
  "TG_BTN_EMOJI_PRIMARY_ID=<telegram-custom-emoji-id>",
  "TG_BTN_EMOJI_SUCCESS_ID=<telegram-custom-emoji-id>",
  "TG_BTN_EMOJI_DANGER_ID=<telegram-custom-emoji-id>",
  "Material icon packs are not a Telegram Bot API field; use Telegram custom emoji document IDs only.",
  "After changing these env values: restart portal-bot, portal-helpbot, and portal-feedbackbot.",
].join("\n");

function firstUrl(...values: Array<string | null | undefined>): string {
  return values.map((value) => String(value || "").trim()).find(Boolean) || "";
}

function isGithubReleaseArtifactUrl(value: string, suffix: ".apk" | ".exe"): boolean {
  const rawUrl = String(value || "").trim();
  if (!rawUrl) return false;
  try {
    const url = new URL(rawUrl);
    const path = url.pathname.toLowerCase();
    return (
      url.protocol === "https:" &&
      url.hostname.toLowerCase() === "github.com" &&
      path.includes("/releases/download/") &&
      path.endsWith(suffix)
    );
  } catch {
    return false;
  }
}

function isInstallDocsUrl(value: string): boolean {
  const rawUrl = String(value || "").trim();
  if (!rawUrl) return false;
  try {
    const url = new URL(rawUrl);
    const path = url.pathname;
    return url.protocol === "https:" && url.hostname.toLowerCase() === "pokrov.space" && (path === "/install" || path.startsWith("/install/"));
  } catch {
    return false;
  }
}

function yesNo(value: boolean): string {
  return value ? "локально готово" : "нет подтверждения";
}

function reasonList(reasons?: string[] | null): string {
  const rows = Array.isArray(reasons) ? reasons.map((item) => String(item || "").trim()).filter(Boolean) : [];
  return rows.length ? rows.join(", ") : "причина не передана";
}

function isEmailPublicReady(email: EmailAuthStatusResult | null): boolean {
  return Boolean(
    email?.enabled &&
      email?.public_enabled &&
      email?.delivery_configured &&
      email?.delivery_secret_configured &&
      !email?.debug_echo,
  );
}

async function copyTextToClipboard(text: string): Promise<void> {
  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(text);
      return;
    } catch {
      // Fall back to the legacy selection path for hardened browser contexts.
    }
  }

  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "true");
  textarea.style.position = "fixed";
  textarea.style.left = "-9999px";
  document.body.appendChild(textarea);
  textarea.select();
  try {
    const ok = document.execCommand("copy");
    if (!ok) throw new Error("copy command failed");
  } finally {
    document.body.removeChild(textarea);
  }
}

async function fetchReleaseStatusArtifact(): Promise<ReleaseStatusArtifact | null> {
  try {
    const response = await fetch("/release-status.json", { cache: "no-store" });
    if (!response.ok) return null;
    const payload = (await response.json()) as ReleaseStatusArtifact;
    if (!payload || typeof payload !== "object") return null;
    return payload;
  } catch {
    return null;
  }
}

function artifactCheck(artifact: ReleaseStatusArtifact | null, ...names: string[]): ReleaseStatusCheck | null {
  const checks = Array.isArray(artifact?.checks) ? artifact?.checks || [] : [];
  const wanted = new Set(names.map((name) => name.toLowerCase()));
  return checks.find((check) => wanted.has(String(check?.name || "").toLowerCase())) || null;
}

function missingText(items?: string[] | null): string {
  const rows = Array.isArray(items) ? items.map((item) => String(item || "").trim()).filter(Boolean) : [];
  return rows.length ? ` Не хватает: ${rows.join(", ")}.` : "";
}

function releaseArtifactDecisionGate(artifact: ReleaseStatusArtifact | null): GateItem | null {
  if (!artifact) return null;
  const check = artifactCheck(
    artifact,
    "machine-launch-decision",
    "public_beta_handoff_policy",
    "completion_audit_verdict",
  );
  const value = String(artifact.verdict || check?.status || artifact.classification || "NO_GO").trim() || "NO_GO";
  const source = String(artifact.source_artifact || "release-status.json").trim();
  const classification = String(artifact.classification || check?.status || "unknown").trim();
  const safe = artifact.safe_to_publish_public_beta === true;
  const detail = [
    `Статус из release-status.json: ${source}.`,
    `safe_to_publish_public_beta=${safe ? "true" : "false"}, classification=${classification}.`,
    String(check?.note || "").trim(),
    missingText(check?.missing),
  ]
    .filter(Boolean)
    .join(" ");

  return {
    key: "machine-launch-decision",
    label: "Машинный launch decision",
    value,
    detail,
    tone: safe ? "success" : "danger",
  };
}

function toneForCheckStatus(status: string, fallback: GateTone): GateTone {
  const value = status.toUpperCase();
  if (value === "PASS" || value === "OK" || value === "SUCCESS") return "success";
  if (value.includes("BLOCKED") || value.includes("NO_GO") || value.includes("FAIL")) return "danger";
  if (value.includes("SKIPPED") || value.includes("ATTESTED") || value.includes("WARNING")) return "warning";
  return fallback;
}

function artifactBackedGate(
  artifact: ReleaseStatusArtifact | null,
  fallback: GateItem,
  ...checkNames: string[]
): GateItem {
  const check = artifactCheck(artifact, ...checkNames);
  if (!check) return fallback;

  const status = String(check.status || fallback.value).trim() || fallback.value;
  const note = String(check.note || "").trim();
  const source = String(check.source || "").trim();
  const detail = [
    fallback.detail,
    note,
    missingText(check.missing),
    source ? `Источник: ${source}.` : "",
  ]
    .filter(Boolean)
    .join(" ");

  return {
    ...fallback,
    value: status,
    detail,
    tone: toneForCheckStatus(status, fallback.tone),
  };
}

function buildRuntimeGates({
  apps,
  email,
  metrics,
  payments,
}: {
  apps: ClientAppsPayload | null;
  email: EmailAuthStatusResult | null;
  metrics: AdminMetricsStatus | null;
  payments: RubPaymentProvidersResult | null;
}): GateItem[] {
  const androidUrl = firstUrl(apps?.android?.apk_url, apps?.android?.mirror_url);
  const androidPlayUrl = firstUrl(apps?.android?.play_url);
  const windowsUrl = firstUrl(apps?.windows?.exe_url, apps?.windows?.mirror_url);
  const docsUrl = firstUrl(apps?.docs_url);
  const appLinksReady = Boolean(
    !androidPlayUrl &&
      isGithubReleaseArtifactUrl(androidUrl, ".apk") &&
      isGithubReleaseArtifactUrl(windowsUrl, ".exe") &&
      isInstallDocsUrl(docsUrl),
  );
  const providers = payments?.providers || [];
  const lavaOnly = Boolean(payments?.ok && providers.length === 1 && providers[0]?.code === "lavatop");
  const emailReady = isEmailPublicReady(email);
  const metricsFresh = Boolean(metrics?.status === "fresh" && !(metrics?.active_alerts || []).length);

  return [
    {
      key: "apps",
      label: "Ссылки Android и Windows",
      value: appLinksReady ? "ссылки беты подтверждены" : "нет подтверждения",
      detail: appLinksReady
        ? "API отдаёт файлы приложения из GitHub Releases, ссылку на инструкцию установки и пустую ссылку Google Play. Это подходит для беты вне магазинов; при смене файла нужна новая проверка загрузки."
        : "Нужны файлы GitHub Releases, инструкция https://pokrov.space/install/ и пустая ссылка Google Play в /api/client/apps.",
      tone: appLinksReady ? "success" : "danger",
    },
    {
      key: "payments",
      label: "Оплата Lava.top",
      value: payments?.blocked ? "закрыто" : lavaOnly ? "список открыт" : "проверить",
      detail: payments?.blocked
        ? reasonList(payments.blocked_reason_texts || payments.blocked_reasons)
        : lavaOnly
          ? "Оплата открыта и показывает только Lava.top. Для беты это подтверждено 2026-05-15; для более сильных заявлений нужны отдельные проверки возвратов, споров и сверки."
          : "Каталог оплаты не доказывает готовность режима только Lava.top.",
      tone: lavaOnly ? "success" : payments?.blocked ? "warning" : "danger",
    },
    {
      key: "email",
      label: "Email-вход и доставка ключей",
      value: yesNo(emailReady),
      detail: emailReady
        ? "Email включен, доставка настроена, отладочная отправка выключена. После деплоя всё равно нужна ручная проверка письма в реальном ящике."
        : `Email закрыт: ${reasonList(email?.blocked_reasons)}.`,
      tone: emailReady ? "success" : "warning",
    },
    {
      key: "metrics",
      label: "Метрики и тревоги",
      value: metricsFresh ? "свежие" : metrics?.status || "нет данных",
      detail: metricsFresh
        ? "Метрики админки свежие, активных тревог нет."
        : `${(metrics?.active_alerts || []).length} активных тревог, статус ${metrics?.status || "нет данных"}.`,
      tone: metricsFresh ? "success" : "warning",
    },
  ];
}

const EXTERNAL_GATES: GateItem[] = [
  {
    key: "android-physical",
    label: "Проверка Android на устройстве",
    value: "OPERATOR_ATTESTED",
    detail:
      "Проверка текущего Android-файла на устройстве принята как подтверждение оператора. Это не публикация в магазине; публично можно говорить только об операторской проверке.",
    tone: "warning",
  },
  {
    key: "lavatop-live",
    label: "Подтверждение Lava.top для беты",
    value: "PASS_FOR_BETA",
    detail: "Проверка от 2026-05-15 подтверждает создание счёта, уведомления платёжной системы, повторные события, ошибки, ручную проверку, сверку и отправку ключа по email для беты вне магазинов. Возвраты, споры и зрелая продовая сверка остаются отдельной задачей.",
    tone: "success",
  },
  {
    key: "paid-checkout-launch-evidence",
    label: "Итоговая проверка оплаты",
    value: "PASS_FOR_BETA",
    detail:
      "Последняя проверка разрешает оплату только через Lava.top для беты. При смене платёжной системы или более сильных заявлениях нужна новая датированная проверка.",
    tone: "success",
  },
  {
    key: "machine-launch-decision",
    label: "Автоматическая проверка запуска",
    value: "GO_WITH_ACCEPTED_SKIPS",
    detail:
      "Если release-status.json недоступен, админка опирается на решение от 2026-05-15: публичная бета разрешена с принятыми пропусками. Это не подтверждение боевого запуска или 1.0.0.",
    tone: "success",
  },
  {
    key: "brain-post-deploy-live-probe",
    label: "Проверка email и Lava.top с сервера",
    value: "PASS_FOR_BETA",
    detail:
      "Проверка после деплоя от 2026-05-15 зелёная для беты. Секреты остаются на сервере; при новом деплое повторять только с безопасным выводом.",
    tone: "success",
  },
  {
    key: "email-live",
    label: "Боевые подтверждения email-реле",
    value: "PASS_FOR_BETA",
    detail: "Email-вход, восстановление и доставка оплаченного ключа подтверждены для беты. Новый отправитель, домен или кандидат релиза требует новой проверки реального письма.",
    tone: "success",
  },
  {
    key: "ru-origin",
    label: "Доступность Telegram из России",
    value: "SKIPPED_BY_OPERATOR",
    detail: "Проверка из России пропущена оператором для этого прохода беты. Это не подтверждает доступность Telegram из России и не должно звучать как публичное обещание.",
    tone: "warning",
  },
  {
    key: "windows-signing",
    label: "Доверенная подпись Windows",
    value: "UNSIGNED_BETA_RISK_ACCEPTED",
    detail:
      "Подпись не требуется для этой волны вне магазинов по текущему операторскому решению. EXE может показывать предупреждение Windows о неизвестном издателе или SmartScreen; нельзя называть его доверенно подписанным.",
    tone: "warning",
  },
  {
    key: "github-release",
    label: "GitHub Releases и деплой",
    value: "PASS_FOR_BETA",
    detail:
      "GitHub prerelease v0.2.0-beta.1 и /api/client/apps подтверждены для беты вне магазинов. Telegram-анонс остаётся ручным действием владельца, не автоматическим блокером админки.",
    tone: "success",
  },
];

function buildExternalGates(artifact: ReleaseStatusArtifact | null): GateItem[] {
  const decisionGate = releaseArtifactDecisionGate(artifact);
  const brainStaticGate = artifactCheck(artifact, "brain_origin_static_deploy_verify")
    ? artifactBackedGate(
        artifact,
        {
          key: "brain-origin-static-deploy",
          label: "Статический деплой с сервера",
          value: "PASS_STATIC_CONTEXT",
          detail:
            "Проверка статического деплоя полезна как контекст, но сама по себе не разрешает заявления о боевом запуске, магазинах, доверенной подписи, доступности из России или полном Android-аудите.",
          tone: "success",
        },
        "brain_origin_static_deploy_verify",
      )
    : null;
  const externalAccessGate = artifactCheck(artifact, "external_access_preflight")
    ? artifactBackedGate(
        artifact,
        {
          key: "external-access-preflight",
          label: "Внешняя проверка доступа",
          value: "BLOCKED_BY_ACCESS",
          detail: "Внешняя проверка доступа не предназначена для публичных заявлений.",
          tone: "danger",
        },
        "external_access_preflight",
      )
    : null;

  const gates = EXTERNAL_GATES.map((gate) => {
    if (gate.key === "machine-launch-decision") return decisionGate || gate;
    if (gate.key === "lavatop-live") return artifactBackedGate(artifact, gate, "post_deploy_payment_email_probe", "lavatop_live_invoice_creation");
    if (gate.key === "paid-checkout-launch-evidence") return artifactBackedGate(artifact, gate, "paid_checkout_launch_evidence");
    if (gate.key === "brain-post-deploy-live-probe") return artifactBackedGate(artifact, gate, "post_deploy_payment_email_probe");
    if (gate.key === "email-live") return artifactBackedGate(artifact, gate, "post_deploy_payment_email_probe", "email_delivery_verify", "email_delivery_payment_access_key");
    if (gate.key === "github-release") return artifactBackedGate(artifact, gate, "staged_client_apps_reachability", "runtime_app_download_smoke");
    return gate;
  });

  const machineIndex = gates.findIndex((gate) => gate.key === "machine-launch-decision");
  const insertAt = machineIndex >= 0 ? machineIndex + 1 : 0;
  const dynamicGates = [brainStaticGate, externalAccessGate].filter((gate): gate is GateItem => Boolean(gate));
  if (!dynamicGates.length) return gates;
  return [...gates.slice(0, insertAt), ...dynamicGates, ...gates.slice(insertAt)];
}

function GateCard({ gate }: { gate: GateItem }) {
  return (
    <article className={adminPanelClass(gate.tone)}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[color:var(--atlas-text-soft)]">{gate.label}</p>
          <h3 className="mt-2 text-base font-semibold text-[color:var(--atlas-text)]">{gate.value}</h3>
        </div>
        <AdminBadge tone={gate.tone}>{gate.tone === "success" ? "готово" : gate.tone === "warning" ? "проверить" : "блок"}</AdminBadge>
      </div>
      <p className="mt-3 text-sm leading-6 text-[color:var(--atlas-text-soft)]">{gate.detail}</p>
    </article>
  );
}

function OperatorActionCard({ action }: { action: OperatorAction }) {
  const [copied, setCopied] = useState(false);
  const [copyError, setCopyError] = useState("");

  const copyCommand = async (): Promise<void> => {
    setCopyError("");
    try {
      await copyTextToClipboard(action.command);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      setCopied(false);
      setCopyError("Не удалось скопировать автоматически. Текст можно выделить вручную.");
    }
  };

  return (
    <article className={adminPanelClass(action.tone)}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[color:var(--atlas-text-soft)]">{action.title}</p>
          <h3 className="mt-2 text-base font-semibold text-[color:var(--atlas-text)]">{action.status}</h3>
        </div>
        <div className="flex shrink-0 flex-col items-end gap-2">
          <AdminBadge tone={action.tone}>{action.tone === "success" ? "готово" : "нужно"}</AdminBadge>
          <button
            type="button"
            className={adminButtonClass("secondary", "xs")}
            onClick={() => void copyCommand()}
            aria-label={`Скопировать ${action.title}`}
          >
            {copied ? "Скопировано" : "Скопировать"}
          </button>
        </div>
      </div>
      <p className="mt-3 text-sm leading-6 text-[color:var(--atlas-text-soft)]">{action.detail}</p>
      <pre className="mt-3 overflow-x-auto rounded-[0.9rem] border border-[color:var(--atlas-border)] bg-slate-950 p-3 text-xs leading-5 text-slate-100">
        <code>{action.command}</code>
      </pre>
      {copyError ? <p className="mt-2 text-xs text-[color:var(--atlas-status-danger-text)]">{copyError}</p> : null}
    </article>
  );
}

export default function AdminReleasePage() {
  const [apps, setApps] = useState<ClientAppsPayload | null>(null);
  const [emailRaw, setEmail] = useState<EmailAuthStatusResult | null>(null);
  const [metrics, setMetrics] = useState<AdminMetricsStatus | null>(null);
  const [payments, setPayments] = useState<RubPaymentProvidersResult | null>(null);
  const [releaseStatus, setReleaseStatus] = useState<ReleaseStatusArtifact | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [appsPayload, emailPayload, metricsPayload, paymentPayload, releaseStatusPayload] = await Promise.all([
        fetchClientApps(),
        getEmailAuthStatus(),
        adminMetricsStatus(),
        getRubPaymentProviders(),
        fetchReleaseStatusArtifact(),
      ]);
      setApps(appsPayload);
      setEmail(emailPayload);
      setMetrics(metricsPayload);
      setPayments(paymentPayload);
      setReleaseStatus(releaseStatusPayload);
    } catch (nextError) {
      setError(userFacingErrorMessage(nextError, "Не удалось загрузить релизный экран."));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const email = useMemo(() => {
    if (!emailRaw || isEmailPublicReady(emailRaw)) return emailRaw;
    return { ...emailRaw, enabled: false };
  }, [emailRaw]);
  const runtimeGates = useMemo(() => buildRuntimeGates({ apps, email, metrics, payments }), [apps, email, metrics, payments]);
  const externalGates = useMemo(() => buildExternalGates(releaseStatus), [releaseStatus]);
  const runtimeBlocks = runtimeGates.filter((gate) => gate.tone === "danger").length;
  const runtimeLinksDetected = runtimeGates.find((gate) => gate.key === "apps")?.value.startsWith("ссылки беты") || false;
  const externalBlocks = externalGates.filter((gate) => gate.tone === "danger").length;
  const publicGo = runtimeBlocks === 0 && externalBlocks === 0;
  const androidUrl = firstUrl(apps?.android?.apk_url, apps?.android?.mirror_url);
  const androidPlayUrl = firstUrl(apps?.android?.play_url);
  const windowsUrl = firstUrl(apps?.windows?.exe_url, apps?.windows?.mirror_url);
  const androidUrlReady = isGithubReleaseArtifactUrl(androidUrl, ".apk") && !androidPlayUrl;
  const windowsUrlReady = isGithubReleaseArtifactUrl(windowsUrl, ".exe");
  const emailPublicReady = isEmailPublicReady(email);
  const artifactSafeClaims = Array.isArray(releaseStatus?.safe_public_claims)
    ? releaseStatus.safe_public_claims.map((claim) => String(claim || "").trim()).filter(Boolean)
    : [];
  const artifactUnsafeClaims = Array.isArray(releaseStatus?.unsafe_public_claims)
    ? releaseStatus.unsafe_public_claims.map((claim) => String(claim || "").trim()).filter(Boolean)
    : [];
  const safePublicClaims = artifactSafeClaims.length
    ? artifactSafeClaims
    : [
        "POKROV готовит ограниченную бету Android и Windows вне магазинов.",
        "POKROV открыт в публичной бете вне магазинов по проверке от 2026-05-15.",
        runtimeLinksDetected
          ? "Файлы GitHub Releases найдены в /api/client/apps; при смене ссылок нужна новая проверка загрузки."
          : "Файлы GitHub prerelease подготовлены для проверки; рабочие ссылки пока не активны.",
        "Android-кандидат принят как операторски подтверждённый, Windows-файл остаётся неподписанным бета-файлом.",
        "Оплата работает через Lava.top для текущей беты; зрелая продовая оплата всё ещё требует отдельной проверки возвратов, споров и сверки.",
        "Email-вход и доставка ключей подтверждены для беты; новый отправитель или деплой требует новой проверки реального письма.",
      ];
  const unsafePublicClaims = artifactUnsafeClaims.length
    ? artifactUnsafeClaims
    : [
        "POKROV уже готов к стабильной версии 1.0.0.",
        "Оплата Lava.top полностью готова для боевого запуска без дополнительных проверок возвратов, споров и сверки.",
        "Полная проверка Android-файла или магазинная публикация уже разрешена.",
        "Windows подписан доверенным сертификатом.",
        runtimeLinksDetected
          ? "Рабочие ссылки обнаружены, значит можно отправлять публичный анонс без финального подтверждения владельца."
          : "GitHub Releases уже являются рабочим путем загрузки в приложении или кабинете.",
      ];
  const operatorActions: OperatorAction[] = [
    runtimeLinksDetected
      ? {
          key: "runtime-links-detected",
          title: "Рабочие ссылки приложения",
          status: "обнаружены для беты",
          detail:
            "API уже отдаёт файлы GitHub Releases и инструкцию установки. Перед новым анонсом или заменой файла проверьте, что ссылки открываются и скачивание работает.",
          command: RUNTIME_SYNC_AUDIT_TEXT,
          tone: "warning",
        }
      : {
          key: "runtime-link-go",
          title: "Рабочие ссылки приложения",
          status: "нужен явный GO",
          detail:
            "Чтобы включить файлы приложения в /api/client/apps, оператор должен явно подтвердить действие. Это не открывает оплату и не разрешает публичный анонс.",
          command: RUNTIME_SYNC_GO_TEXT,
          tone: "warning",
        },
    {
      key: "email-probe",
      title: "Email-доставка",
      status: emailPublicReady ? "для беты подтверждено" : "сначала включить публичный email",
      detail:
        "Для текущей беты проверка есть. После нового деплоя, смены отправителя или кандидата релиза нужен безопасный адрес для проверки входа, восстановления и письма с тестовым ключом.",
      command: EMAIL_PROBE_COMMAND,
      tone: emailPublicReady ? "success" : "warning",
    },
    {
      key: "lavatop-probe",
      title: "Lava.top",
      status: "для беты подтверждено",
      detail:
        "Оплата открыта для текущей беты. Новое сильное заявление, смена платёжной системы или кандидат релиза требуют новой проверки Lava.top: счёт, уведомления, повторы, ошибки, ручная проверка, сверка и доставка ключа по email.",
      command: LAVATOP_PROBE_COMMAND,
      tone: "success",
    },
    {
      key: "telegram-buttons",
      title: "Telegram-кнопки",
      status: "опциональная полировка",
      detail:
        "Код уже использует текущие поля Telegram-кнопок: style, icon_custom_emoji_id и copy_text. Для кастом-иконок нужны Telegram custom emoji document IDs; arbitrary Material icon packs не являются полем Bot API и не должны блокировать запуск.",
      command: TELEGRAM_BUTTON_EMOJI_TEXT,
      tone: "neutral",
    },
  ];

  if (loading) {
    return (
      <section className="space-y-4" aria-busy="true" aria-live="polite">
        <div className="h-40 animate-pulse rounded-[1rem] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)]" />
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className="h-28 animate-pulse rounded-[1rem] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)]" />
          ))}
        </div>
      </section>
    );
  }

  return (
    <section className="space-y-4">
      <article className={adminPanelClass(publicGo ? "success" : "danger")}>
        <AdminPanelHeader
          eyebrow="релиз"
          title={publicGo ? "Публичная бета: можно выпускать" : "Публичная бета: требует внимания"}
          description="Один экран для проверки текущей беты. GO относится только к публичной бете вне магазинов; боевой запуск, 1.0.0, магазины, доверенная подпись, полный Android-аудит и доступность из России остаются отдельными ручными проверками."
          actions={
            <button type="button" onClick={() => void load()} className={adminButtonClass("secondary", "sm")}>
              Обновить
            </button>
          }
        />
        <div className="flex flex-wrap gap-2">
          <AdminBadge tone={runtimeBlocks ? "warning" : "success"}>что проверяет админка: {runtimeBlocks}</AdminBadge>
          <AdminBadge tone={externalBlocks ? "danger" : "success"}>что проверяется вручную: {externalBlocks}</AdminBadge>
          <AdminBadge tone="warning">
            {runtimeLinksDetected ? "Рабочие ссылки беты обнаружены" : "Рабочие ссылки не обнаружены"}
          </AdminBadge>
          <AdminBadge tone="warning">Telegram пост — ручное действие владельца</AdminBadge>
        </div>
      </article>

      {error ? (
        <AdminEmptyState
          title="Релизный экран не загрузился"
          description={error}
        />
      ) : null}

      <AdminMetricStrip
        items={[
          {
            label: "Android ссылка",
            value: androidUrlReady ? "есть" : "нет",
            hint: androidUrlReady
              ? androidUrl
              : androidPlayUrl
                ? "Android Play URL должен оставаться пустым для беты вне магазинов."
                : androidUrl
                  ? "Android ссылка должна быть GitHub Releases .apk."
                  : "API не отдал GitHub Releases APK или запасную ссылку.",
            tone: androidUrlReady ? "success" : "danger",
          },
          {
            label: "Windows ссылка",
            value: windowsUrlReady ? "есть" : "нет",
            hint: windowsUrlReady ? windowsUrl : windowsUrl ? "Windows ссылка должна быть GitHub Releases .exe." : "API не отдал GitHub Releases EXE или запасную ссылку.",
            tone: windowsUrlReady ? "success" : "danger",
          },
          {
            label: "Оплата",
            value: payments?.ok ? "каталог найден" : "закрыто",
            hint: payments?.ok
              ? `платёжные системы: ${(payments.providers || []).map((provider) => provider.code).join(", ")}; для беты разрешена только Lava.top, продовая проверка остаётся отдельной задачей.`
              : reasonList(payments?.blocked_reason_texts || payments?.blocked_reasons),
            tone: payments?.ok ? "warning" : "warning",
          },
          {
            label: "Telegram Stars",
            value: "выключено по политике",
            hint: "Оплата Telegram Stars выключена по политике этой беты. Публичная оплата идёт через Lava.top. Подарочные коды можно только активировать.",
            tone: "success",
          },
          {
            label: "Email",
            value: email?.enabled ? "локально проверено" : "закрыто",
            hint: email?.enabled ? "режим включён; после деплоя нужна проверка реального письма." : reasonList(email?.blocked_reasons),
            tone: email?.enabled ? "warning" : "warning",
          },
        ]}
      />

      <section className={adminPanelClass("accent")}>
        <AdminPanelHeader
          eyebrow="следующие действия"
          title="Что нужно от оператора"
          description="Короткий список ручных проверок для нового деплоя, нового кандидата или более сильных публичных заявлений. Они не закрываются агентом и не должны превращаться в скрытый блокер текущей беты."
        />
        <div className="grid gap-3 xl:grid-cols-4">
          {operatorActions.map((action) => (
            <OperatorActionCard key={action.key} action={action} />
          ))}
        </div>
      </section>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr),minmax(360px,0.72fr)]">
        <section className={adminPanelClass("neutral")}>
          <AdminPanelHeader
            eyebrow="локальные проверки"
            title="Что можно проверить из админки"
            description="Эти пункты берутся из боевых API-ответов текущего окружения. Зеленые локальные проверки не заменяют аудит Android-файла, подтверждения Lava.top и проверку публикации GitHub."
          />
          <div className="grid gap-3 md:grid-cols-2">
            {runtimeGates.map((gate) => (
              <GateCard key={gate.key} gate={gate} />
            ))}
          </div>
        </section>

        <section className={adminPanelClass("neutral")}>
          <AdminPanelHeader
            eyebrow="внешние подтверждения"
            title="Блокеры вне браузера"
            description="Эти проверки не закрываются самим WebApp. Их нельзя заменить зеленым билдом или моками."
          />
          <div className="space-y-3">
            {externalGates.map((gate) => (
              <GateCard key={gate.key} gate={gate} />
            ))}
          </div>
        </section>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <section className={adminPanelClass("success")}>
          <AdminPanelHeader
            eyebrow="можно говорить"
            title="Что можно говорить публично"
            description="Только бета вне магазинов, оплата Lava.top для беты и явно обозначенные ограничения. Без заявлений о боевом запуске, магазинах, доверенной подписи, полном Android-аудите и доступности из России."
          />
          <div className="space-y-2">
            {safePublicClaims.map((claim) => (
              <p key={claim} className={adminInsetPanelClass}>{claim}</p>
            ))}
          </div>
        </section>

        <section className={adminPanelClass("danger")}>
          <AdminPanelHeader
            eyebrow="нельзя говорить"
            title="Что нельзя публиковать"
            description="Эти формулировки запрещены до отдельных подтверждений по боевому запуску, магазинам, доверенной подписи, России и полной проверке на устройстве."
          />
          <div className="space-y-2">
            {unsafePublicClaims.map((claim) => (
              <p key={claim} className={adminInsetPanelClass}>{claim}</p>
            ))}
          </div>
        </section>
      </div>

      <section className={adminPanelClass("accent")}>
        <AdminPanelHeader
            eyebrow="рабочие экраны"
          title="Соседние рабочие экраны"
          description="Экран выпуска только фиксирует статус. Ручные разборы остаются в профильных разделах админки."
          actions={
            <>
              <AppRouteLink href="/admin/payments" className={adminButtonClass("secondary", "sm")}>
                Платежи
              </AppRouteLink>
              <AppRouteLink href="/admin/promos" className={adminButtonClass("secondary", "sm")}>
                Ключи и промо
              </AppRouteLink>
              <AppRouteLink href="/admin/nodes" className={adminButtonClass("secondary", "sm")}>
                Ноды
              </AppRouteLink>
              <AppRouteLink href="/admin/tickets" className={adminButtonClass("secondary", "sm")}>
                Обращения
              </AppRouteLink>
            </>
          }
        />
      </section>
    </section>
  );
}
