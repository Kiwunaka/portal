import { useEffect, useMemo, useRef, useState } from "react";
import gsap from "gsap";
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
  { key: "1_month", label: "1 мес", stars: 199 },
  { key: "3_months", label: "3 мес", stars: 499 },
  { key: "6_months", label: "6 мес", stars: 949, badge: "Выбор" },
  { key: "9_months", label: "9 мес", stars: 1299 },
  { key: "12_months", label: "12 мес", stars: 1499, badge: "Рек." },
];

const MAP_POINTS: Array<{ code: string; x: number; y: number; label: string }> = [
  { code: "us", x: 55, y: 70, label: "US" },
  { code: "de", x: 155, y: 62, label: "DE" },
  { code: "pl", x: 170, y: 56, label: "PL" },
  { code: "it", x: 162, y: 78, label: "IT" },
];

/* ── Dev Mode: mock data for local preview ── */
const IS_DEV = typeof window !== "undefined" && (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1");

const MOCK_USER: UserPayload = {
  tg_id: 123456,
  username: "dev_preview",
  is_admin: false,
  segment: "PAID",
  features: { haptic: false },
  actions: { pay_via_bot: "#" },
  support: { username: "portal_privacy_helpbot", new_ticket_link: "#" },
} as UserPayload;

const MOCK_DASH: DashboardSnapshot = {
  is_active: true,
  segment: "PAID",
  sub_type: "PRO",
  expiry_at: new Date(Date.now() + 45 * 86400000).toISOString(),
  device_limit: 5,
  total_gb: 0,
  used_gb: 0,
  subscription_url: "vless://demo-key-for-preview",
  active_offer: null,
} as DashboardSnapshot;

const MOCK_NODES: NodeStatus[] = [
  { code: "de", country: "Germany", host: "de-1.portal.net", ping_ms: 42, is_healthy: true },
  { code: "us", country: "United States", host: "us-1.portal.net", ping_ms: 128, is_healthy: true },
  { code: "pl", country: "Poland", host: "pl-1.portal.net", ping_ms: 38, is_healthy: true },
  { code: "it", country: "Italy", host: "it-1.portal.net", ping_ms: 55, is_healthy: false },
] as NodeStatus[];

const MOCK_POINTS: PointsSnapshot = { available_points: 320, expiring_soon_points: 50 } as PointsSnapshot;

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

function prefersReducedMotion(): boolean {
  if (typeof window === "undefined") return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
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

/* ── Animated Counter Hook ── */
function useCountUp(target: number, duration = 1.2): number {
  const [val, setVal] = useState(0);
  const prevTarget = useRef(0);

  useEffect(() => {
    if (target === prevTarget.current) return;
    prevTarget.current = target;
    if (prefersReducedMotion()) {
      setVal(target);
      return;
    }
    const obj = { v: val };
    gsap.to(obj, {
      v: target,
      duration,
      ease: "power2.out",
      onUpdate: () => setVal(Math.round(obj.v)),
    });
  }, [target, duration]);

  return val;
}

/* ── Nodes Map Component ── */
function NodesMap({
  nodes,
  selectedCode,
  onSelect,
}: {
  nodes: NodeStatus[];
  selectedCode: string;
  onSelect: (code: string) => void;
}) {
  const mapRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!mapRef.current) return;
    if (prefersReducedMotion()) return;
    // Animate nodes in
    gsap.from(mapRef.current.querySelectorAll(".node-point"), {
      scale: 0,
      opacity: 0,
      stagger: 0.15,
      duration: 0.5,
      ease: "back.out(2)",
      transformOrigin: "center center",
    });
    gsap.from(mapRef.current.querySelectorAll(".node-label"), {
      opacity: 0,
      x: 10,
      stagger: 0.15,
      duration: 0.4,
      ease: "power2.out",
      delay: 0.3,
    });
  }, []);

  // Animate selection change
  useEffect(() => {
    if (!mapRef.current) return;
    if (prefersReducedMotion()) return;
    mapRef.current.querySelectorAll(".node-point").forEach((el) => {
      const code = el.getAttribute("data-code");
      if (code === selectedCode) {
        gsap.to(el, { attr: { r: 8 }, duration: 0.3, ease: "elastic.out(1, 0.5)" });
      } else {
        gsap.to(el, { attr: { r: 5 }, duration: 0.2, ease: "power2.out" });
      }
    });
  }, [selectedCode]);

  return (
    <svg ref={mapRef} viewBox="0 0 320 160" className="nodes-map" aria-label="nodes map">
      <defs>
        <filter id="glow">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <rect className="map-bg" x="0" y="0" width="320" height="160" />
      {/* Grid lines */}
      {[40, 80, 120].map((y) => (
        <line key={`h${y}`} className="grid-line" x1="0" y1={y} x2="320" y2={y} />
      ))}
      {[64, 128, 192, 256].map((x) => (
        <line key={`v${x}`} className="grid-line" x1={x} y1="0" x2={x} y2="160" />
      ))}
      {/* Connection lines between nodes */}
      {MAP_POINTS.slice(1).map((p) => (
        <line
          key={`conn-${p.code}`}
          className={`conn-line ${selectedCode === p.code ? "active" : ""}`}
          x1={MAP_POINTS[0].x}
          y1={MAP_POINTS[0].y}
          x2={p.x}
          y2={p.y}
        />
      ))}
      {/* Node points */}
      {MAP_POINTS.map((p) => (
        <g
          key={p.code}
          className="node-hit"
          role="button"
          tabIndex={0}
          aria-label={`Выбрать узел ${p.label}`}
          style={{ cursor: "pointer" }}
          onClick={() => onSelect(p.code)}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              onSelect(p.code);
            }
          }}
        >
          <circle
            className={`node-ring ${selectedCode === p.code ? "active" : ""}`}
            cx={p.x}
            cy={p.y}
            r={14}
          />
          <circle
            className={`node-point ${selectedCode === p.code ? "selected" : ""}`}
            cx={p.x}
            cy={p.y}
            r={selectedCode === p.code ? 8 : 5}
            data-code={p.code}
            filter="url(#glow)"
          />
          <text
            className={`node-label ${selectedCode === p.code ? "selected" : ""}`}
            x={p.x + 12}
            y={p.y + 3}
          >
            [{p.label}]
          </text>
        </g>
      ))}
    </svg>
  );
}

/* ── App ── */
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

  const tabContentRef = useRef<HTMLElement>(null);
  const prevTab = useRef<UserTab>("status");

  const platform = detectPlatform();
  const segment = segmentInfo((dash?.segment || user?.segment || dash?.sub_type || "").toUpperCase());
  const selectedNode = useMemo(() => nodes.find((n) => n.code === selectedNodeCode) || nodes[0] || null, [nodes, selectedNodeCode]);

  // Animated metric values
  const deviceCount = useCountUp(dash?.device_limit ?? 0);
  const trafficUsed = useCountUp(dash?.used_gb ?? 0, 0.8);

  useEffect(() => {
    tgReady();
  }, []);

  useEffect(() => {
    if (!banner) return;
    const id = window.setTimeout(() => setBanner(""), 2200);
    return () => window.clearTimeout(id);
  }, [banner]);

  // GSAP tab transition
  useEffect(() => {
    if (prevTab.current === uTab) return;
    prevTab.current = uTab;
    if (prefersReducedMotion()) return;
    if (tabContentRef.current) {
      gsap.fromTo(
        tabContentRef.current,
        { opacity: 0, y: 12, scale: 0.98 },
        { opacity: 1, y: 0, scale: 1, duration: 0.45, ease: "power3.out" },
      );
    }
  }, [uTab]);

  // Entry animation
  useEffect(() => {
    if (!loading && !error) {
      if (prefersReducedMotion()) return;
      gsap.from(".card", {
        y: 20,
        opacity: 0,
        stagger: 0.08,
        duration: 0.5,
        ease: "power3.out",
        delay: 0.1,
      });
    }
  }, [loading, error]);

  async function loadAll() {
    if (!tgUser && !IS_DEV) {
      setError("Откройте WebApp из Telegram-бота.");
      setLoading(false);
      return;
    }
    if (!tgUser && IS_DEV) {
      // Dev mode: use mock data for design preview
      setUser(MOCK_USER);
      setDash(MOCK_DASH);
      setNodes(MOCK_NODES);
      setPoints(MOCK_POINTS);
      setTickets([]);
      setSelectedNodeCode("de");
      setLoading(false);
      return;
    }
    try {
      setLoading(true);
      setError("");
      const [u, d, n, t, p] = await Promise.all([
        fetchUser(tgUser!.id),
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
      setSpeedText(`Задержка ${res.latencyMs}ms | Проба ${res.downloadMs}ms | ${qualityLabel(res.quality)}`);
    } catch {
      setSpeedText("Проверка не удалась");
    } finally {
      setProbeBusy(false);
    }
  }

  function switchTab(t: UserTab) {
    setUTab(t);
    void trackEvent("opened_webapp", "webapp", { tab: t });
  }

  if (loading) {
    return (
      <div className="app">
        <div className="grain" />
        <section className="card">
          <div className="section-tag">[ЗАГРУЗКА]</div>
          <div className="skeleton skeleton--title" />
          <div className="skeleton skeleton--line" />
          <div className="skeleton skeleton--line" />
        </section>
      </div>
    );
  }

  if (error || !user || !dash) {
    return (
      <div className="app">
        <div className="grain" />
        <section className="card card--danger">
          <div className="section-tag">[ОШИБКА]</div>
          <div className="card__title">Ошибка</div>
          <div className="muted">{error || "Нет данных"}</div>
        </section>
      </div>
    );
  }

  return (
    <div className="app">
      <div className="grain" />

      {banner ? <div className="banner">{banner}</div> : null}

      <header className="top">
        <div className="brand">
          <div className="brand__mark">P</div>
          <div>
            <div className="brand__title">PORTAL</div>
            <div className="brand__sub">{user.username ? `@${user.username}` : `ID ${user.tg_id}`}</div>
          </div>
        </div>
        <button className="chip" onClick={() => setShowSettings((v) => !v)} type="button">
          [CFG]
        </button>
      </header>

      {showSettings ? (
        <section className="card card-enter">
          <div className="section-tag">[НАСТРОЙКИ]</div>
          <div className="card__title">Настройки</div>
          <div className="list">
            <div className="row">
              <div>
                <div className="row__title">Аккаунт</div>
                <div className="row__sub">{`${dash.sub_type} | ${fmtDate(dash.expiry_at)}`}</div>
              </div>
            </div>
            <div className="row">
              <div>
                <div className="row__title">Оферта</div>
                <div className="row__sub">{`Обновлено: ${OFFER_UPDATED_AT}`}</div>
              </div>
            </div>
          </div>
          <pre className="mono legal">{OFFER_FULL}</pre>
        </section>
      ) : null}

      {user.is_admin ? (
        <section className="card card-enter">
          <div className="section-tag">[АДМИН]</div>
          <div className="chips">
            {(["summary", "tickets", "nodes"] as AdminTab[]).map((k) => (
              <button key={k} className={aTab === k ? "chip chip--active" : "chip"} type="button" onClick={() => setATab(k)}>{k.toUpperCase()}</button>
            ))}
          </div>
          {aTab === "summary" && admSummary ? <div className="muted" style={{ marginTop: 12 }}>{`Пользователи ${admSummary.users.total} | Узлы ${admSummary.nodes.healthy}/${admSummary.nodes.total}`}</div> : null}
          {aTab === "tickets" ? <div className="muted" style={{ marginTop: 12 }}>{`Тикеты: ${admTickets.length}`}</div> : null}
          {aTab === "nodes" ? <div className="muted" style={{ marginTop: 12 }}>{`Узлы: ${admNodes.length}`}</div> : null}
        </section>
      ) : null}

      <section ref={tabContentRef} key={uTab}>
        {uTab === "status" ? (
          <div className="card tab-content">
            <div className="section-tag">[СТАТУС]</div>
            <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 12 }}>
              <div className={dash.is_active ? "status status--ok" : "status status--bad"}>
                {dash.is_active ? "● АКТИВЕН" : "● ИСТЁК"}
              </div>
              <div className="pill">{segment.title}</div>
            </div>
            <div className="muted" style={{ marginBottom: 14 }}>{segment.text}</div>

            <div className="stories">
              {STORY_SLIDES.map((s, i) => (
                <article className={`story slide-in stagger-${i + 1}`} key={s.title}>
                  <div className="story__title">{s.title}</div>
                  <div className="story__text">{s.text}</div>
                </article>
              ))}
            </div>

            <div className="grid2">
              <div className="metric">
                <div className="metric__k">До конца</div>
                <div className="metric__v metric__v--accent">{fmtLeft(dash.expiry_at)}</div>
              </div>
              <div className="metric">
                <div className="metric__k">Устройства</div>
                <div className="metric__v">{deviceCount}</div>
              </div>
              <div className="metric">
                <div className="metric__k">Трафик</div>
                <div className="metric__v">{dash.total_gb > 0 ? `${trafficUsed}/${dash.total_gb} GB` : "∞"}</div>
              </div>
              <div className="metric">
                <div className="metric__k">Сегмент</div>
                <div className="metric__v">{dash.segment || dash.sub_type}</div>
              </div>
            </div>

            <div className="muted" style={{ marginBottom: 8 }}>
              {`Баллы: ${points?.available_points ?? 0} | Сгорают скоро: ${points?.expiring_soon_points ?? 0}`}
            </div>

            {dash.active_offer ? (
              <div className="pill pill--ok" style={{ marginBottom: 12 }}>
                {`Оффер: ${dash.active_offer.price_stars}⭐ до ${fmtDate(dash.active_offer.expires_at)}`}
              </div>
            ) : null}

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

            <div className="actions" style={{ marginTop: 12 }}>
              <button className="btn" type="button" onClick={() => onPay(dash.active_offer?.plan_code || selectedPlan || segment.ctaPlan)}>
                <span style={{ position: "relative", zIndex: 1 }}>→ Подключить / Продлить</span>
              </button>
              <button className="btn btn--ghost" type="button" onClick={() => onCopyKey("copied_key")}>
                <span style={{ position: "relative", zIndex: 1 }}>Скопировать ключ</span>
              </button>
            </div>
          </div>
        ) : null}

        {uTab === "connect" ? (
          <div className="card tab-content">
            <div className="section-tag">[ПОДКЛЮЧЕНИЕ]</div>
            <div className="card__title">Мастер подключения</div>

            <div className="step">
              <div className={`step__n ${connectStep === 1 ? "step__n--active" : connectStep > 1 ? "step__n--done" : ""}`}>
                {connectStep > 1 ? "✓" : "1"}
              </div>
              <div className="step__body">Импорт ключа в клиент</div>
            </div>
            <div className="step">
              <div className={`step__n ${connectStep === 2 ? "step__n--active" : connectStep > 2 ? "step__n--done" : ""}`}>
                {connectStep > 2 ? "✓" : "2"}
              </div>
              <div className="step__body">Проверка соединения</div>
            </div>
            <div className="step">
              <div className={`step__n ${connectStep === 3 ? "step__n--active" : ""}`}>
                {connectStep === 3 ? "✓" : "3"}
              </div>
              <div className="step__body">Готово</div>
            </div>

            <div className="list">
              {clientOptionsForPlatform().map((c) => (
                <div
                  key={c.title}
                  className="row row--btn"
                  role="button"
                  tabIndex={0}
                  onClick={() => openLink(c.url)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      openLink(c.url);
                    }
                  }}
                >
                  <div>
                    <div className="row__title">{c.title}</div>
                    <div className="row__sub">Рекомендуемый клиент</div>
                  </div>
                  <span style={{ color: "var(--red)", fontFamily: "var(--mono)", fontSize: 12 }}>→</span>
                </div>
              ))}
            </div>

            <div className="actions" style={{ marginTop: 12 }}>
              <button className="btn" type="button" onClick={runConnectImport}>
                <span style={{ position: "relative", zIndex: 1 }}>Импорт</span>
              </button>
              <button className="btn btn--ghost" type="button" onClick={finishConnect}>
                <span style={{ position: "relative", zIndex: 1 }}>Проверить и завершить</span>
              </button>
            </div>

            <div className="actions" style={{ marginTop: 2 }}>
              <button className="btn btn--ghost" type="button" onClick={() => onCopyKey("copy_used")}>
                <span style={{ position: "relative", zIndex: 1 }}>Если не сработало: копировать</span>
              </button>
              <button className="btn btn--ghost" type="button" onClick={() => openLink("https://t.me/" + (user.support?.username || "portal_privacy_helpbot"))}>
                <span style={{ position: "relative", zIndex: 1 }}>Инструкция</span>
              </button>
            </div>

            <div className="muted" style={{ marginTop: 12 }}>{`Платформа: ${platform}`}</div>
          </div>
        ) : null}

        {uTab === "nodes" ? (
          <div className="card tab-content">
            <div className="section-tag">[УЗЛЫ]</div>
            <div className="card__title">Сетевые узлы</div>

            <NodesMap
              nodes={nodes}
              selectedCode={selectedNodeCode}
              onSelect={setSelectedNodeCode}
            />

            {selectedNode ? (
              <div className="pill" style={{ marginBottom: 12 }}>
                {`[${selectedNode.code.toUpperCase()}] ${selectedNode.country} • ${selectedNode.host} • ping ${selectedNode.ping_ms ?? "n/a"}ms`}
              </div>
            ) : null}

            <div className="list">
              {nodes.map((n) => (
                <button key={n.code} className="row row--btn" type="button" onClick={() => setSelectedNodeCode(n.code)}>
                  <div>
                    <div className="row__title">{`[${n.code.toUpperCase()}] ${n.country}`}</div>
                    <div className="row__sub">{`${n.host} • ping ${n.ping_ms ?? "n/a"}ms`}</div>
                  </div>
                  <div className={n.is_healthy ? "pill pill--ok" : "pill pill--bad"}>{n.is_healthy ? "Онлайн" : "Проблемы"}</div>
                </button>
              ))}
            </div>

            <div className="actions" style={{ marginTop: 12 }}>
              <button className="btn btn--ghost" onClick={runDiagnostics} type="button">
                <span style={{ position: "relative", zIndex: 1 }}>Диагностика</span>
              </button>
              <button className="btn btn--ghost" onClick={runSpeedCheck} disabled={probeBusy} type="button">
                <span style={{ position: "relative", zIndex: 1 }}>Проверка скорости</span>
              </button>
            </div>
            <div className="muted" style={{ marginTop: 8 }}>{diagText || speedText}</div>
          </div>
        ) : null}

        {uTab === "support" ? (
          <div className="card tab-content">
            <div className="section-tag">[ПОДДЕРЖКА]</div>
            <div className="card__title">Поддержка</div>
            <div className="actions">
              <button className="btn btn--ghost" type="button" onClick={() => openLink(user.support.new_ticket_link)}>
                <span style={{ position: "relative", zIndex: 1 }}>Открыть бот поддержки</span>
              </button>
            </div>
            <textarea className="field field--area" value={ticketBody} onChange={(e) => setTicketBody(e.target.value)} placeholder="Опишите проблему..." />
            <div className="actions" style={{ marginTop: 8 }}>
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
                <span style={{ position: "relative", zIndex: 1 }}>Создать тикет</span>
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
                <textarea className="field field--area" value={replyBody} onChange={(e) => setReplyBody(e.target.value)} placeholder="Ответ..." />
                <button
                  className="btn"
                  type="button"
                  style={{ marginTop: 8 }}
                  onClick={async () => {
                    if (!ticket || !replyBody.trim()) return;
                    const t = await addTicketMessage(ticket.id, replyBody.trim());
                    setTicket(t);
                    setReplyBody("");
                    setTickets(await fetchTickets(20));
                  }}
                >
                  <span style={{ position: "relative", zIndex: 1 }}>Отправить ответ</span>
                </button>
              </>
            ) : null}
          </div>
        ) : null}
      </section>

      <nav className="nav">
        {USER_TABS.map((t) => (
          <button
            key={t.id}
            className={uTab === t.id ? "nav__btn nav__btn--a" : "nav__btn"}
            type="button"
            onClick={() => switchTab(t.id)}
          >
            <span className="nav__ico">{t.icon}</span>
            <span className="nav__txt">{t.label}</span>
          </button>
        ))}
      </nav>
    </div>
  );
}
