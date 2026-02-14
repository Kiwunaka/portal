import { useEffect, useMemo, useRef, useState } from "react";
import gsap from "gsap";
import {
  addTicketMessage,
  adminBroadcast,
  adminGiftCodeCreate,
  adminGiftCodes,
  adminManualBlock,
  adminManualCreate,
  adminManualExtend,
  adminManualRegenerateToken,
  adminMetricsStatus,
  adminNodesHealth,
  adminNodesSync,
  adminPromoCreate,
  adminPromoDelete,
  adminPromoUpdate,
  adminPromos,
  adminSummary,
  adminTemplateCreate,
  adminTemplateDelete,
  adminTemplateUpdate,
  adminTemplates,
  adminTicketReply,
  adminTicketStatus,
  adminTickets,
  adminUserCard,
  adminUserMessage,
  adminUsers,
  authByTelegramWebLogin,
  clearWebSessionToken,
  confirmConnect,
  createTicket,
  fetchClientApps,
  fetchDashboard,
  fetchNodeStatus,
  fetchTickets,
  fetchUser,
  getPoints,
  hasWebSessionToken,
  getTicket,
  redeemGiftCode,
  runNetworkProbe,
  runNodeDiagnostics,
  setWebSessionToken,
  startPayAttempt,
  trackEvent,
  type AdminGiftCodeRow,
  type AdminMetricsStatus,
  type AdminPromoRow,
  type AdminTemplateRow,
  type AdminUserCard,
  type AdminUserRow,
  type AdminNodeHealthRow,
  type AdminSummaryPayload,
  type ClientAppsPayload,
  type DashboardSnapshot,
  type ManualCreateIn,
  type NodeStatus,
  type PointsSnapshot,
  type TicketInfo,
  type UserPayload,
} from "./api";
import { OFFER_FULL, OFFER_UPDATED_AT } from "./legal";
import { getTgUser, haptic, openLink, tgReady } from "./telegram";

type UserTab = "status" | "connect" | "nodes" | "support";
type AdminTab = "summary" | "users" | "tickets" | "nodes" | "broadcast" | "promos" | "templates" | "giftcodes";

type StorySlide = { title: string; text: string };
type PlanChoice = { key: string; label: string; stars: number; badge?: string };
type SegmentInfo = { title: string; text: string; ctaPlan: string };

declare global {
  interface Window {
    onTelegramAuth?: (user: any) => void;
  }
}

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
  { key: "1_month", label: "1 мес", stars: 249 },
  { key: "3_months", label: "3 мес", stars: 699 },
  { key: "6_months", label: "6 мес", stars: 1199, badge: "Выбор" },
  { key: "9_months", label: "9 мес", stars: 1399 },
  { key: "12_months", label: "12 мес", stars: 1499, badge: "Рек." },
];

const MAP_POINTS: Array<{ code: string; x: number; y: number; label: string }> = [
  { code: "us", x: 55, y: 70, label: "US" },
  { code: "nl", x: 145, y: 60, label: "NL" },
  { code: "pl", x: 170, y: 56, label: "PL" },
  { code: "it", x: 162, y: 78, label: "IT" },
];

const ADMIN_TABS: Array<{ id: AdminTab; label: string }> = [
  { id: "summary", label: "Сводка" },
  { id: "users", label: "Пользователи" },
  { id: "tickets", label: "Тикеты" },
  { id: "nodes", label: "Ноды" },
  { id: "broadcast", label: "Рассылка" },
  { id: "promos", label: "Промокоды" },
  { id: "templates", label: "Шаблоны" },
  { id: "giftcodes", label: "Gift-коды" },
];

const GIFT_CODE_CHOICES: Array<{ key: "mini" | "standard" | "premium"; label: string; days: number; stars: number }> = [
  { key: "mini", label: "Mini", days: 7, stars: 59 },
  { key: "standard", label: "Standard", days: 30, stars: 249 },
  { key: "premium", label: "Premium", days: 90, stars: 699 },
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
  { code: "nl", country: "Netherlands", host: "nl-1.portal.net", ping_ms: 44, is_healthy: true },
  { code: "pl_free", country: "NL Free", host: "free-1.portal.net", ping_ms: 39, is_healthy: true },
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

function firstNonEmpty(...values: Array<string | null | undefined>): string {
  for (const value of values) {
    const trimmed = String(value || "").trim();
    if (trimmed) return trimmed;
  }
  return "";
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
  const [clientApps, setClientApps] = useState<ClientAppsPayload | null>(null);
  const [probeBusy, setProbeBusy] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<string>("1_month");
  const [selectedNodeCode, setSelectedNodeCode] = useState<string>("nl");
  const [giftCode, setGiftCode] = useState("");
  const [giftRedeemResult, setGiftRedeemResult] = useState("");
  const [webLoginRequired, setWebLoginRequired] = useState(false);
  const [webLoginError, setWebLoginError] = useState("");
  const [webLoginBusy, setWebLoginBusy] = useState(false);

  const [aTab, setATab] = useState<AdminTab>("summary");
  const [admBusy, setAdmBusy] = useState(false);
  const [admError, setAdmError] = useState("");
  const [admSummary, setAdmSummary] = useState<AdminSummaryPayload | null>(null);
  const [admMetrics, setAdmMetrics] = useState<AdminMetricsStatus | null>(null);
  const [admTickets, setAdmTickets] = useState<TicketInfo[]>([]);
  const [admTicketFilter, setAdmTicketFilter] = useState<string>("");
  const [admTicket, setAdmTicket] = useState<TicketInfo | null>(null);
  const [admReplyBody, setAdmReplyBody] = useState("");
  const [admNodes, setAdmNodes] = useState<AdminNodeHealthRow[]>([]);
  const [admUsersRows, setAdmUsersRows] = useState<AdminUserRow[]>([]);
  const [admUsersQuery, setAdmUsersQuery] = useState("");
  const [admSelectedUserId, setAdmSelectedUserId] = useState<number | null>(null);
  const [admUserCardData, setAdmUserCardData] = useState<AdminUserCard | null>(null);
  const [admUserMessageBody, setAdmUserMessageBody] = useState("");
  const [admManualForm, setAdmManualForm] = useState<ManualCreateIn>({ display_name: "", days: 30 });
  const [admManualLastLink, setAdmManualLastLink] = useState("");
  const [admBroadcastText, setAdmBroadcastText] = useState("");
  const [admBroadcastSegment, setAdmBroadcastSegment] = useState("all_active");
  const [admBroadcastLimit, setAdmBroadcastLimit] = useState(120);
  const [admBroadcastResult, setAdmBroadcastResult] = useState("");
  const [admNodeSyncSegment, setAdmNodeSyncSegment] = useState("active");
  const [admNodeSyncLimit, setAdmNodeSyncLimit] = useState(100);
  const [admNodeSyncTgId, setAdmNodeSyncTgId] = useState("");
  const [admPromosRows, setAdmPromosRows] = useState<AdminPromoRow[]>([]);
  const [admPromoForm, setAdmPromoForm] = useState({
    code: "",
    promo_type: "days" as "days" | "discount",
    value: 14,
    uses_left: 100,
    expires_at: "",
  });
  const [admTemplatesRows, setAdmTemplatesRows] = useState<AdminTemplateRow[]>([]);
  const [admTemplateForm, setAdmTemplateForm] = useState({ key: "", text: "" });
  const [admTemplateEdit, setAdmTemplateEdit] = useState<{ key: string; text: string }>({ key: "", text: "" });
  const [admGiftCodesRows, setAdmGiftCodesRows] = useState<AdminGiftCodeRow[]>([]);
  const [admGiftType, setAdmGiftType] = useState<"mini" | "standard" | "premium">("standard");
  const [admGiftLastCode, setAdmGiftLastCode] = useState("");

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
    const hasWebSession = hasWebSessionToken();
    if (!tgUser && !IS_DEV && !hasWebSession) {
      setWebLoginRequired(true);
      setError("");
      setLoading(false);
      return;
    }
    if (!tgUser && IS_DEV && !hasWebSession) {
      // Dev mode: use mock data for design preview
      setUser(MOCK_USER);
      setDash(MOCK_DASH);
      setNodes(MOCK_NODES);
      setPoints(MOCK_POINTS);
      setClientApps(null);
      setTickets([]);
      setSelectedNodeCode("nl");
      setLoading(false);
      return;
    }
    try {
      setLoading(true);
      setError("");
      setWebLoginRequired(false);

      let u: UserPayload;
      let d: DashboardSnapshot;
      let n: NodeStatus[];
      let t: TicketInfo[];
      let p: PointsSnapshot | null;
      let apps: ClientAppsPayload | null;

      if (tgUser) {
        [u, d, n, t, p, apps] = await Promise.all([
          fetchUser(tgUser.id),
          fetchDashboard(),
          fetchNodeStatus(),
          fetchTickets(20),
          getPoints().catch(() => null),
          fetchClientApps().catch(() => null),
        ]);
      } else {
        d = await fetchDashboard();
        [u, n, t, p, apps] = await Promise.all([
          fetchUser(d.tg_id),
          fetchNodeStatus(),
          fetchTickets(20),
          getPoints().catch(() => null),
          fetchClientApps().catch(() => null),
        ]);
      }

      setUser(u);
      setDash(d);
      setNodes(n);
      setTickets(t);
      setPoints(p);
      setClientApps(apps);
      if (n.length > 0) setSelectedNodeCode(n[0].code);
      if (u.is_admin) {
        const [s, at, an, m, au, promos, templates, giftCodes] = await Promise.all([
          adminSummary(),
          adminTickets("", 30),
          adminNodesHealth(),
          adminMetricsStatus(),
          adminUsers("", 40, 0),
          adminPromos(250),
          adminTemplates(250),
          adminGiftCodes(100),
        ]);
        setAdmSummary(s);
        setAdmTickets(at);
        setAdmNodes(an);
        setAdmMetrics(m);
        setAdmUsersRows(au);
        setAdmPromosRows(promos);
        setAdmTemplatesRows(templates);
        setAdmGiftCodesRows(giftCodes);
        if (templates.length > 0) {
          setAdmTemplateEdit({ key: templates[0].key, text: templates[0].text });
        }
        if (au.length > 0) {
          const first = au[0].tg_id;
          setAdmSelectedUserId(first);
          setAdmUserCardData(await adminUserCard(first));
        } else {
          setAdmSelectedUserId(null);
          setAdmUserCardData(null);
        }
      }
      void trackEvent("opened_webapp", "webapp", { tab: "status" });
    } catch (e: unknown) {
      const msg = String((e as { message?: string })?.message || e);
      if (!tgUser && msg.includes("Telegram auth required")) {
        setWebLoginRequired(true);
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  }

  async function reloadAdminCore() {
    const [s, an, m] = await Promise.all([adminSummary(), adminNodesHealth(), adminMetricsStatus()]);
    setAdmSummary(s);
    setAdmNodes(an);
    setAdmMetrics(m);
  }

  async function reloadAdminUsers(query = admUsersQuery) {
    const rows = await adminUsers(query, 60, 0);
    setAdmUsersRows(rows);
    if (!rows.length) {
      setAdmSelectedUserId(null);
      setAdmUserCardData(null);
      return;
    }
    if (!admSelectedUserId || !rows.some((u) => u.tg_id === admSelectedUserId)) {
      setAdmSelectedUserId(rows[0].tg_id);
      setAdmUserCardData(await adminUserCard(rows[0].tg_id));
    }
  }

  async function openAdminUser(tgId: number) {
    setAdmSelectedUserId(tgId);
    setAdmUserCardData(await adminUserCard(tgId));
  }

  async function reloadAdminTickets(status = admTicketFilter) {
    const rows = await adminTickets(status, 40);
    setAdmTickets(rows);
    if (admTicket && !rows.some((t) => t.id === admTicket.id)) {
      setAdmTicket(null);
    }
  }

  async function reloadAdminPromos() {
    setAdmPromosRows(await adminPromos(250));
  }

  async function reloadAdminTemplates() {
    const rows = await adminTemplates(250);
    setAdmTemplatesRows(rows);
    if (!rows.length) {
      setAdmTemplateEdit({ key: "", text: "" });
      return;
    }
    if (!admTemplateEdit.key || !rows.some((t) => t.key === admTemplateEdit.key)) {
      setAdmTemplateEdit({ key: rows[0].key, text: rows[0].text });
    }
  }

  async function reloadAdminGiftCodes() {
    setAdmGiftCodesRows(await adminGiftCodes(100));
  }

  async function runAdminAction(action: () => Promise<void>, successText: string) {
    try {
      setAdmBusy(true);
      setAdmError("");
      await action();
      setBanner(successText);
      pulse("success");
    } catch (e: unknown) {
      const msg = String((e as { message?: string })?.message || e);
      setAdmError(msg);
      setBanner("Ошибка действия администратора");
      pulse("error");
    } finally {
      setAdmBusy(false);
    }
  }

  useEffect(() => {
    void loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!webLoginRequired || tgUser || IS_DEV) return;
    const host = document.getElementById("tg-login-widget");
    if (!host) return;
    host.innerHTML = "";
    const botName = ((import.meta as any).env?.VITE_TELEGRAM_LOGIN_BOT || "portal_service_bot").trim();

    window.onTelegramAuth = async (loginUser: any) => {
      setWebLoginBusy(true);
      setWebLoginError("");
      try {
        const res = await authByTelegramWebLogin(loginUser);
        if (!res?.token) throw new Error("Missing web session token");
        setWebSessionToken(res.token);
        setWebLoginRequired(false);
        await loadAll();
      } catch (e: unknown) {
        setWebLoginError(String((e as { message?: string })?.message || e));
      } finally {
        setWebLoginBusy(false);
      }
    };

    const script = document.createElement("script");
    script.async = true;
    script.src = "https://telegram.org/js/telegram-widget.js?22";
    script.setAttribute("data-telegram-login", botName);
    script.setAttribute("data-size", "large");
    script.setAttribute("data-userpic", "false");
    script.setAttribute("data-request-access", "write");
    script.setAttribute("data-radius", "12");
    script.setAttribute("data-onauth", "onTelegramAuth(user)");
    host.appendChild(script);

    return () => {
      host.innerHTML = "";
      delete window.onTelegramAuth;
    };
  }, [webLoginRequired, tgUser]);

  function pulse(kind: "success" | "error") {
    if (user?.features?.haptic ?? true) haptic(kind);
  }

  function onLogoutWebSession() {
    clearWebSessionToken();
    setUser(null);
    setDash(null);
    setNodes([]);
    setTickets([]);
    setPoints(null);
    setWebLoginRequired(true);
    setError("");
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

  async function onRedeemGift() {
    const code = giftCode.trim();
    if (!code) return;
    try {
      const res = await redeemGiftCode(code);
      setGiftRedeemResult(`Код активирован: +${res?.days ?? 0} дней`);
      setGiftCode("");
      await loadAll();
      pulse("success");
    } catch (e: unknown) {
      setGiftRedeemResult(String((e as { message?: string })?.message || e));
      pulse("error");
    }
  }

  async function onAdminSearchUsers() {
    await runAdminAction(async () => {
      await reloadAdminUsers(admUsersQuery.trim());
    }, "Список пользователей обновлён");
  }

  async function onAdminCreateManual() {
    const name = admManualForm.display_name.trim();
    const days = Math.max(1, Number(admManualForm.days || 0));
    if (!name) {
      setAdmError("Укажите имя ручного профиля");
      return;
    }
    await runAdminAction(async () => {
      const res = await adminManualCreate({ display_name: name, days });
      setAdmManualLastLink(res.user.subscription_url || "");
      setAdmManualForm({ display_name: "", days: 30 });
      await reloadAdminUsers("");
      await reloadAdminCore();
      if (res.user?.tg_id) {
        await openAdminUser(Number(res.user.tg_id));
      }
    }, "Ручной профиль создан");
  }

  async function onAdminSendUserMessage() {
    if (!admSelectedUserId) return;
    const text = admUserMessageBody.trim();
    if (!text) {
      setAdmError("Текст сообщения пустой");
      return;
    }
    await runAdminAction(async () => {
      await adminUserMessage(admSelectedUserId, text);
      setAdmUserMessageBody("");
    }, "Сообщение отправлено пользователю");
  }

  async function onAdminManualExtend(days: number) {
    if (!admSelectedUserId) return;
    await runAdminAction(async () => {
      await adminManualExtend(admSelectedUserId, Math.max(1, days));
      await openAdminUser(admSelectedUserId);
      await reloadAdminUsers(admUsersQuery.trim());
      await reloadAdminCore();
    }, `Продлено на ${days} дней`);
  }

  async function onAdminManualBlock(blocked: boolean) {
    if (!admSelectedUserId) return;
    await runAdminAction(async () => {
      await adminManualBlock(admSelectedUserId, blocked);
      await openAdminUser(admSelectedUserId);
      await reloadAdminUsers(admUsersQuery.trim());
      await reloadAdminCore();
    }, blocked ? "Профиль заблокирован" : "Профиль разблокирован");
  }

  async function onAdminManualRegenerate() {
    if (!admSelectedUserId) return;
    await runAdminAction(async () => {
      const res = await adminManualRegenerateToken(admSelectedUserId);
      setAdmManualLastLink(res.subscription_url || "");
    }, "Токен пересоздан");
  }

  async function onAdminTicketReply() {
    if (!admTicket) return;
    const body = admReplyBody.trim();
    if (!body) {
      setAdmError("Ответ пустой");
      return;
    }
    await runAdminAction(async () => {
      const updated = await adminTicketReply(admTicket.id, body);
      setAdmTicket(updated);
      setAdmReplyBody("");
      await reloadAdminTickets(admTicketFilter);
      await reloadAdminCore();
    }, "Ответ отправлен");
  }

  async function onAdminTicketSetStatus(status: "open" | "in_progress" | "closed") {
    if (!admTicket) return;
    await runAdminAction(async () => {
      const updated = await adminTicketStatus(admTicket.id, status);
      setAdmTicket(updated);
      await reloadAdminTickets(admTicketFilter);
      await reloadAdminCore();
    }, `Статус тикета: ${status}`);
  }

  async function onAdminNodesSync() {
    const maybeTgId = Number(admNodeSyncTgId.trim() || 0);
    await runAdminAction(async () => {
      if (maybeTgId > 0) {
        await adminNodesSync({ tg_id: maybeTgId });
      } else {
        await adminNodesSync({
          segment: admNodeSyncSegment,
          limit: Math.max(1, Math.min(1000, Number(admNodeSyncLimit || 0) || 100)),
        });
      }
      await reloadAdminCore();
      await reloadAdminTickets(admTicketFilter);
      await reloadAdminUsers(admUsersQuery.trim());
    }, "Синхронизация нод завершена");
  }

  async function onAdminBroadcast() {
    const text = admBroadcastText.trim();
    if (!text) {
      setAdmError("Введите текст рассылки");
      return;
    }
    await runAdminAction(async () => {
      const res = await adminBroadcast({
        text,
        segment: admBroadcastSegment,
        limit: Math.max(1, Math.min(1000, Number(admBroadcastLimit || 0) || 100)),
      });
      setAdmBroadcastResult(`Отправлено: ${res.sent}, ошибок: ${res.failed}, попыток: ${res.attempted}`);
      await reloadAdminCore();
    }, "Рассылка запущена");
  }

  async function onAdminCreatePromo() {
    const code = admPromoForm.code.trim().toUpperCase();
    if (!code) {
      setAdmError("Укажите код промокода");
      return;
    }
    await runAdminAction(async () => {
      await adminPromoCreate({
        code,
        promo_type: admPromoForm.promo_type,
        value: Math.max(1, Number(admPromoForm.value || 0)),
        uses_left: Number(admPromoForm.uses_left || 0),
        expires_at: admPromoForm.expires_at?.trim() ? admPromoForm.expires_at.trim() : null,
      });
      setAdmPromoForm({ code: "", promo_type: admPromoForm.promo_type, value: 14, uses_left: 100, expires_at: "" });
      await reloadAdminPromos();
    }, `Промокод ${code} создан`);
  }

  async function onAdminPatchPromo(row: AdminPromoRow) {
    await runAdminAction(async () => {
      await adminPromoUpdate(row.code, {
        promo_type: row.promo_type === "discount" ? "discount" : "days",
        value: Math.max(1, Number(row.value || 0)),
        uses_left: Number(row.uses_left || 0),
        expires_at: row.expires_at ? row.expires_at : "",
      });
      await reloadAdminPromos();
    }, `Промокод ${row.code} обновлён`);
  }

  async function onAdminDeletePromo(code: string) {
    await runAdminAction(async () => {
      await adminPromoDelete(code);
      await reloadAdminPromos();
    }, `Промокод ${code} удалён`);
  }

  async function onAdminCreateTemplate() {
    const key = admTemplateForm.key.trim().toLowerCase();
    const text = admTemplateForm.text.trim();
    if (!key || !text) {
      setAdmError("Укажите ключ и текст шаблона");
      return;
    }
    await runAdminAction(async () => {
      await adminTemplateCreate({ key, text });
      setAdmTemplateForm({ key: "", text: "" });
      await reloadAdminTemplates();
    }, `Шаблон ${key} создан`);
  }

  async function onAdminPatchTemplate() {
    const key = admTemplateEdit.key.trim().toLowerCase();
    const text = admTemplateEdit.text.trim();
    if (!key || !text) {
      setAdmError("Выберите шаблон и введите текст");
      return;
    }
    await runAdminAction(async () => {
      await adminTemplateUpdate(key, { text });
      await reloadAdminTemplates();
    }, `Шаблон ${key} обновлён`);
  }

  async function onAdminDeleteTemplate(key: string) {
    await runAdminAction(async () => {
      await adminTemplateDelete(key);
      if (admTemplateEdit.key === key) {
        setAdmTemplateEdit({ key: "", text: "" });
      }
      await reloadAdminTemplates();
    }, `Шаблон ${key} удалён`);
  }

  async function onAdminCreateGiftCode() {
    await runAdminAction(async () => {
      const res = await adminGiftCodeCreate(admGiftType);
      const code = res?.gift_code?.code || "";
      setAdmGiftLastCode(code);
      if (code) {
        await copyText(code);
      }
      await reloadAdminGiftCodes();
    }, "Gift-код создан и скопирован");
  }

  function clientOptionsForPlatform(): Array<{ title: string; url: string }> {
    if (platform === "ios") {
      return [
        { title: "Streisand", url: "https://apps.apple.com/app/streisand/id6450534064" },
        { title: "Happ", url: "https://apps.apple.com/app/happ-proxy-utility/id6504287215" },
      ];
    }
    if (platform === "android") {
      const fromApi = [
        { title: "Google Play", url: clientApps?.android?.play_url || "" },
        { title: "APK", url: clientApps?.android?.apk_url || "" },
        { title: "Mirror", url: clientApps?.android?.mirror_url || "" },
      ].filter((x) => x.url.trim().length > 0);
      if (fromApi.length) return fromApi;
      return [
        { title: "Hiddify", url: "https://play.google.com/store/apps/details?id=app.hiddify.com" },
        { title: "v2rayNG", url: "https://github.com/2dust/v2rayNG/releases" },
      ];
    }
    const desktopFromApi = [
      { title: "Windows EXE", url: clientApps?.windows?.exe_url || "" },
      { title: "Windows Mirror", url: clientApps?.windows?.mirror_url || "" },
    ].filter((x) => x.url.trim().length > 0);
    if (desktopFromApi.length) return desktopFromApi;
    return [
      { title: "Hiddify Next", url: "https://github.com/hiddify/hiddify-next/releases" },
      { title: "Nekoray", url: "https://github.com/MatsuriDayo/nekoray/releases" },
    ];
  }

  function docsLinkForConnect(): string {
    return firstNonEmpty(clientApps?.docs_url, user?.support?.new_ticket_link, "https://t.me/" + (user?.support?.username || "portal_privacy_helpbot"));
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

  if (webLoginRequired) {
    return (
      <div className="app">
        <div className="grain" />
        <section className="card">
          <div className="section-tag">[WEB LOGIN]</div>
          <div className="card__title">Вход через Telegram</div>
          <div className="muted" style={{ marginBottom: 12 }}>
            Авторизуйтесь через Telegram Login, чтобы открыть личный кабинет в браузере.
          </div>
          <div id="tg-login-widget" style={{ minHeight: 56 }} />
          {webLoginBusy ? <div className="muted" style={{ marginTop: 10 }}>Проверяю аккаунт...</div> : null}
          {webLoginError ? <div className="muted" style={{ marginTop: 10, color: "#ff5a5f" }}>{webLoginError}</div> : null}
          <div className="actions" style={{ marginTop: 12 }}>
            <button className="btn btn--ghost" type="button" onClick={() => openLink("https://t.me/portal_service_bot")}>
              <span style={{ position: "relative", zIndex: 1 }}>Открыть бота</span>
            </button>
            {hasWebSessionToken() ? (
              <button className="btn btn--ghost" type="button" onClick={onLogoutWebSession}>
                <span style={{ position: "relative", zIndex: 1 }}>Сбросить web-сессию</span>
              </button>
            ) : null}
          </div>
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

      {banner ? <div className="banner" aria-live="polite">{banner}</div> : null}

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
          {!tgUser && hasWebSessionToken() ? (
            <div className="actions" style={{ marginTop: 8 }}>
              <button className="btn btn--ghost" type="button" onClick={onLogoutWebSession}>
                <span style={{ position: "relative", zIndex: 1 }}>Выйти из web-сессии</span>
              </button>
            </div>
          ) : null}
          <pre className="mono legal">{OFFER_FULL}</pre>
        </section>
      ) : null}

      {user.is_admin ? (
        <section className="card card-enter">
          <div className="section-tag">[ADMIN]</div>
          <div className="card__title">Панель оператора</div>
          <div className="chips">
            {ADMIN_TABS.map((tab) => (
              <button
                key={tab.id}
                className={aTab === tab.id ? "chip chip--active" : "chip"}
                type="button"
                onClick={() => setATab(tab.id)}
              >
                {tab.label}
              </button>
            ))}
          </div>
          {admError ? (
            <div className="pill pill--bad" style={{ marginTop: 12 }}>
              {admError}
            </div>
          ) : null}

          {aTab === "summary" && admSummary ? (
            <>
              <div className="grid2" style={{ marginTop: 12 }}>
                <div className="metric">
                  <div className="metric__k">Всего пользователей</div>
                  <div className="metric__v">{admSummary.users.total}</div>
                </div>
                <div className="metric">
                  <div className="metric__k">Активные</div>
                  <div className="metric__v">{admSummary.users.active}</div>
                </div>
                <div className="metric">
                  <div className="metric__k">Тикеты open</div>
                  <div className="metric__v">{admSummary.tickets.open}</div>
                </div>
                <div className="metric">
                  <div className="metric__k">Ноды healthy</div>
                  <div className="metric__v">{`${admSummary.nodes.healthy}/${admSummary.nodes.total}`}</div>
                </div>
              </div>
              <div className="pill" style={{ marginBottom: 12 }}>
                {admMetrics
                  ? `Метрики: ${admMetrics.status.toUpperCase()} | age=${admMetrics.age_seconds ?? "-"}s | stale>${admMetrics.stale_after_seconds}s`
                  : "Метрики: loading..."}
              </div>
              <div className="list">
                {admSummary.top_nodes.map((n) => (
                  <div key={n.code} className="row">
                    <div>
                      <div className="row__title">{`[${n.code.toUpperCase()}] score ${n.health_score.toFixed(2)}`}</div>
                      <div className="row__sub">{`lat=${n.panel_latency_ms ?? "-"}ms | clients=${n.active_clients}`}</div>
                    </div>
                    <div className="pill">{n.last_health_at ? fmtDate(n.last_health_at) : "-"}</div>
                  </div>
                ))}
              </div>
            </>
          ) : null}

          {aTab === "users" ? (
            <>
              <div className="actions" style={{ marginTop: 12 }}>
                <input
                  className="field"
                  aria-label="User search"
                  value={admUsersQuery}
                  onChange={(e) => setAdmUsersQuery(e.target.value)}
                  placeholder="Поиск: @username или tg_id"
                />
                <button className="btn btn--inline" type="button" disabled={admBusy} onClick={() => void onAdminSearchUsers()}>
                  Найти
                </button>
              </div>

              <div className="list">
                {admUsersRows.map((u) => (
                  <button
                    key={u.tg_id}
                    className="row row--btn"
                    type="button"
                    onClick={() =>
                      void runAdminAction(async () => {
                        await openAdminUser(u.tg_id);
                      }, `Открыт профиль ${u.tg_id}`)
                    }
                  >
                    <div>
                      <div className="row__title">
                        {u.username ? `@${u.username}` : `ID ${u.tg_id}`} {u.is_manual ? "[MANUAL]" : ""}
                      </div>
                      <div className="row__sub">{`${u.sub_type} | active=${u.is_active ? "yes" : "no"} | exp=${fmtDate(u.expiry_at)}`}</div>
                    </div>
                    <div className="pill">{u.stars_paid}⭐</div>
                  </button>
                ))}
              </div>

              {admUserCardData ? (
                <>
                  <div className="divider" />
                  <div className="card__title">Карточка пользователя</div>
                  <div className="list">
                    <div className="row">
                      <div>
                        <div className="row__title">
                          {admUserCardData.user.username
                            ? `@${admUserCardData.user.username}`
                            : admUserCardData.user.display_name || `ID ${admUserCardData.user.tg_id}`}
                        </div>
                        <div className="row__sub">{`ID=${admUserCardData.user.tg_id} | ${admUserCardData.user.sub_type} | active=${admUserCardData.user.is_active ? "yes" : "no"}`}</div>
                      </div>
                    </div>
                    <div className="row">
                      <div className="row__sub">{`Expires: ${fmtDate(admUserCardData.user.expiry_at)} | stars=${admUserCardData.user.stars_paid} | referral=${admUserCardData.user.referral_count}`}</div>
                    </div>
                  </div>

                  {admUserCardData.user.is_manual ? (
                    <div className="actions" style={{ marginTop: 10 }}>
                      <button className="btn btn--ghost btn--inline" type="button" disabled={admBusy} onClick={() => void onAdminManualExtend(7)}>
                        +7 дней
                      </button>
                      <button className="btn btn--ghost btn--inline" type="button" disabled={admBusy} onClick={() => void onAdminManualExtend(30)}>
                        +30 дней
                      </button>
                      <button
                        className="btn btn--ghost btn--inline"
                        type="button"
                        disabled={admBusy}
                        onClick={() => void onAdminManualBlock(admUserCardData.user.is_active)}
                      >
                        {admUserCardData.user.is_active ? "Блок" : "Разблок"}
                      </button>
                      <button className="btn btn--ghost btn--inline" type="button" disabled={admBusy} onClick={() => void onAdminManualRegenerate()}>
                        Новый токен
                      </button>
                    </div>
                  ) : null}

                  <textarea
                    className="field field--area"
                    aria-label="Message to user"
                    value={admUserMessageBody}
                    onChange={(e) => setAdmUserMessageBody(e.target.value)}
                    placeholder="Сообщение пользователю"
                  />
                  <div className="actions" style={{ marginTop: 8 }}>
                    <button className="btn" type="button" disabled={admBusy} onClick={() => void onAdminSendUserMessage()}>
                      <span style={{ position: "relative", zIndex: 1 }}>Отправить сообщение</span>
                    </button>
                  </div>
                </>
              ) : null}

              <div className="divider" />
              <div className="card__title">Создание manual-профиля</div>
              <input
                className="field"
                aria-label="Manual profile name"
                value={admManualForm.display_name}
                onChange={(e) => setAdmManualForm((v) => ({ ...v, display_name: e.target.value }))}
                placeholder="Имя профиля"
              />
              <div className="actions" style={{ marginTop: 8 }}>
                <input
                  className="field field--compact"
                  aria-label="Manual profile days"
                  value={String(admManualForm.days)}
                  onChange={(e) =>
                    setAdmManualForm((v) => ({ ...v, days: Math.max(1, Number(e.target.value || 0) || 1) }))
                  }
                  placeholder="Дней"
                />
                <button className="btn" type="button" disabled={admBusy} onClick={() => void onAdminCreateManual()}>
                  <span style={{ position: "relative", zIndex: 1 }}>Создать</span>
                </button>
              </div>
              {admManualLastLink ? (
                <div className="actions" style={{ marginTop: 8 }}>
                  <button className="btn btn--ghost" type="button" onClick={() => void copyText(admManualLastLink)}>
                    <span style={{ position: "relative", zIndex: 1 }}>Скопировать ключ manual</span>
                  </button>
                </div>
              ) : null}
            </>
          ) : null}

          {aTab === "tickets" ? (
            <>
              <div className="chips" style={{ marginTop: 12 }}>
                {[
                  { key: "", label: "Все" },
                  { key: "open", label: "Open" },
                  { key: "in_progress", label: "InProgress" },
                  { key: "closed", label: "Closed" },
                ].map((f) => (
                  <button
                    key={f.key || "all"}
                    className={admTicketFilter === f.key ? "chip chip--active" : "chip"}
                    type="button"
                    onClick={() =>
                      void runAdminAction(async () => {
                        setAdmTicketFilter(f.key);
                        const rows = await adminTickets(f.key, 40);
                        setAdmTickets(rows);
                        setAdmTicket(null);
                      }, "Список тикетов обновлён")
                    }
                  >
                    {f.label}
                  </button>
                ))}
              </div>
              <div className="list">
                {admTickets.map((t) => (
                  <button
                    key={t.id}
                    className="row row--btn"
                    type="button"
                    onClick={() =>
                      void runAdminAction(async () => {
                        setAdmTicket(await getTicket(t.id));
                      }, `Открыт тикет #${t.id}`)
                    }
                  >
                    <div>
                      <div className="row__title">{`#${t.id} ${t.status_title}`}</div>
                      <div className="row__sub">{`${t.user_tg_id} | ${t.last_message_preview || "-"}`}</div>
                    </div>
                  </button>
                ))}
              </div>

              {admTicket ? (
                <>
                  <div className="divider" />
                  <div className="chips">
                    <button className="chip" type="button" disabled={admBusy} onClick={() => void onAdminTicketSetStatus("open")}>
                      open
                    </button>
                    <button className="chip" type="button" disabled={admBusy} onClick={() => void onAdminTicketSetStatus("in_progress")}>
                      in_progress
                    </button>
                    <button className="chip" type="button" disabled={admBusy} onClick={() => void onAdminTicketSetStatus("closed")}>
                      closed
                    </button>
                  </div>
                  <div className="list">
                    {admTicket.messages.map((m) => (
                      <div key={m.id} className={m.sender_role === "admin" ? "msg msg--op" : "msg msg--mine"}>
                        <div className="row__sub">{`${m.sender_role} | ${fmtDate(m.created_at)}`}</div>
                        <div>{m.body}</div>
                      </div>
                    ))}
                  </div>
                  <textarea
                    className="field field--area"
                    aria-label="Operator reply"
                    value={admReplyBody}
                    onChange={(e) => setAdmReplyBody(e.target.value)}
                    placeholder="Ответ оператора"
                  />
                  <div className="actions" style={{ marginTop: 8 }}>
                    <button className="btn" type="button" disabled={admBusy} onClick={() => void onAdminTicketReply()}>
                      <span style={{ position: "relative", zIndex: 1 }}>Отправить ответ</span>
                    </button>
                  </div>
                </>
              ) : null}
            </>
          ) : null}

          {aTab === "nodes" ? (
            <>
              <div className="actions" style={{ marginTop: 12 }}>
                <input
                  className="field field--compact"
                  aria-label="Node sync limit"
                  value={admNodeSyncLimit}
                  onChange={(e) => setAdmNodeSyncLimit(Math.max(1, Number(e.target.value || 0) || 1))}
                  placeholder="limit"
                />
                <input
                  className="field field--compact"
                  aria-label="Node sync user id"
                  value={admNodeSyncTgId}
                  onChange={(e) => setAdmNodeSyncTgId(e.target.value)}
                  placeholder="tg_id (optional)"
                />
              </div>
              <div className="chips" style={{ marginTop: 8 }}>
                {["active", "free", "paid"].map((seg) => (
                  <button
                    key={seg}
                    className={admNodeSyncSegment === seg ? "chip chip--active" : "chip"}
                    type="button"
                    onClick={() => setAdmNodeSyncSegment(seg)}
                  >
                    {seg}
                  </button>
                ))}
              </div>
              <div className="actions" style={{ marginTop: 8 }}>
                <button className="btn" type="button" disabled={admBusy} onClick={() => void onAdminNodesSync()}>
                  <span style={{ position: "relative", zIndex: 1 }}>Sync нод</span>
                </button>
              </div>

              <div className="list">
                {admNodes.map((n) => (
                  <div key={n.code} className="row">
                    <div>
                      <div className="row__title">{`[${n.code.toUpperCase()}] ${n.name}`}</div>
                      <div className="row__sub">{`score=${n.health_score.toFixed(2)} | lat=${n.panel_latency_ms ?? "-"}ms | err=${(n.panel_error_rate * 100).toFixed(1)}% | clients=${n.active_clients}`}</div>
                    </div>
                    <div className={n.is_healthy ? "pill pill--ok" : "pill pill--bad"}>{n.is_healthy ? "OK" : "STALE"}</div>
                  </div>
                ))}
              </div>
            </>
          ) : null}

          {aTab === "broadcast" ? (
            <>
              <div className="chips" style={{ marginTop: 12 }}>
                {["all_active", "free", "paid", "expired"].map((seg) => (
                  <button
                    key={seg}
                    className={admBroadcastSegment === seg ? "chip chip--active" : "chip"}
                    type="button"
                    onClick={() => setAdmBroadcastSegment(seg)}
                  >
                    {seg}
                  </button>
                ))}
              </div>
              <div className="actions" style={{ marginTop: 8 }}>
                <input
                  className="field field--compact"
                  aria-label="Broadcast limit"
                  value={admBroadcastLimit}
                  onChange={(e) => setAdmBroadcastLimit(Math.max(1, Number(e.target.value || 0) || 1))}
                  placeholder="limit"
                />
              </div>
              <textarea
                className="field field--area"
                aria-label="Broadcast text"
                value={admBroadcastText}
                onChange={(e) => setAdmBroadcastText(e.target.value)}
                placeholder="Текст рассылки"
              />
              <div className="actions" style={{ marginTop: 8 }}>
                <button className="btn" type="button" disabled={admBusy} onClick={() => void onAdminBroadcast()}>
                  <span style={{ position: "relative", zIndex: 1 }}>Запустить рассылку</span>
                </button>
              </div>
              {admBroadcastResult ? <div className="muted" style={{ marginTop: 8 }}>{admBroadcastResult}</div> : null}
            </>
          ) : null}

          {aTab === "promos" ? (
            <>
              <div className="card__title" style={{ marginTop: 12 }}>Создать промокод</div>
              <div className="actions">
                <input
                  className="field field--compact"
                  aria-label="Promo code"
                  value={admPromoForm.code}
                  onChange={(e) => setAdmPromoForm((v) => ({ ...v, code: e.target.value.toUpperCase() }))}
                  placeholder="CODE"
                />
                <input
                  className="field field--compact"
                  aria-label="Promo value"
                  value={String(admPromoForm.value)}
                  onChange={(e) => setAdmPromoForm((v) => ({ ...v, value: Math.max(1, Number(e.target.value || 0) || 1) }))}
                  placeholder="value"
                />
                <input
                  className="field field--compact"
                  aria-label="Promo uses"
                  value={String(admPromoForm.uses_left)}
                  onChange={(e) => setAdmPromoForm((v) => ({ ...v, uses_left: Number(e.target.value || 0) || 0 }))}
                  placeholder="uses (-1∞)"
                />
              </div>
              <div className="chips" style={{ marginTop: 8 }}>
                {(["days", "discount"] as const).map((type) => (
                  <button
                    key={type}
                    className={admPromoForm.promo_type === type ? "chip chip--active" : "chip"}
                    type="button"
                    onClick={() => setAdmPromoForm((v) => ({ ...v, promo_type: type }))}
                  >
                    {type}
                  </button>
                ))}
              </div>
              <div className="actions" style={{ marginTop: 8 }}>
                <input
                  className="field"
                  aria-label="Promo expires at"
                  value={admPromoForm.expires_at}
                  onChange={(e) => setAdmPromoForm((v) => ({ ...v, expires_at: e.target.value }))}
                  placeholder="expires_at ISO (опционально)"
                />
                <button className="btn btn--inline" type="button" disabled={admBusy} onClick={() => void onAdminCreatePromo()}>
                  Создать
                </button>
              </div>

              <div className="divider" />
              <div className="card__title">Список промокодов</div>
              <div className="list">
                {admPromosRows.map((p) => (
                  <div key={p.code} className="row" style={{ alignItems: "flex-start", flexDirection: "column", gap: 8 }}>
                    <div className="row__title">{`${p.code} | ${p.promo_type}`}</div>
                    <div className="row__sub">{`used=${p.used_count} | left=${p.uses_left} | exp=${fmtDate(p.expires_at)}`}</div>
                    <div className="actions">
                      <button
                        className="chip"
                        type="button"
                        onClick={() =>
                          setAdmPromosRows((rows) =>
                            rows.map((x) =>
                              x.code === p.code
                                ? { ...x, promo_type: x.promo_type === "discount" ? "days" : "discount" }
                                : x,
                            ),
                          )
                        }
                      >
                        {p.promo_type}
                      </button>
                      <input
                        className="field field--compact"
                        aria-label={`Promo ${p.code} value`}
                        value={String(p.value)}
                        onChange={(e) =>
                          setAdmPromosRows((rows) =>
                            rows.map((x) => (x.code === p.code ? { ...x, value: Math.max(1, Number(e.target.value || 0) || 1) } : x)),
                          )
                        }
                        placeholder="value"
                      />
                      <input
                        className="field field--compact"
                        aria-label={`Promo ${p.code} uses`}
                        value={String(p.uses_left)}
                        onChange={(e) =>
                          setAdmPromosRows((rows) =>
                            rows.map((x) => (x.code === p.code ? { ...x, uses_left: Number(e.target.value || 0) || 0 } : x)),
                          )
                        }
                        placeholder="uses"
                      />
                      <input
                        className="field"
                        aria-label={`Promo ${p.code} expires at`}
                        value={p.expires_at || ""}
                        onChange={(e) =>
                          setAdmPromosRows((rows) =>
                            rows.map((x) => (x.code === p.code ? { ...x, expires_at: e.target.value } : x)),
                          )
                        }
                        placeholder="expires_at ISO"
                      />
                      <button className="chip" type="button" disabled={admBusy} onClick={() => void onAdminPatchPromo(p)}>
                        Сохранить
                      </button>
                      <button className="chip" type="button" disabled={admBusy} onClick={() => void onAdminDeletePromo(p.code)}>
                        Удалить
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : null}

          {aTab === "templates" ? (
            <>
              <div className="card__title" style={{ marginTop: 12 }}>Создать шаблон рассылки</div>
              <div className="actions">
                <input
                  className="field field--compact"
                  aria-label="Template key"
                  value={admTemplateForm.key}
                  onChange={(e) => setAdmTemplateForm((v) => ({ ...v, key: e.target.value.toLowerCase() }))}
                  placeholder="key"
                />
              </div>
              <textarea
                className="field field--area"
                aria-label="Template text"
                value={admTemplateForm.text}
                onChange={(e) => setAdmTemplateForm((v) => ({ ...v, text: e.target.value }))}
                placeholder="Текст шаблона"
              />
              <div className="actions" style={{ marginTop: 8 }}>
                <button className="btn btn--inline" type="button" disabled={admBusy} onClick={() => void onAdminCreateTemplate()}>
                  Создать
                </button>
              </div>

              <div className="divider" />
              <div className="card__title">Редактирование шаблона</div>
              <div className="chips" style={{ marginTop: 8 }}>
                {admTemplatesRows.map((t) => (
                  <button
                    key={t.key}
                    className={admTemplateEdit.key === t.key ? "chip chip--active" : "chip"}
                    type="button"
                    onClick={() => setAdmTemplateEdit({ key: t.key, text: t.text })}
                  >
                    {t.key}
                  </button>
                ))}
              </div>
              <textarea
                className="field field--area"
                aria-label="Template edit text"
                value={admTemplateEdit.text}
                onChange={(e) => setAdmTemplateEdit((v) => ({ ...v, text: e.target.value }))}
                placeholder="Выберите шаблон для редактирования"
              />
              <div className="actions" style={{ marginTop: 8 }}>
                <button className="btn btn--inline" type="button" disabled={admBusy || !admTemplateEdit.key} onClick={() => void onAdminPatchTemplate()}>
                  Сохранить
                </button>
                <button
                  className="btn btn--inline"
                  type="button"
                  disabled={admBusy || !admTemplateEdit.key}
                  onClick={() => void onAdminDeleteTemplate(admTemplateEdit.key)}
                >
                  Удалить
                </button>
              </div>
            </>
          ) : null}

          {aTab === "giftcodes" ? (
            <>
              <div className="card__title" style={{ marginTop: 12 }}>Генерация gift-кодов</div>
              <div className="chips">
                {GIFT_CODE_CHOICES.map((g) => (
                  <button
                    key={g.key}
                    className={admGiftType === g.key ? "chip chip--active" : "chip"}
                    type="button"
                    onClick={() => setAdmGiftType(g.key)}
                  >
                    {`${g.label} ${g.days}д / ${g.stars}⭐`}
                  </button>
                ))}
              </div>
              <div className="actions" style={{ marginTop: 8 }}>
                <button className="btn" type="button" disabled={admBusy} onClick={() => void onAdminCreateGiftCode()}>
                  <span style={{ position: "relative", zIndex: 1 }}>Создать gift-код</span>
                </button>
                <button className="btn btn--ghost" type="button" disabled={!admGiftLastCode} onClick={() => void copyText(admGiftLastCode)}>
                  <span style={{ position: "relative", zIndex: 1 }}>Скопировать последний</span>
                </button>
              </div>
              {admGiftLastCode ? <div className="pill" style={{ marginTop: 8 }}>{admGiftLastCode}</div> : null}
              <div className="list" style={{ marginTop: 10 }}>
                {admGiftCodesRows.map((g) => (
                  <div key={g.code} className="row">
                    <div>
                      <div className="row__title">{`${g.code} | ${g.card_type}`}</div>
                      <div className="row__sub">{`${g.days} дней | ${g.stars}⭐ | ${fmtDate(g.created_at)}`}</div>
                    </div>
                    <div className={g.redeemed_by ? "pill pill--ok" : "pill"}>{g.redeemed_by ? "Погашен" : "Новый"}</div>
                  </div>
                ))}
              </div>
            </>
          ) : null}
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
            {dash.free_next_reset_at ? (
              <div className="muted" style={{ marginBottom: 8 }}>
                {`Следующий reset FREE: ${fmtDate(dash.free_next_reset_at)}`}
              </div>
            ) : null}

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
            <div className="card__title" style={{ marginTop: 14 }}>Подарочный код</div>
            <div className="actions">
              <input
                className="field field--compact"
                aria-label="Gift code"
                placeholder="PORTAL-XXXX-XXXX"
                value={giftCode}
                onChange={(e) => setGiftCode(e.target.value)}
              />
              <button className="btn btn--ghost" type="button" onClick={() => void onRedeemGift()}>
                <span style={{ position: "relative", zIndex: 1 }}>Активировать</span>
              </button>
            </div>
            {giftRedeemResult ? <div className="muted" style={{ marginTop: 8 }}>{giftRedeemResult}</div> : null}
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
                <a
                  key={c.title}
                  className="row row--btn"
                  href={c.url}
                  target="_blank"
                  rel="noreferrer"
                  onClick={() => void trackEvent("open_client_store", "webapp", { platform, title: c.title })}
                >
                  <div>
                    <div className="row__title">{c.title}</div>
                    <div className="row__sub">Рекомендуемый клиент</div>
                  </div>
                  <span style={{ color: "var(--red)", fontFamily: "var(--mono)", fontSize: 12 }}>→</span>
                </a>
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
              <button className="btn btn--ghost" type="button" onClick={() => openLink(docsLinkForConnect())}>
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
            <textarea className="field field--area" aria-label="Ticket description" value={ticketBody} onChange={(e) => setTicketBody(e.target.value)} placeholder="Опишите проблему..." />
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
                <textarea className="field field--area" aria-label="Ticket reply" value={replyBody} onChange={(e) => setReplyBody(e.target.value)} placeholder="Ответ..." />
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

