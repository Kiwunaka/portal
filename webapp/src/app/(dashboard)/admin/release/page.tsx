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

const RUNTIME_SYNC_GO_TEXT = [
  "RUNTIME LINK SYNC GO FOR APP-DOWNLOAD SMOKE",
  "OPERATOR_APPROVED_RUNTIME_LINK_SYNC=true",
  "STAGED GITHUB ASSET REACHABILITY GREEN",
  "NO PUBLIC ANNOUNCEMENT",
  "PAID CHECKOUT REMAINS CLOSED",
].join("\n");

const EMAIL_PROBE_COMMAND = [
  "python scripts\\brain_payment_email_readiness.py --brain-ip 82.21.114.104 --ssh-user root --ssh-port 29374 --post-deploy-live --email-probe-to <probe-email> --output docs\\audit-artifacts\\brain-post-deploy-live-probe-2026-05-08.json",
].join("\n");

const LAVATOP_PROBE_COMMAND = [
  "python scripts\\brain_payment_email_readiness.py --brain-ip 82.21.114.104 --ssh-user root --ssh-port 29374 --post-deploy-live --email-probe-to <probe-email> --lavatop-probe-email <buyer-email> --output docs\\audit-artifacts\\brain-post-deploy-live-probe-2026-05-08.json",
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
      value: yesNo(appLinksReady),
      detail: appLinksReady
        ? "Backend отдает GitHub Releases APK/EXE, install docs URL, Android Play URL пустой."
        : "Нужны GitHub Releases APK/EXE, docs URL https://pokrov.space/install/ и пустой Android Play URL в /api/client/apps.",
      tone: appLinksReady ? "success" : "danger",
    },
    {
      key: "payments",
      label: "Гейт оплаты Lava.top",
      value: lavaOnly ? "Lava.top в каталоге" : payments?.blocked ? "закрыто" : "проверить",
      detail: lavaOnly
        ? "Каталог оплаты показывает только Lava.top; боевые подтверждения оплаты все еще проверяются ниже."
        : payments?.blocked
          ? reasonList(payments.blocked_reason_texts || payments.blocked_reasons)
          : "Каталог оплаты не доказывает готовность режима только Lava.top.",
      tone: lavaOnly ? "success" : payments?.blocked ? "warning" : "danger",
    },
    {
      key: "email",
      label: "Email-вход и доставка ключей",
      value: yesNo(emailReady),
      detail: emailReady
        ? "Публичный email-режим включен, доставка настроена, debug echo выключен; боевую доставку писем все еще нужно подтвердить ниже."
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
    detail: "Нужны создание счета, проверка вебхука, повторная доставка/идемпотентность, неуспешный платеж и сверка.",
    tone: "danger",
  },
  {
    key: "paid-checkout-launch-evidence",
    label: "Агрегированный гейт оплаты",
    value: "BLOCKED_BY_ACCESS",
    detail:
      "paid-checkout-launch-evidence-brain-2026-05-08.json держит оплату закрытой: нет полного redacted evidence по invoice, success webhook, replay, failure/manual-review, reconciliation и email-доставке ключа.",
    tone: "danger",
  },
  {
    key: "machine-launch-decision",
    label: "Машинный launch decision",
    value: "NO_GO",
    detail:
      "public-beta-launch-decision-2026-05-08.json: safe_to_publish_public_beta=false, post_deploy_payment_email_probe=BLOCKED_BY_ACCESS. Зеленый email runtime не заменяет inbox proof, Lava.top invoice proof и финальный GO.",
    tone: "danger",
  },
  {
    key: "brain-post-deploy-live-probe",
    label: "Brain-local email/Lava.top probe",
    value: "BLOCKED_BY_ACCESS",
    detail:
      "brain-post-deploy-live-probe-2026-05-08.json дошел до brain и runtime env, но остановился без отправки писем и invoice: нужны безопасные email_probe_to и lavatop_probe_email. Секреты остаются на brain, наружу должен идти только redacted HTTP-status.",
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
      "Подпись не требуется для этой волны вне магазинов по операторскому решению 2026-05-08. EXE может показывать предупреждение Windows о неизвестном издателе или SmartScreen; нельзя называть его доверенно подписанным.",
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
  return (
    <article className={adminPanelClass(action.tone)}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">{action.title}</p>
          <h3 className="mt-2 text-base font-semibold text-slate-900">{action.status}</h3>
        </div>
        <AdminBadge tone={action.tone}>{action.tone === "success" ? "готово" : "нужно"}</AdminBadge>
      </div>
      <p className="mt-3 text-sm leading-6 text-slate-600">{action.detail}</p>
      <pre className="mt-3 overflow-x-auto rounded-[0.9rem] border border-slate-200/70 bg-slate-950 p-3 text-xs leading-5 text-slate-100">
        <code>{action.command}</code>
      </pre>
    </article>
  );
}

export default function AdminReleasePage() {
  const [apps, setApps] = useState<ClientAppsPayload | null>(null);
  const [emailRaw, setEmail] = useState<EmailAuthStatusResult | null>(null);
  const [metrics, setMetrics] = useState<AdminMetricsStatus | null>(null);
  const [payments, setPayments] = useState<RubPaymentProvidersResult | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [appsPayload, emailPayload, metricsPayload, paymentPayload] = await Promise.all([
        fetchClientApps(),
        getEmailAuthStatus(),
        adminMetricsStatus(),
        getRubPaymentProviders(),
      ]);
      setApps(appsPayload);
      setEmail(emailPayload);
      setMetrics(metricsPayload);
      setPayments(paymentPayload);
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
  const runtimeBlocks = runtimeGates.filter((gate) => gate.tone !== "success").length;
  const runtimeLinksReady = runtimeGates.find((gate) => gate.key === "apps")?.tone === "success";
  const externalBlocks = EXTERNAL_GATES.filter((gate) => gate.tone === "danger").length;
  const publicGo = runtimeBlocks === 0 && externalBlocks === 0;
  const androidUrl = firstUrl(apps?.android?.apk_url, apps?.android?.mirror_url);
  const androidPlayUrl = firstUrl(apps?.android?.play_url);
  const windowsUrl = firstUrl(apps?.windows?.exe_url, apps?.windows?.mirror_url);
  const androidUrlReady = isGithubReleaseArtifactUrl(androidUrl, ".apk") && !androidPlayUrl;
  const windowsUrlReady = isGithubReleaseArtifactUrl(windowsUrl, ".exe");
  const emailPublicReady = isEmailPublicReady(email);
  const operatorActions: OperatorAction[] = [
    runtimeLinksReady
      ? {
          key: "runtime-links-live",
          title: "Runtime APP-ссылки",
          status: "уже live",
          detail:
            "Backend уже отдает GitHub APK/EXE и install docs. Новый sync нужен только при смене release-кандидата.",
          command: "ДЕЙСТВИЙ НЕ НУЖНО: runtime-ссылки уже активны для текущего релиз-кандидата.",
          tone: "success",
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
        "Нужен безопасный адрес, на который можно отправить verify/reset и письмо с тестовым ключом. Без inbox-подтверждения email остается внешним блокером.",
      command: EMAIL_PROBE_COMMAND,
      tone: emailPublicReady ? "warning" : "danger",
    },
    {
      key: "lavatop-probe",
      title: "Lava.top",
      status: "нужна живая проверка",
      detail:
        "Оплата остается закрытой, пока не будет invoice creation, webhook auth, replay/idempotency, failed/manual-review, reconciliation и email key delivery evidence.",
      command: LAVATOP_PROBE_COMMAND,
      tone: "danger",
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
          <AdminBadge tone={runtimeLinksReady ? "success" : "warning"}>
            {runtimeLinksReady ? "Runtime-ссылки активны" : "Runtime-ссылки не синкать"}
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
            value: payments?.ok ? "локально проверено" : "закрыто",
            hint: payments?.ok ? `провайдеры: ${(payments.providers || []).map((provider) => provider.code).join(", ")}; боевой гейт ниже остается закрыт до подтверждений Lava.top.` : reasonList(payments?.blocked_reasons),
            tone: payments?.ok ? "warning" : "warning",
          },
          {
            label: "Telegram Stars",
            value: "выключено по политике",
            hint: "BOT_STARS_PAYMENTS_ENABLED=false; после GO единственный публичный платежный маршрут — Lava.top. Сейчас оплата закрыта, подарочные коды можно только активировать.",
            tone: "success",
          },
          {
            label: "Email",
            value: email?.enabled ? "локально проверено" : "закрыто",
            hint: email?.enabled ? "режим включен; боевой гейт ниже остается закрыт до подтвержденной доставки писем." : reasonList(email?.blocked_reasons),
            tone: email?.enabled ? "warning" : "warning",
          },
        ]}
      />

      <section className={adminPanelClass("accent")}>
        <AdminPanelHeader
          eyebrow="следующие действия"
          title="Что нужно от оператора"
          description="Короткий список входов, без которых релизный экран честно остается NO-GO. Команды и маркеры не содержат секретов; адреса для probe нужно подставить вручную."
        />
        <div className="grid gap-3 xl:grid-cols-3">
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
            {EXTERNAL_GATES.map((gate) => (
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
            {[
              "POKROV готовит ограниченную Android и Windows бета вне магазинов.",
              runtimeLinksReady
                ? "GitHub Releases APK/EXE доступны в runtime /api/client/apps; публичный анонс все еще ждет финальный GO."
                : "GitHub prerelease assets подготовлены для проверки; runtime-ссылки пока не активны.",
              "Android-кандидат принят как операторски подтвержденный, Windows EXE остается неподписанной бета-сборкой.",
              "Оплата остается закрытой до подтверждений Lava.top и доставки ключей по email.",
              "Email-вход включается только при готовой доставке писем.",
            ].map((claim) => (
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
            {[
              "Публичная бета уже запущена.",
              "Оплата Lava.top работает в бою.",
              "Android raw repo validation green или магазинная публикация уже разрешена.",
              "Windows подписан доверенным сертификатом.",
              runtimeLinksReady
                ? "Runtime-ссылки активны, значит можно отправлять публичный анонс без финального GO."
                : "GitHub Releases уже являются рабочим путем загрузки в приложении или кабинете.",
            ].map((claim) => (
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
