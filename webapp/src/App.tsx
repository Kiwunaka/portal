import { useEffect, useMemo, useState } from "react";
import {
  addTicketMessage,
  adminNodesHealth,
  adminSummary,
  adminTickets,
  confirmConnect,
  createTicket,
  fetchDashboard,
  fetchNodeStatus,
  fetchTickets,
  fetchUser,
  getPoints,
  getTicket,
  runNetworkProbe,
  runNodeDiagnostics,
  startPayAttempt,
  trackEvent,
  type AdminNodeHealthRow,
  type AdminSummaryPayload,
  type DashboardSnapshot,
  type NodeStatus,
  type PointsSnapshot,
  type TicketInfo,
  type UserPayload,
} from "./api";
import { OFFER_FULL, OFFER_UPDATED_AT } from "./legal";
import { getTgUser, haptic, openLink, tgReady } from "./telegram";

type UserTab = "status" | "connect" | "nodes" | "support";
type AdminTab = "summary" | "tickets" | "nodes";

type StorySlide = { title: string; text: string };
type PlanChoice = { key: string; label: string; stars: number; badge?: string };
type SegmentInfo = { title: string; text: string; ctaPlan: string };

const USER_TABS: Array<{ id: UserTab; label: string; icon: string }> = [
  { id: "status", label: "Статус", icon: "S" },
  { id: "connect", label: "Подключение", icon: "C" },
  { id: "nodes", label: "Ноды", icon: "N" },
  { id: "support", label: "Поддержка", icon: "?" },
];

const STORY_SLIDES: StorySlide[] = [
  { title: "Шифрование", text: "Зашифрованный канал между устройством и узлом." },
  { title: "4 страны", text: "Платные тарифы включают доступ ко всем доступным странам." },
  { title: "Антитрекинг", text: "Маршрутизация снижает трекинг и лишний шум." },
  { title: "1-2 минуты", text: "Импорт ключа и подключение за пару шагов." },
];

const PLAN_CHOICES: PlanChoice[] = [
  { key: "1_month", label: "1 месяц", stars: 199 },
  { key: "3_months", label: "3 месяца", stars: 499 },
  { key: "6_months", label: "6 месяцев", stars: 949, badge: "Выбор" },
  { key: "9_months", label: "9 месяцев", stars: 1299 },
  { key: "12_months", label: "12 месяцев", stars: 1499, badge: "Рекомендуем" },
];

const MAP_POINTS: Array<{ code: string; x: number; y: number }> = [
  { code: "us", x: 55, y: 70 },
  { code: "de", x: 155, y: 62 },
  { code: "pl", x: 170, y: 56 },
  { code: "it", x: 162, y: 78 },
];

function fmtDate(iso?: string | null): string {
  if (!iso) return "-";
  return new Date(iso).toLocaleString("ru-RU");
}

function fmtLeft(iso?: string | null): string {
  if (!iso) return "-";
  const ms = new Date(iso).getTime() - Date.now();
  if (ms <= 0) return "истёк";
  const d = Math.floor(ms / 86400000);
  const h = Math.floor((ms % 86400000) / 3600000);
  return `${d}д ${h}ч`;
}

function detectPlatform(): "ios" | "android" | "desktop" {
  const ua = navigator.userAgent.toLowerCase();
  if (/iphone|ipad|ipod/.test(ua)) return "ios";
  if (/android/.test(ua)) return "android";
  return "desktop";
}

function segmentInfo(segmentRaw: string): SegmentInfo {
  const segment = (segmentRaw || "").toUpperCase();
  if (segment === "FREE") {
    return {
      title: "Бесплатный профиль",
      text: "Базовый доступ активен. Апгрейд откроет все страны и повышенные лимиты.",
      ctaPlan: "1_month",
    };
  }
  if (segment === "EXPIRED") {
    return {
      title: "Доступ истёк",
      text: "Продлите доступ, чтобы защита не прерывалась.",
      ctaPlan: "1_month",
    };
  }
  if (segment === "MANUAL") {
    return {
      title: "Ручной профиль",
      text: "Ваш доступ управляется вручную. Для изменений используйте поддержку.",
      ctaPlan: "3_months",
    };
  }
  return {
    title: "Платный профиль",
    text: "Доступны все страны и приоритетный маршрут.",
    ctaPlan: "12_months",
  };
}

function qualityLabel(q: "good" | "fair" | "poor"): string {
  if (q === "good") return "Хорошо";
  if (q === "fair") return "Средне";
  return "Слабо";
}

async function copyText(text: string): Promise<boolean> {
  const value = (text || "").trim();
  if (!value) return false;
  try {
    await navigator.clipboard.writeText(value);
    return true;
  } catch {
    return false;
  }
}

export default function App() {
  const tgUser = useMemo(() => getTgUser(), []);
  const [user, setUser] = useState<UserPayload | null>(null);
  const [dash, setDash] = useState<DashboardSnapshot | null>(null);
  const [nodes, setNodes] = useState<NodeStatus[]>([]);
  const [points, setPoints] = useState<PointsSnapshot | null>(null);
  const [tickets, setTickets] = useState<TicketInfo[]>([]);
  const [ticket, setTicket] = useState<TicketInfo | null>(null);
  const [ticketBody, setTicketBody] = useState("");
  const [replyBody, setReplyBody] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [uTab, setUTab] = useState<UserTab>("status");
  const [showSettings, setShowSettings] = useState(false);
  const [connectStep, setConnectStep] = useState<1 | 2 | 3>(1);
  const [diagText, setDiagText] = useState("");
  const [speedText, setSpeedText] = useState("");
  const [banner, setBanner] = useState("");
  const [probeBusy, setProbeBusy] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<string>("1_month");
  const [selectedNodeCode, setSelectedNodeCode] = useState<string>("de");

  const [aTab, setATab] = useState<AdminTab>("summary");
  const [admSummary, setAdmSummary] = useState<AdminSummaryPayload | null>(null);
  const [admTickets, setAdmTickets] = useState<TicketInfo[]>([]);
  const [admNodes, setAdmNodes] = useState<AdminNodeHealthRow[]>([]);

  const platform = detectPlatform();
  const segment = segmentInfo((dash?.segment || user?.segment || dash?.sub_type || "").toUpperCase());
  const selectedNode = useMemo(() => nodes.find((n) => n.code === selectedNodeCode) || nodes[0] || null, [nodes, selectedNodeCode]);

  useEffect(() => {
    tgReady();
  }, []);

  useEffect(() => {
    if (!banner) return;
    const id = window.setTimeout(() => setBanner(""), 2200);
    return () => window.clearTimeout(id);
  }, [banner]);

  async function loadAll() {
    if (!tgUser) {
      setError("Откройте WebApp из Telegram-бота.");
      setLoading(false);
      return;
    }
    try {
      setLoading(true);
      setError("");
      const [u, d, n, t, p] = await Promise.all([
        fetchUser(tgUser.id),
        fetchDashboard(),
        fetchNodeStatus(),
        fetchTickets(20),
        getPoints().catch(() => null),
      ]);
      setUser(u);
      setDash(d);
      setNodes(n);
      setTickets(t);
      setPoints(p);
      if (n.length > 0) setSelectedNodeCode(n[0].code);
      if (u.is_admin) {
        const [s, at, an] = await Promise.all([adminSummary(), adminTickets("", 30), adminNodesHealth()]);
        setAdmSummary(s);
        setAdmTickets(at);
        setAdmNodes(an);
      }
      void trackEvent("opened_webapp", "webapp", { tab: "status" });
    } catch (e: unknown) {
      setError(String((e as { message?: string })?.message || e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function pulse(kind: "success" | "error") {
    if (user?.features?.haptic ?? true) haptic(kind);
  }

  async function onCopyKey(eventName: "copied_key" | "copy_used" = "copied_key") {
    if (!dash?.subscription_url) return;
    const ok = await copyText(dash.subscription_url);
    if (ok) {
      setBanner("Ключ скопирован");
      pulse("success");
      void trackEvent(eventName, "webapp");
    } else {
      setBanner("Не удалось скопировать");
      pulse("error");
    }
  }

  async function onPay(plan = "1_month") {
    try {
      const offerId = dash?.active_offer?.id;
      const res = await startPayAttempt(plan, "webapp", offerId ?? undefined);
      openLink(res.pay_url || user?.actions.pay_via_bot || "");
      pulse("success");
    } catch {
      openLink(user?.actions.pay_via_bot || "");
    }
  }

  function clientOptionsForPlatform(): Array<{ title: string; url: string }> {
    if (platform === "ios") {
      return [
        { title: "Streisand", url: "https://apps.apple.com/app/streisand/id6450534064" },
        { title: "Happ", url: "https://apps.apple.com/app/happ-proxy-utility/id6504287215" },
      ];
    }
    if (platform === "android") {
      return [
        { title: "Hiddify", url: "https://play.google.com/store/apps/details?id=app.hiddify.com" },
        { title: "v2rayNG", url: "https://github.com/2dust/v2rayNG/releases" },
      ];
    }
    return [
      { title: "Hiddify Next", url: "https://github.com/hiddify/hiddify-next/releases" },
      { title: "Nekoray", url: "https://github.com/MatsuriDayo/nekoray/releases" },
    ];
  }

  async function runConnectImport() {
    if (!dash?.subscription_url) return;
    void trackEvent("clicked_connect", "webapp", { platform });
    const deep = `hiddify://import/${encodeURIComponent(dash.subscription_url)}`;
    openLink(deep);
    setBanner("Открываю клиент...");
    pulse("success");
    setConnectStep(2);
    void trackEvent("deep_link_opened", "webapp", { platform });
  }

  async function finishConnect() {
    try {
      await confirmConnect();
      setConnectStep(3);
      setBanner("Подключение подтверждено");
      pulse("success");
    } catch {
      setBanner("Проверка не удалась");
      pulse("error");
    }
  }

  async function runDiagnostics() {
    setDiagText("Проверяю маршрут до ноды...");
    try {
      const res = await runNodeDiagnostics();
      setDiagText(`${res.summary} | DNS=${res.dns_status} | SNI=${res.sni_status}`);
      pulse("success");
    } catch (e: unknown) {
      setDiagText(String((e as { message?: string })?.message || e));
      pulse("error");
    }
  }

  async function runSpeedCheck() {
    setProbeBusy(true);
    setSpeedText("Измеряю качество...");
    try {
      const res = await runNetworkProbe(2);
      setSpeedText(`Latency ${res.latencyMs}ms | Probe ${res.downloadMs}ms | ${qualityLabel(res.quality)}`);
    } catch {
      setSpeedText("Проверка не удалась");
    } finally {
      setProbeBusy(false);
    }
  }

  if (loading) {
    return <div className="app"><section className="card"><div className="card__title">Загрузка...</div></section></div>;
  }
  if (error || !user || !dash) {
    return <div className="app"><section className="card card--danger"><div className="card__title">Ошибка</div><div className="muted">{error || "Нет данных"}</div></section></div>;
  }

  return (
    <div className="app app--new">
      <header className="top">
        <div className="brand">
          <div className="brand__mark">P</div>
          <div>
            <div className="brand__title">PORTAL</div>
            <div className="brand__sub">{user.username ? `@${user.username}` : `ID ${user.tg_id}`}</div>
          </div>
        </div>
        <button className="chip" onClick={() => setShowSettings((v) => !v)} type="button">Настройки</button>
      </header>

      {banner ? <section className="card card--notice"><div className="muted">{banner}</div></section> : null}

      {showSettings ? (
        <section className="card">
          <div className="card__title">Настройки</div>
          <div className="list">
            <div className="row"><div><div className="row__title">Аккаунт</div><div className="row__sub">{`${dash.sub_type} | ${fmtDate(dash.expiry_at)}`}</div></div></div>
            <div className="row"><div><div className="row__title">Оферта</div><div className="row__sub">{`Обновлено: ${OFFER_UPDATED_AT}`}</div></div></div>
          </div>
          <pre className="mono legal">{OFFER_FULL}</pre>
        </section>
      ) : null}

      {user.is_admin ? (
        <section className="card">
          <div className="chips">
            {(["summary", "tickets", "nodes"] as AdminTab[]).map((k) => (
              <button key={k} className={aTab === k ? "chip chip--active" : "chip"} type="button" onClick={() => setATab(k)}>{k}</button>
            ))}
          </div>
          {aTab === "summary" && admSummary ? <div className="muted">{`Пользователи ${admSummary.users.total} | Ноды ${admSummary.nodes.healthy}/${admSummary.nodes.total}`}</div> : null}
          {aTab === "tickets" ? <div className="muted">{`Тикеты: ${admTickets.length}`}</div> : null}
          {aTab === "nodes" ? <div className="muted">{`Ноды: ${admNodes.length}`}</div> : null}
        </section>
      ) : null}

      {uTab === "status" ? (
        <section className="card">
          <div className={dash.is_active ? "status status--ok" : "status status--bad"}>{dash.is_active ? "Активен" : "Истёк"}</div>
          <div className="pill">{segment.title}</div>
          <div className="muted">{segment.text}</div>
          <div className="stories">
            {STORY_SLIDES.map((s) => (
              <article className="story" key={s.title}>
                <div className="story__title">{s.title}</div>
                <div className="story__text">{s.text}</div>
              </article>
            ))}
          </div>
          <div className="grid2">
            <div className="metric"><div className="metric__k">До конца</div><div className="metric__v">{fmtLeft(dash.expiry_at)}</div></div>
            <div className="metric"><div className="metric__k">Устройства</div><div className="metric__v">{dash.device_limit}</div></div>
            <div className="metric"><div className="metric__k">Трафик</div><div className="metric__v">{dash.total_gb > 0 ? `${dash.used_gb}/${dash.total_gb} GB` : "Безлимит"}</div></div>
            <div className="metric"><div className="metric__k">Сегмент</div><div className="metric__v">{dash.segment || dash.sub_type}</div></div>
          </div>
          <div className="muted">{`Баллы: ${points?.available_points ?? 0} | Скоро сгорят: ${points?.expiring_soon_points ?? 0}`}</div>
          {dash.active_offer ? <div className="pill pill--ok">{`Офер: ${dash.active_offer.price_stars}⭐ до ${fmtDate(dash.active_offer.expires_at)}`}</div> : null}
          <div className="plans-mini">
            {PLAN_CHOICES.map((p) => (
              <button
                key={p.key}
                type="button"
                className={selectedPlan === p.key ? "chip chip--active" : "chip"}
                onClick={() => {
                  setSelectedPlan(p.key);
                  pulse("success");
                }}
              >
                {`${p.label} ${p.stars}⭐${p.badge ? ` • ${p.badge}` : ""}`}
              </button>
            ))}
          </div>
          <div className="actions">
            <button className="btn" type="button" onClick={() => onPay(dash.active_offer?.plan_code || selectedPlan || segment.ctaPlan)}>Подключить / Продлить</button>
            <button className="btn btn--ghost" type="button" onClick={() => onCopyKey("copied_key")}>Скопировать ключ</button>
          </div>
        </section>
      ) : null}

      {uTab === "connect" ? (
        <section className="card">
          <div className="card__title">Мастер подключения</div>
          <div className="step"><div className="step__n">{connectStep === 1 ? "o" : "1"}</div><div className="step__body">Импорт ключа в клиент</div></div>
          <div className="step"><div className="step__n">{connectStep === 2 ? "o" : "2"}</div><div className="step__body">Проверка подключения</div></div>
          <div className="step"><div className="step__n">{connectStep === 3 ? "o" : "3"}</div><div className="step__body">Готово</div></div>
          <div className="list">
            {clientOptionsForPlatform().map((c) => (
              <div key={c.title} className="row row--btn" role="button" tabIndex={0} onClick={() => openLink(c.url)} onKeyDown={() => openLink(c.url)}>
                <div>
                  <div className="row__title">{c.title}</div>
                  <div className="row__sub">Рекомендуемый клиент</div>
                </div>
              </div>
            ))}
          </div>
          <div className="actions">
            <button className="btn" type="button" onClick={runConnectImport}>Импорт</button>
            <button className="btn btn--ghost" type="button" onClick={finishConnect}>Проверить и завершить</button>
          </div>
          <div className="actions">
            <button className="btn btn--ghost" type="button" onClick={() => onCopyKey("copy_used")}>Если не открылось: копировать</button>
            <button className="btn btn--ghost" type="button" onClick={() => openLink("https://t.me/" + (user.support?.username || "portal_privacy_helpbot"))}>Открыть инструкцию</button>
          </div>
          <div className="muted">{`Платформа: ${platform}`}</div>
        </section>
      ) : null}

      {uTab === "nodes" ? (
        <section className="card">
          <div className="card__title">Ноды</div>
          <svg viewBox="0 0 320 160" className="nodes-map" aria-label="карта нод">
            <rect x="0" y="0" width="320" height="160" rx="12" />
            {MAP_POINTS.map((p) => (
              <g key={p.code} onClick={() => setSelectedNodeCode(p.code)} role="button">
                <circle cx={p.x} cy={p.y} r={selectedNodeCode === p.code ? 7 : 5} />
                <text x={p.x + 10} y={p.y + 4}>{p.code.toUpperCase()}</text>
              </g>
            ))}
          </svg>
          {selectedNode ? (
            <div className="pill">{`${selectedNode.country} • ${selectedNode.host} • ping ${selectedNode.ping_ms ?? "n/a"}ms`}</div>
          ) : null}
          <div className="list">
            {nodes.map((n) => (
              <button key={n.code} className="row row--btn" type="button" onClick={() => setSelectedNodeCode(n.code)}>
                <div>
                  <div className="row__title">{`${n.country} • ${n.code.toUpperCase()}`}</div>
                  <div className="row__sub">{`${n.host} • ping ${n.ping_ms ?? "n/a"}ms`}</div>
                </div>
                <div className={n.is_healthy ? "pill pill--ok" : "pill pill--bad"}>{n.is_healthy ? "Онлайн" : "Проблема"}</div>
              </button>
            ))}
          </div>
          <div className="actions">
            <button className="btn btn--ghost" onClick={runDiagnostics} type="button">Диагностика</button>
            <button className="btn btn--ghost" onClick={runSpeedCheck} disabled={probeBusy} type="button">Проверка скорости</button>
          </div>
          <div className="muted">{diagText || speedText}</div>
        </section>
      ) : null}

      {uTab === "support" ? (
        <section className="card">
          <div className="card__title">Поддержка</div>
          <div className="actions">
            <button className="btn btn--ghost" type="button" onClick={() => openLink(user.support.new_ticket_link)}>Открыть бот поддержки</button>
          </div>
          <textarea className="field field--area" value={ticketBody} onChange={(e) => setTicketBody(e.target.value)} placeholder="Опишите проблему" />
          <div className="actions">
            <button
              className="btn"
              type="button"
              onClick={async () => {
                if (!ticketBody.trim()) return;
                const t = await createTicket("", ticketBody.trim());
                setTicket(t);
                setTicketBody("");
                setTickets(await fetchTickets(20));
                pulse("success");
              }}
            >
              Создать тикет
            </button>
          </div>
          <div className="list">
            {tickets.map((t) => (
              <button key={t.id} className="row row--btn" type="button" onClick={async () => setTicket(await getTicket(t.id))}>
                <div>
                  <div className="row__title">{`#${t.id} ${t.status_title}`}</div>
                  <div className="row__sub">{t.last_message_preview || "-"}</div>
                </div>
              </button>
            ))}
          </div>
          {ticket ? (
            <>
              <div className="divider" />
              <div className="list">
                {ticket.messages.map((m) => (
                  <div key={m.id} className={m.sender_role === "admin" ? "msg msg--op" : "msg msg--mine"}>
                    <div className="row__sub">{m.sender_role === "admin" ? "Оператор" : "Вы"}</div>
                    <div>{m.body}</div>
                  </div>
                ))}
              </div>
              <textarea className="field field--area" value={replyBody} onChange={(e) => setReplyBody(e.target.value)} placeholder="Ответ" />
              <button
                className="btn"
                type="button"
                onClick={async () => {
                  if (!ticket || !replyBody.trim()) return;
                  const t = await addTicketMessage(ticket.id, replyBody.trim());
                  setTicket(t);
                  setReplyBody("");
                  setTickets(await fetchTickets(20));
                }}
              >
                Отправить ответ
              </button>
            </>
          ) : null}
        </section>
      ) : null}

      <nav className="nav nav--bottom">
        {USER_TABS.map((t) => (
          <button
            key={t.id}
            className={uTab === t.id ? "nav__btn nav__btn--a" : "nav__btn"}
            type="button"
            onClick={() => {
              setUTab(t.id);
              void trackEvent("opened_webapp", "webapp", { tab: t.id });
            }}
          >
            <span className="nav__ico">{t.icon}</span>
            <span className="nav__txt">{t.label}</span>
          </button>
        ))}
      </nav>
    </div>
  );
}
