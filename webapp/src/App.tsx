import React, { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import gsap from "gsap";
import Lottie from "lottie-react";
import {
  addTicketMessage,
  adminManualBlock,
  adminManualCreate,
  adminManualExtend,
  adminManualRegenerateToken,
  adminNodesHealth,
  adminNodesSync,
  adminSummary,
  adminTicketReply,
  adminTicketStatus,
  adminTickets,
  adminUserCard,
  adminUserMessage,
  adminUsers,
  createTicket,
  fetchDashboard,
  fetchNodeStatus,
  fetchTickets,
  fetchUser,
  getTicket,
  runNodeDiagnostics,
  type AdminNodeHealthRow,
  type AdminSummaryPayload,
  type AdminUserCard,
  type AdminUserRow,
  type DashboardSnapshot,
  type NodeStatus,
  type TicketInfo,
  type UserPayload,
} from "./api";
import { OFFER_FULL, OFFER_UPDATED_AT } from "./legal";
import { getTgUser, haptic, openLink, tgReady } from "./telegram";

type Mode = "user" | "admin";
type UserTab = "dashboard" | "nodes" | "support" | "account" | "legal";
type AdminTab = "summary" | "users" | "tickets" | "nodes";

const USER_TAB_LABEL: Record<UserTab, string> = {
  dashboard: "Dashboard",
  nodes: "Nodes",
  support: "Support",
  account: "Account",
  legal: "Offer",
};

const ADMIN_TAB_LABEL: Record<AdminTab, string> = {
  summary: "Summary",
  users: "Users",
  tickets: "Tickets",
  nodes: "Nodes",
};

const FLOATING_ICONS = ["🔐", "🛡️", "⚡", "🌐", "🔒"];
const PRELOADER_TEXT = "CONNECTING TO PORTAL...";

const scannerAnim = {
  v: "5.6.5",
  fr: 30,
  ip: 0,
  op: 120,
  w: 240,
  h: 240,
  nm: "scanner",
  ddd: 0,
  assets: [],
  layers: [
    {
      ddd: 0,
      ind: 1,
      ty: 4,
      nm: "ring",
      sr: 1,
      ks: {
        o: { a: 0, k: 100 },
        r: { a: 1, k: [{ t: 0, s: [0] }, { t: 120, s: [360] }] },
        p: { a: 0, k: [120, 120, 0] },
        a: { a: 0, k: [0, 0, 0] },
        s: { a: 0, k: [100, 100, 100] },
      },
      ao: 0,
      shapes: [
        {
          ty: "gr",
          it: [
            { ty: "el", p: { a: 0, k: [0, 0] }, s: { a: 0, k: [140, 140] }, d: 1, nm: "ellipse" },
            { ty: "st", c: { a: 0, k: [0.27, 0.66, 1, 1] }, o: { a: 0, k: 100 }, w: { a: 0, k: 8 }, lc: 2, lj: 2, nm: "stroke" },
            { ty: "tr", p: { a: 0, k: [0, 0] }, a: { a: 0, k: [0, 0] }, s: { a: 0, k: [100, 100] }, r: { a: 0, k: 0 }, o: { a: 0, k: 100 }, sk: { a: 0, k: 0 }, sa: { a: 0, k: 0 }, nm: "transform" },
          ],
          nm: "group",
        },
      ],
      ip: 0,
      op: 120,
      st: 0,
      bm: 0,
    },
  ],
};

function fmtDate(iso?: string | null): string {
  if (!iso) return "-";
  return new Date(iso).toLocaleString("ru-RU");
}

async function copyText(text: string): Promise<boolean> {
  const t = (text || "").trim();
  if (!t) return false;
  try {
    await navigator.clipboard.writeText(t);
    return true;
  } catch {
    return false;
  }
}

function tabCls(active: boolean): string {
  return active ? "chip chip--active" : "chip";
}

export default function App() {
  const tgUser = useMemo(() => getTgUser(), []);
  const [mode, setMode] = useState<Mode>("user");
  const [uTab, setUTab] = useState<UserTab>("dashboard");
  const [aTab, setATab] = useState<AdminTab>("summary");

  const [user, setUser] = useState<UserPayload | null>(null);
  const [dash, setDash] = useState<DashboardSnapshot | null>(null);
  const [nodes, setNodes] = useState<NodeStatus[]>([]);
  const [diagText, setDiagText] = useState("");
  const [diagLoading, setDiagLoading] = useState(false);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");
  const [loading, setLoading] = useState(true);

  const [tickets, setTickets] = useState<TicketInfo[]>([]);
  const [ticket, setTicket] = useState<TicketInfo | null>(null);
  const [ticketSubject, setTicketSubject] = useState("");
  const [ticketBody, setTicketBody] = useState("");
  const [ticketReply, setTicketReply] = useState("");

  const [admSummary, setAdmSummary] = useState<AdminSummaryPayload | null>(null);
  const [admUsers, setAdmUsers] = useState<AdminUserRow[]>([]);
  const [admUserCard, setAdmUserCard] = useState<AdminUserCard | null>(null);
  const [admUserQuery, setAdmUserQuery] = useState("");
  const [admUserMsg, setAdmUserMsg] = useState("");
  const [admUserToken, setAdmUserToken] = useState("");
  const [manualName, setManualName] = useState("");
  const [manualDays, setManualDays] = useState(30);
  const [admTickets, setAdmTickets] = useState<TicketInfo[]>([]);
  const [admTicket, setAdmTicket] = useState<TicketInfo | null>(null);
  const [admTicketReplyText, setAdmTicketReplyText] = useState("");
  const [admNodes, setAdmNodes] = useState<AdminNodeHealthRow[]>([]);

  // UI state
  const [showPreloader, setShowPreloader] = useState(true);

  // Refs
  const appRef = useRef<HTMLDivElement>(null);
  const cursorRef = useRef<HTMLDivElement>(null);
  const cursorDotRef = useRef<HTMLDivElement>(null);
  const floatingRef = useRef<HTMLDivElement>(null);
  const preloaderRef = useRef<HTMLDivElement>(null);

  // Cursor tracking
  useEffect(() => {
    const cursor = cursorRef.current;
    const dot = cursorDotRef.current;
    if (!cursor || !dot) return;

    let cx = 0, cy = 0, dx = 0, dy = 0;
    let animId: number;

    const onMove = (e: MouseEvent) => {
      cx = e.clientX;
      cy = e.clientY;
    };

    const animate = () => {
      dx += (cx - dx) * 0.15;
      dy += (cy - dy) * 0.15;
      cursor.style.left = `${dx}px`;
      cursor.style.top = `${dy}px`;
      dot.style.left = `${cx}px`;
      dot.style.top = `${cy}px`;
      animId = requestAnimationFrame(animate);
    };

    document.addEventListener("mousemove", onMove);
    animId = requestAnimationFrame(animate);

    // Hover effect
    const addHover = () => cursor.classList.add("hover");
    const removeHover = () => cursor.classList.remove("hover");
    const interactiveEls = document.querySelectorAll(".btn, .chip, .row, .nav__btn, .metric");
    interactiveEls.forEach((el) => {
      el.addEventListener("mouseenter", addHover);
      el.addEventListener("mouseleave", removeHover);
    });

    return () => {
      document.removeEventListener("mousemove", onMove);
      cancelAnimationFrame(animId);
      interactiveEls.forEach((el) => {
        el.removeEventListener("mouseenter", addHover);
        el.removeEventListener("mouseleave", removeHover);
      });
    };
  }, [loading, showPreloader]);

  // Preloader animation
  useEffect(() => {
    if (!loading && preloaderRef.current) {
      const textEl = preloaderRef.current.querySelector(".preloader-text");
      const fillEl = preloaderRef.current.querySelector(".preloader-fill");
      const iconEl = preloaderRef.current.querySelector(".preloader-icon");

      if (textEl && fillEl && iconEl) {
        // Create text spans
        textEl.innerHTML = PRELOADER_TEXT.split("")
          .map((ch) => `<span>${ch === " " ? "\u00A0" : ch}</span>`)
          .join("");

        const tl = gsap.timeline({
          onComplete: () => {
            gsap.to(preloaderRef.current, {
              yPercent: -100,
              duration: 0.6,
              ease: "power4.inOut",
              onComplete: () => setShowPreloader(false),
            });
          },
        });

        tl.to(iconEl, { opacity: 1, scale: 1, rotation: 360, duration: 0.5, ease: "back.out(1.7)" })
          .to(textEl.querySelectorAll("span"), { opacity: 1, stagger: 0.02, duration: 0.15 }, 0.2)
          .to(fillEl, { width: "100%", duration: 1, ease: "power2.inOut" }, 0.3)
          .to(iconEl, { rotation: 720, duration: 0.3 }, 1.2);
      }
    }
  }, [loading]);

  // Floating icons
  useEffect(() => {
    if (!floatingRef.current || showPreloader) return;

    const container = floatingRef.current;
    container.innerHTML = "";

    FLOATING_ICONS.forEach((icon, i) => {
      const span = document.createElement("span");
      span.textContent = icon;
      span.style.left = `${Math.random() * 100}%`;
      span.style.top = `${Math.random() * 100}%`;
      container.appendChild(span);

      gsap.to(span, { opacity: 0.06, duration: 0 });
      gsap.to(span, {
        y: gsap.utils.random(-30, 30),
        x: gsap.utils.random(-20, 20),
        rotation: gsap.utils.random(-10, 10),
        duration: gsap.utils.random(6, 12),
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut",
        delay: i * 0.5,
      });
    });
  }, [showPreloader]);

  // Main app GSAP animations
  useLayoutEffect(() => {
    if (loading || showPreloader || !appRef.current) return;

    const ctx = gsap.context(() => {
      // Header animation
      gsap.from(".brand__mark", { scale: 0, duration: 0.5, ease: "back.out(1.7)" });
      gsap.from(".brand__title", { y: 15, opacity: 0, duration: 0.4, delay: 0.1 });
      gsap.from(".brand__sub", { y: 8, opacity: 0, duration: 0.4, delay: 0.2 });
      gsap.from(".status", { scale: 0.8, opacity: 0, duration: 0.4, delay: 0.3 });

      // Cards stagger
      gsap.from(".card", { y: 20, opacity: 0, duration: 0.5, stagger: 0.1, ease: "power3.out", delay: 0.2 });

      // Nav buttons
      gsap.from(".nav__btn", { y: 30, opacity: 0, duration: 0.4, stagger: 0.08, ease: "back.out(1.5)", delay: 0.5 });

      // Rows
      gsap.from(".row", { x: -15, opacity: 0, duration: 0.4, stagger: 0.06, ease: "power3.out", delay: 0.6 });
    }, appRef);

    return () => ctx.revert();
  }, [loading, showPreloader, user]);

  // Tab change animation
  useEffect(() => {
    if (!appRef.current || loading || showPreloader) return;
    gsap.from(".card:not(:first-child)", { y: 15, opacity: 0, duration: 0.35, stagger: 0.08, ease: "power2.out" });
  }, [uTab, aTab, mode]);

  useEffect(() => {
    tgReady();
  }, []);


  useEffect(() => {
    if (!toast) return;
    const id = window.setTimeout(() => setToast(""), 2200);
    return () => window.clearTimeout(id);
  }, [toast]);

  async function loadUser(): Promise<UserPayload | null> {
    if (!tgUser) {
      setError("Откройте WebApp из Telegram-бота.");
      return null;
    }
    const u = await fetchUser(tgUser.id);
    const [d, n, t] = await Promise.all([fetchDashboard(), fetchNodeStatus(), fetchTickets(25)]);
    setUser(u);
    setDash(d);
    setNodes(n);
    setTickets(t);
    return u;
  }

  async function loadAdmin() {
    const [s, t, n] = await Promise.all([adminSummary(), adminTickets("", 40), adminNodesHealth()]);
    setAdmSummary(s);
    setAdmTickets(t);
    setAdmNodes(n);
  }

  async function reloadAll() {
    try {
      setError("");
      setLoading(true);
      const u = await loadUser();
      if (u?.is_admin) await loadAdmin();
    } catch (e: unknown) {
      setError(String((e as { message?: string })?.message || e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void reloadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function notifySuccess(msg: string) {
    setToast(msg);
    if (user?.features?.haptic ?? true) haptic("success");
  }

  function notifyError(msg: string) {
    setToast(msg);
    if (user?.features?.haptic ?? true) haptic("error");
  }

  if (loading) {
    return (
      <div className="app">
        <section className="card glass-card card-enter">
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
        <section className="card card--danger glass-card">
          <div className="card__title">Ошибка</div>
          <div className="muted">{error || "Нет данных"}</div>
        </section>
      </div>
    );
  }

  return (
    <>
      {/* Custom Cursor */}
      <div className="cursor" ref={cursorRef} />
      <div className="cursor-dot" ref={cursorDotRef} />

      {/* Floating Icons */}
      <div className="floating" ref={floatingRef} />

      {/* Preloader */}
      {showPreloader && (
        <div className="preloader" ref={preloaderRef}>
          <div className="preloader-icon">🔐</div>
          <div className="preloader-text" />
          <div className="preloader-bar">
            <div className="preloader-fill" />
          </div>
        </div>
      )}

      <div className="app" ref={appRef}>
        <header className="top">
          <div className="brand">
            <div className="brand__mark">P</div>
            <div>
              <div className="brand__title">PORTAL | Network Security</div>
              <div className="brand__sub">{user.username ? `@${user.username}` : `ID ${user.tg_id}`}</div>
            </div>
          </div>
          <div className={dash.is_active ? "status status--ok" : "status status--bad"}>{dash.is_active ? "Active" : "Expired"}</div>
        </header>

        {toast ? (
          <section className="card card--notice glass-card card-enter">
            <div className="muted">{toast}</div>
          </section>
        ) : null}

        {user.is_admin ? (
          <section className="card glass-card">
            <div className="chips">
              <button className={tabCls(mode === "user")} type="button" onClick={() => setMode("user")}>
                User
              </button>
              <button className={tabCls(mode === "admin")} type="button" onClick={() => setMode("admin")}>
                Admin
              </button>
            </div>
          </section>
        ) : null}

        {mode === "user" ? (
          <>
            <section className="card glass-card">
              <div className="chips">
                {(Object.keys(USER_TAB_LABEL) as UserTab[]).map((k) => (
                  <button key={k} className={tabCls(uTab === k)} type="button" onClick={() => setUTab(k)}>
                    {USER_TAB_LABEL[k]}
                  </button>
                ))}
              </div>
            </section>

            {uTab === "dashboard" ? (
              <section className={`card glass-card pulse-ring ${dash.is_active ? "pulse-ring--ok" : "pulse-ring--bad"}`}>
                <div className="card__title">Подписка</div>
                <div className="grid2">
                  <div className="metric">
                    <div className="metric__k">Тариф</div>
                    <div className="metric__v">{dash.sub_type}</div>
                  </div>
                  <div className="metric">
                    <div className="metric__k">Истекает</div>
                    <div className="metric__v">{fmtDate(dash.expiry_at)}</div>
                  </div>
                  <div className="metric">
                    <div className="metric__k">Трафик</div>
                    <div className="metric__v">
                      {dash.total_gb > 0 ? `${dash.used_gb} / ${dash.total_gb} GB` : "Unlimited"}
                    </div>
                  </div>
                  <div className="metric">
                    <div className="metric__k">Сессии</div>
                    <div className="metric__v">
                      {dash.active_sessions || 0} / {dash.device_limit}
                    </div>
                  </div>
                </div>
                <div className="monoWrap">
                  <div className="monoLabel">Ключ подписки</div>
                  <div className="mono">{dash.subscription_url || "-"}</div>
                </div>
                <div className="actions">
                  <button
                    className="btn"
                    type="button"
                    onClick={async () => {
                      const ok = await copyText(dash.subscription_url || "");
                      if (ok) notifySuccess("Ключ скопирован");
                      else notifyError("Не удалось скопировать");
                    }}
                  >
                    Копировать ключ
                  </button>
                  <button className="btn btn--ghost" type="button" onClick={() => openLink(user.actions.pay_via_bot)}>
                    Подключить / Продлить
                  </button>
                </div>
              </section>
            ) : null}

            {uTab === "nodes" ? (
              <section className="card glass-card slide-in">
                <div className="card__title">Узлы сети</div>
                <div className="list">
                  {nodes.map((n) => (
                    <div className="row glass-tile" key={n.code}>
                      <div>
                        <div className="row__title">{`${n.country} • ${n.code.toUpperCase()}`}</div>
                        <div className="row__sub">{`${n.host} • ping ${n.ping_ms ?? "n/a"}ms`}</div>
                      </div>
                      <div className={n.is_healthy ? "pill pill--ok" : "pill pill--bad"}>{n.is_healthy ? "Online" : "Degraded"}</div>
                    </div>
                  ))}
                </div>
                <div className="actions">
                  <button
                    className="btn"
                    type="button"
                    disabled={diagLoading}
                    onClick={async () => {
                      setDiagLoading(true);
                      setDiagText("");
                      try {
                        const res = await runNodeDiagnostics();
                        setDiagText(`${res.summary} • DNS=${res.dns_status} • SNI=${res.sni_status}`);
                        notifySuccess("Диагностика завершена");
                      } catch (e: unknown) {
                        setDiagText(String((e as { message?: string })?.message || e));
                        notifyError("Диагностика не удалась");
                      } finally {
                        setDiagLoading(false);
                      }
                    }}
                  >
                    Проверить доступность
                  </button>
                  <button
                    className="btn btn--ghost"
                    type="button"
                    onClick={async () => {
                      setNodes(await fetchNodeStatus());
                      notifySuccess("Статусы узлов обновлены");
                    }}
                  >
                    Обновить
                  </button>
                </div>
                {diagLoading && (dash.features?.lottie ?? true) ? <Lottie animationData={scannerAnim} loop className="lottie" /> : null}
                <div className="muted">{diagText}</div>
              </section>
            ) : null}

            {uTab === "support" ? (
              <section className="card glass-card slide-in">
                <div className="card__title">Поддержка и тикеты</div>
                <div className="actions">
                  <button className="btn btn--ghost" type="button" onClick={() => openLink(user.support.new_ticket_link)}>
                    Открыть helpbot
                  </button>
                  <button
                    className="btn btn--ghost"
                    type="button"
                    onClick={async () => {
                      setTickets(await fetchTickets(25));
                      notifySuccess("Тикеты обновлены");
                    }}
                  >
                    Обновить
                  </button>
                </div>
                <input className="field" value={ticketSubject} onChange={(e) => setTicketSubject(e.target.value)} placeholder="Тема (опционально)" />
                <textarea className="field field--area" value={ticketBody} onChange={(e) => setTicketBody(e.target.value)} placeholder="Опишите проблему" />
                <div className="actions">
                  <button
                    className="btn"
                    type="button"
                    onClick={async () => {
                      if (!ticketBody.trim()) return;
                      const t = await createTicket(ticketSubject.trim(), ticketBody.trim());
                      setTicket(t);
                      setTickets(await fetchTickets(25));
                      setTicketBody("");
                      setTicketSubject("");
                      notifySuccess(`Тикет #${t.id} создан`);
                    }}
                  >
                    Новый запрос
                  </button>
                </div>
                <div className="list">
                  {tickets.map((t) => (
                    <button key={t.id} className="row row--btn glass-tile" type="button" onClick={async () => setTicket(await getTicket(t.id))}>
                      <div>
                        <div className="row__title">{`#${t.id} ${t.status_title}`}</div>
                        <div className="row__sub">{t.last_message_preview || "-"}</div>
                      </div>
                      <div className={t.status === "closed" ? "pill" : "pill pill--ok"}>{t.status === "closed" ? "Closed" : "Open"}</div>
                    </button>
                  ))}
                </div>
                {ticket ? (
                  <>
                    <div className="divider" />
                    <div className="row">
                      <div>
                        <div className="row__title">{`Тикет #${ticket.id}`}</div>
                        <div className="row__sub">{fmtDate(ticket.updated_at)}</div>
                      </div>
                      <div className={ticket.status === "closed" ? "pill" : "pill pill--ok"}>{ticket.status === "closed" ? "Closed" : "Open"}</div>
                    </div>
                    <div className="list">
                      {ticket.messages.map((m) => (
                        <div key={m.id} className={m.sender_role === "admin" ? "msg msg--op" : "msg msg--mine"}>
                          <div className="row__title">{m.sender_role === "admin" ? "Оператор" : "Вы"}</div>
                          <div className="muted">{m.body}</div>
                          <div className="row__sub">{fmtDate(m.created_at)}</div>
                        </div>
                      ))}
                    </div>
                    <textarea className="field field--area" value={ticketReply} onChange={(e) => setTicketReply(e.target.value)} placeholder="Ответ в тикет" />
                    <div className="actions">
                      <button
                        className="btn"
                        type="button"
                        onClick={async () => {
                          if (!ticketReply.trim()) return;
                          const updated = await addTicketMessage(ticket.id, ticketReply.trim());
                          setTicket(updated);
                          setTicketReply("");
                          setTickets(await fetchTickets(25));
                          notifySuccess("Ответ отправлен");
                        }}
                      >
                        Отправить ответ
                      </button>
                    </div>
                  </>
                ) : null}
              </section>
            ) : null}

            {uTab === "account" ? (
              <section className="card glass-card slide-in">
                <div className="card__title">Аккаунт</div>
                <div className="list">
                  <div className="row">
                    <div className="row__title">Telegram ID</div>
                    <div className="mono">{user.tg_id}</div>
                  </div>
                  <div className="row">
                    <div className="row__title">Username</div>
                    <div className="mono">{user.username ? `@${user.username}` : "-"}</div>
                  </div>
                  <div className="row">
                    <div className="row__title">План</div>
                    <div className="mono">{`${dash.sub_type} • ${fmtDate(dash.expiry_at)}`}</div>
                  </div>
                </div>
              </section>
            ) : null}

            {uTab === "legal" ? (
              <section className="card glass-card slide-in">
                <div className="card__title">Оферта</div>
                <div className="muted">{`Обновлено: ${OFFER_UPDATED_AT}`}</div>
                <pre className="mono legal">{OFFER_FULL}</pre>
              </section>
            ) : null}
          </>
        ) : (
          <>
            <section className="card glass-card">
              <div className="chips">
                {(Object.keys(ADMIN_TAB_LABEL) as AdminTab[]).map((k) => (
                  <button key={k} className={tabCls(aTab === k)} type="button" onClick={() => setATab(k)}>
                    {ADMIN_TAB_LABEL[k]}
                  </button>
                ))}
              </div>
            </section>

            {aTab === "summary" && admSummary ? (
              <section className="card glass-card slide-in">
                <div className="card__title">Admin Summary</div>
                <div className="grid2">
                  <div className="metric"><div className="metric__k">Users</div><div className="metric__v">{admSummary.users.total}</div></div>
                  <div className="metric"><div className="metric__k">Active</div><div className="metric__v">{admSummary.users.active}</div></div>
                  <div className="metric"><div className="metric__k">Tickets</div><div className="metric__v">{admSummary.tickets.open}</div></div>
                  <div className="metric"><div className="metric__k">Healthy Nodes</div><div className="metric__v">{`${admSummary.nodes.healthy}/${admSummary.nodes.total}`}</div></div>
                </div>
                <div className="actions">
                  <button className="btn btn--ghost" type="button" onClick={async () => setAdmSummary(await adminSummary())}>
                    Refresh
                  </button>
                </div>
              </section>
            ) : null}

            {aTab === "users" ? (
              <section className="card glass-card slide-in">
                <div className="card__title">Users / Manual</div>
                <input className="field" value={admUserQuery} onChange={(e) => setAdmUserQuery(e.target.value)} placeholder="Поиск username или tg_id" />
                <div className="actions">
                  <button className="btn" type="button" onClick={async () => setAdmUsers(await adminUsers(admUserQuery.trim(), 100, 0))}>
                    Поиск
                  </button>
                </div>
                <div className="divider" />
                <div className="row__title">Создать manual user</div>
                <input className="field" value={manualName} onChange={(e) => setManualName(e.target.value)} placeholder="Display name" />
                <input
                  className="field"
                  type="number"
                  min={1}
                  max={3650}
                  value={String(manualDays)}
                  onChange={(e) => setManualDays(Number(e.target.value) || 30)}
                />
                <div className="actions">
                  <button
                    className="btn"
                    type="button"
                    onClick={async () => {
                      if (!manualName.trim()) return;
                      const res = await adminManualCreate({ display_name: manualName.trim(), days: manualDays });
                      notifySuccess(`Manual user создан: ${res.user.tg_id}`);
                      setManualName("");
                      setAdmUsers(await adminUsers("", 120, 0));
                    }}
                  >
                    Создать
                  </button>
                </div>
                <div className="list">
                  {admUsers.map((u) => (
                    <button key={u.tg_id} className="row row--btn glass-tile" type="button" onClick={async () => setAdmUserCard(await adminUserCard(u.tg_id))}>
                      <div>
                        <div className="row__title">{u.display_name || (u.username ? `@${u.username}` : String(u.tg_id))}</div>
                        <div className="row__sub">{`${u.sub_type} • ${u.is_manual ? "manual" : "telegram"} • exp ${fmtDate(u.expiry_at)}`}</div>
                      </div>
                    </button>
                  ))}
                </div>
                {admUserCard ? (
                  <>
                    <div className="divider" />
                    <div className="row__title">{`Карточка ${admUserCard.user.display_name || admUserCard.user.username || admUserCard.user.tg_id}`}</div>
                    <textarea className="field field--area" value={admUserMsg} onChange={(e) => setAdmUserMsg(e.target.value)} placeholder="Сообщение пользователю" />
                    <div className="actions">
                      <button
                        className="btn"
                        type="button"
                        onClick={async () => {
                          if (!admUserMsg.trim()) return;
                          await adminUserMessage(admUserCard.user.tg_id, admUserMsg.trim());
                          setAdmUserMsg("");
                          notifySuccess("Сообщение отправлено");
                        }}
                      >
                        Send DM
                      </button>
                      <button className="btn btn--ghost" type="button" onClick={async () => adminNodesSync({ tg_id: admUserCard.user.tg_id })}>
                        Sync Nodes
                      </button>
                    </div>
                    {admUserCard.user.is_manual ? (
                      <>
                        <div className="actions">
                          <button
                            className="btn btn--ghost"
                            type="button"
                            onClick={async () => {
                              const res = await adminManualExtend(admUserCard.user.tg_id, 30);
                              notifySuccess(`Продлено до ${fmtDate(res.expiry_at)}`);
                              setAdmUserCard(await adminUserCard(admUserCard.user.tg_id));
                            }}
                          >
                            +30 дней
                          </button>
                          <button
                            className="btn btn--ghost"
                            type="button"
                            onClick={async () => {
                              await adminManualBlock(admUserCard.user.tg_id, admUserCard.user.is_active);
                              setAdmUserCard(await adminUserCard(admUserCard.user.tg_id));
                              notifySuccess("Статус обновлен");
                            }}
                          >
                            {admUserCard.user.is_active ? "Block" : "Unblock"}
                          </button>
                          <button
                            className="btn btn--ghost"
                            type="button"
                            onClick={async () => {
                              const res = await adminManualRegenerateToken(admUserCard.user.tg_id);
                              setAdmUserToken(res.subscription_url);
                              notifySuccess("Токен перевыпущен");
                            }}
                          >
                            Regen token
                          </button>
                        </div>
                        {admUserToken ? <pre className="mono">{admUserToken}</pre> : null}
                      </>
                    ) : null}
                  </>
                ) : null}
              </section>
            ) : null}

            {aTab === "tickets" ? (
              <section className="card glass-card slide-in">
                <div className="card__title">Tickets Queue</div>
                <div className="list">
                  {admTickets.map((t) => (
                    <button key={t.id} className="row row--btn glass-tile" type="button" onClick={async () => setAdmTicket(await getTicket(t.id))}>
                      <div>
                        <div className="row__title">{`#${t.id} • u:${t.user_tg_id}`}</div>
                        <div className="row__sub">{t.last_message_preview || "-"}</div>
                      </div>
                      <div className={t.status === "closed" ? "pill" : "pill pill--ok"}>{t.status_title}</div>
                    </button>
                  ))}
                </div>
                {admTicket ? (
                  <>
                    <div className="divider" />
                    <div className="row__title">{`Ticket #${admTicket.id}`}</div>
                    <textarea className="field field--area" value={admTicketReplyText} onChange={(e) => setAdmTicketReplyText(e.target.value)} placeholder="Ответ оператора" />
                    <div className="actions">
                      <button
                        className="btn"
                        type="button"
                        onClick={async () => {
                          if (!admTicketReplyText.trim()) return;
                          const updated = await adminTicketReply(admTicket.id, admTicketReplyText.trim());
                          setAdmTicket(updated);
                          setAdmTicketReplyText("");
                          setAdmTickets(await adminTickets("", 40));
                        }}
                      >
                        Reply
                      </button>
                      <button className="btn btn--ghost" type="button" onClick={async () => setAdmTicket(await adminTicketStatus(admTicket.id, "closed"))}>
                        Close
                      </button>
                    </div>
                  </>
                ) : null}
              </section>
            ) : null}

            {aTab === "nodes" ? (
              <section className="card glass-card slide-in">
                <div className="card__title">Nodes Health</div>
                <div className="actions">
                  <button className="btn btn--ghost" type="button" onClick={async () => setAdmNodes(await adminNodesHealth())}>
                    Refresh
                  </button>
                  <button className="btn btn--ghost" type="button" onClick={async () => adminNodesSync({ segment: "active", limit: 150 })}>
                    Sync Active
                  </button>
                </div>
                <div className="list">
                  {admNodes.map((n) => (
                    <div key={n.code} className="row glass-tile">
                      <div>
                        <div className="row__title">{`${n.code} • score ${n.health_score.toFixed(2)}`}</div>
                        <div className="row__sub">{`ping ${n.panel_latency_ms ?? "n/a"}ms • err ${(n.panel_error_rate * 100).toFixed(1)}% • load ${n.active_clients}`}</div>
                      </div>
                      <div className={n.is_healthy ? "pill pill--ok" : "pill pill--bad"}>{n.is_healthy ? "Healthy" : "Degraded"}</div>
                    </div>
                  ))}
                </div>
              </section>
            ) : null}
          </>
        )}
      </div>
    </>
  );
}
