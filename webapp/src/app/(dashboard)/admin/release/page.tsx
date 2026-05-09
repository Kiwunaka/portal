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
      label: "Android и Windows ссылки",
      value: appLinksReady ? "ссылки обнаружены; нужен GO-аудит" : "нет подтверждения",
      detail: appLinksReady
        ? "Backend отдает GitHub Releases APK/EXE, install docs URL, Android Play URL пустой. Наличие ссылок не доказывает, что был явный runtime-sync GO; перед анонсом нужен audit handoff."
        : "Нужны GitHub Releases APK/EXE, docs URL https://pokrov.space/install/ и пустой Android Play URL в /api/client/apps.",
      tone: appLinksReady ? "warning" : "danger",
    },
    {
      key: "payments",
      label: "Гейт оплаты Lava.top",
      value: lavaOnly ? "каталог найден; checkout закрыт" : payments?.blocked ? "закрыто" : "проверить",
      detail: lavaOnly
        ? "Каталог оплаты показывает только Lava.top, но это не live payment proof. Боевой прогон возможен только после deploy и probe-buyer; checkout остается закрытым до invoice/webhook/replay/failure/manual-review/reconciliation и email-key evidence."
        : payments?.blocked
          ? reasonList(payments.blocked_reason_texts || payments.blocked_reasons)
          : "Каталог оплаты не доказывает готовность режима только Lava.top.",
      tone: lavaOnly ? "warning" : payments?.blocked ? "warning" : "danger",
    },
    {
      key: "email",
      label: "Email-вход и доставка ключей",
      value: yesNo(emailReady),
      detail: emailReady
        ? "Runtime-конфиг email зеленый: public mode включен, доставка настроена, debug echo выключен. Боевой inbox smoke verify/reset/key delivery остается post-deploy проверкой."
        : `Email-гейт закрыт: ${reasonList(email?.blocked_reasons)}.`,
      tone: emailReady ? "success" : "warning",
    },
    {
      key: "metrics",
      label: "Метрики и алерты",
      value: metricsFresh ? "свежие" : metrics?.status || "нет данных",
      detail: metricsFresh
        ? "Метрики админки свежие, активных алертов нет."
        : `${(metrics?.active_alerts || []).length} активных алертов, статус ${metrics?.status || "нет данных"}.`,
      tone: metricsFresh ? "success" : "warning",
    },
  ];
}

const EXTERNAL_GATES: GateItem[] = [
  {
    key: "android-physical",
    label: "Физический аудит Android-сборки",
    value: "OPERATOR_ATTESTED",
    detail:
      "Физическая проверка текущего Android-кандидата принята как операторская аттестация. Это не raw repo validation и не магазинная публикация; публично можно говорить только об операторском подтверждении.",
    tone: "warning",
  },
  {
    key: "lavatop-live",
    label: "Боевые подтверждения Lava.top",
    value: "BLOCKED_BY_ACCESS",
    detail: "Нужны post-deploy создание счета, проверка вебхука, повторная доставка/идемпотентность, неуспешный платеж и сверка.",
    tone: "danger",
  },
  {
    key: "paid-checkout-launch-evidence",
    label: "Агрегированный гейт оплаты",
    value: "BLOCKED_BY_ACCESS",
    detail:
      "Последний retained paid-checkout evidence держит оплату закрытой: нет полного redacted evidence по invoice, success webhook, replay, failure/manual-review, reconciliation и email-доставке ключа. При новой проверке нужен свежий датированный artifact.",
    tone: "danger",
  },
  {
    key: "machine-launch-decision",
    label: "Машинный launch decision",
    value: "NO_GO",
    detail:
      "Последний retained launch decision: safe_to_publish_public_beta=false, post_deploy_payment_email_probe=BLOCKED_BY_ACCESS. Зеленый email runtime не заменяет inbox proof, Lava.top invoice proof и финальный GO; после новых probes нужен новый decision artifact.",
    tone: "danger",
  },
  {
    key: "brain-post-deploy-live-probe",
    label: "Brain-local email/Lava.top probe",
    value: "BLOCKED_BY_ACCESS",
    detail:
      "Последний retained brain-local probe дошел до brain и runtime env, но остановился без отправки писем и invoice: после deploy нужны безопасные email_probe_to и lavatop_probe_email. Секреты остаются на brain, наружу должен идти только redacted HTTP-status.",
    tone: "danger",
  },
  {
    key: "email-live",
    label: "Боевые подтверждения email-реле",
    value: "BLOCKED_BY_ACCESS",
    detail: "Нужна доказанная доставка писем входа/восстановления и оплаченного ключа доступа.",
    tone: "danger",
  },
  {
    key: "ru-origin",
    label: "Доступность Telegram из RU-origin",
    value: "SKIPPED_BY_OPERATOR",
    detail: "RU-origin проверка пропущена оператором для этого beta-прохода. Это не подтверждает доступность Telegram из RU-origin и не должно звучать как публичное обещание.",
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
    value: "PUBLISHED_PRERELEASE_STAGING",
    detail:
      "GitHub prerelease v0.2.0-beta.1 опубликован для проверки, APK/EXE доступны в staged-проверке. Синхронизация Runtime APP_* требует явного разрешения на runtime sync, затем нужна контрольная проверка /api/client/apps; Telegram-анонс всё ещё заблокирован до финального GO.",
    tone: "warning",
  },
];

function buildExternalGates(artifact: ReleaseStatusArtifact | null): GateItem[] {
  const decisionGate = releaseArtifactDecisionGate(artifact);
  if (!decisionGate) return EXTERNAL_GATES;
  return EXTERNAL_GATES.map((gate) => (gate.key === "machine-launch-decision" ? decisionGate : gate));
}

function GateCard({ gate }: { gate: GateItem }) {
  return (
    <article className={adminPanelClass(gate.tone)}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">{gate.label}</p>
          <h3 className="mt-2 text-base font-semibold text-slate-900">{gate.value}</h3>
        </div>
        <AdminBadge tone={gate.tone}>{gate.tone === "success" ? "готово" : gate.tone === "warning" ? "проверить" : "блок"}</AdminBadge>
      </div>
      <p className="mt-3 text-sm leading-6 text-slate-600">{gate.detail}</p>
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
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">{action.title}</p>
          <h3 className="mt-2 text-base font-semibold text-slate-900">{action.status}</h3>
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
      <p className="mt-3 text-sm leading-6 text-slate-600">{action.detail}</p>
      <pre className="mt-3 overflow-x-auto rounded-[0.9rem] border border-slate-200/70 bg-slate-950 p-3 text-xs leading-5 text-slate-100">
        <code>{action.command}</code>
      </pre>
      {copyError ? <p className="mt-2 text-xs text-rose-700">{copyError}</p> : null}
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
  const runtimeBlocks = runtimeGates.filter((gate) => gate.tone !== "success").length;
  const runtimeLinksDetected = runtimeGates.find((gate) => gate.key === "apps")?.value.startsWith("ссылки обнаружены") || false;
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
        "POKROV готовит ограниченную Android и Windows бета вне магазинов.",
        runtimeLinksDetected
          ? "GitHub Releases APK/EXE обнаружены в runtime /api/client/apps; публичный анонс все еще ждет подтвержденный runtime-sync GO и финальный GO."
          : "GitHub prerelease assets подготовлены для проверки; runtime-ссылки пока не активны.",
        "Android-кандидат принят как операторски подтвержденный, Windows EXE остается неподписанной бета-сборкой.",
        "Оплата остается закрытой до post-deploy подтверждений Lava.top и доставки ключей по email.",
        "Email-вход можно оставлять публичным только при подтвержденной доставке писем.",
      ];
  const unsafePublicClaims = artifactUnsafeClaims.length
    ? artifactUnsafeClaims
    : [
        "Публичная бета уже запущена.",
        "Оплата Lava.top работает в бою.",
        "Android raw repo validation green или магазинная публикация уже разрешена.",
        "Windows подписан доверенным сертификатом.",
        runtimeLinksDetected
          ? "Runtime-ссылки обнаружены, значит можно отправлять публичный анонс без подтвержденного sync GO и финального GO."
          : "GitHub Releases уже являются рабочим путем загрузки в приложении или кабинете.",
      ];
  const operatorActions: OperatorAction[] = [
    runtimeLinksDetected
      ? {
          key: "runtime-links-detected",
          title: "Runtime APP-ссылки",
          status: "обнаружены; проверьте GO",
          detail:
            "Backend уже отдает GitHub APK/EXE и install docs, но WebApp не может доказать, что sync был разрешен. Перед анонсом проверьте exact runtime-link GO в handoff; если GO нет, не анонсируйте и откатите APP_* ссылки.",
          command: RUNTIME_SYNC_AUDIT_TEXT,
          tone: "warning",
        }
      : {
          key: "runtime-link-go",
          title: "Runtime APP-ссылки",
          status: "нужен явный GO",
          detail:
            "Чтобы включить APK/EXE в runtime /api/client/apps, оператор должен прислать этот narrow GO. Это не открывает оплату и не разрешает публичный анонс.",
          command: RUNTIME_SYNC_GO_TEXT,
          tone: "warning",
        },
    {
      key: "email-probe",
      title: "Email-доставка",
      status: emailPublicReady ? "нужен probe-ящик" : "сначала включить public email",
      detail:
        "После deploy нужен безопасный адрес, на который можно отправить verify/reset и письмо с тестовым ключом. Без inbox-подтверждения email остается внешним блокером.",
      command: EMAIL_PROBE_COMMAND,
      tone: emailPublicReady ? "warning" : "danger",
    },
    {
      key: "lavatop-probe",
      title: "Lava.top",
      status: "нужна живая проверка",
      detail:
        "Оплата остается закрытой. После deploy нужен живой Lava.top-прогон: invoice creation, webhook auth, replay/idempotency, failed/manual-review, reconciliation и email key delivery evidence.",
      command: LAVATOP_PROBE_COMMAND,
      tone: "danger",
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
        <div className="h-40 animate-pulse rounded-[1rem] border border-slate-200 bg-white/70" />
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className="h-28 animate-pulse rounded-[1rem] border border-slate-200 bg-white/70" />
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
          title={publicGo ? "Публичная бета: GO" : "Публичная бета: NO-GO"}
          description="Один экран для операторской проверки перед включением рабочих ссылок и анонсом. GitHub prerelease сейчас staging-only; публичная выдача остается закрытой, пока внешние подтверждения не станут зелеными."
          actions={
            <button type="button" onClick={() => void load()} className={adminButtonClass("secondary", "sm")}>
              Обновить
            </button>
          }
        />
        <div className="flex flex-wrap gap-2">
          <AdminBadge tone={runtimeBlocks ? "warning" : "success"}>локальные блокеры: {runtimeBlocks}</AdminBadge>
          <AdminBadge tone={externalBlocks ? "danger" : "success"}>внешние блокеры: {externalBlocks}</AdminBadge>
          <AdminBadge tone="warning">
            {runtimeLinksDetected ? "Runtime-ссылки требуют GO-аудит" : "Runtime-ссылки не синкать"}
          </AdminBadge>
          <AdminBadge tone="warning">Telegram пост не отправлять</AdminBadge>
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
                  : "Backend не отдал GitHub Releases APK или mirror ссылку.",
            tone: androidUrlReady ? "success" : "danger",
          },
          {
            label: "Windows ссылка",
            value: windowsUrlReady ? "есть" : "нет",
            hint: windowsUrlReady ? windowsUrl : windowsUrl ? "Windows ссылка должна быть GitHub Releases .exe." : "Backend не отдал GitHub Releases EXE или mirror ссылку.",
            tone: windowsUrlReady ? "success" : "danger",
          },
          {
            label: "Оплата",
            value: payments?.ok ? "каталог найден" : "закрыто",
            hint: payments?.ok ? `провайдеры: ${(payments.providers || []).map((provider) => provider.code).join(", ")}; checkout закрыт до post-deploy подтверждений Lava.top.` : reasonList(payments?.blocked_reasons),
            tone: payments?.ok ? "warning" : "warning",
          },
          {
            label: "Telegram Stars",
            value: "выключено по политике",
            hint: "BOT_STARS_PAYMENTS_ENABLED=false; после GO единственный публичный платежный маршрут — Lava.top. Сейчас оплата закрыта, подарочные коды можно только активировать.",
            tone: "success",
          },
          {
            label: "Email runtime",
            value: email?.enabled ? "локально проверено" : "закрыто",
            hint: email?.enabled ? "режим включен; боевой гейт ниже остается закрыт до post-deploy inbox smoke." : reasonList(email?.blocked_reasons),
            tone: email?.enabled ? "warning" : "warning",
          },
        ]}
      />

      <section className={adminPanelClass("accent")}>
        <AdminPanelHeader
          eyebrow="следующие действия"
          title="Что нужно от оператора"
          description="Короткий список входов, без которых релизный экран честно остается NO-GO. Команды и маркеры не содержат секретов; email/probe-buyer адреса подставляются вручную после deploy."
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
            description="Эти пункты берутся из боевых API-ответов текущего окружения. Зеленые локальные проверки не заменяют аудит Android-сборки, подтверждения Lava.top и гейт публикации GitHub."
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
            description="Только аккуратная подготовка беты, локальные инженерные сборки и закрытая оплата до подтверждений."
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
            description="Эти формулировки запрещены до GO-handoff и зеленых P0-подтверждений."
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
          description="Релизный экран только фиксирует статус. Ручные разборы остаются в профильных admin-разделах."
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
