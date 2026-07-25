"use client";

import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { useEffect, useState } from "react";
import {
  Download,
  BookOpenText,
  FileText,
  Hourglass,
  KeyRound,
  LifeBuoy,
  MessageCircle,
  MessageSquarePlus,
  MessagesSquare,
  MonitorSmartphone,
  Send,
  ShieldCheck,
  Wifi,
  X,
} from "lucide-react";

import AppRouteLink from "@/components/app-route-link";
import { FaqAccordion } from "@/components/cabinet/instructions";
import { StatusHero } from "@/components/cabinet/status-hero";
import { Button } from "@/components/ui/button";
import { Chip } from "@/components/ui/chip";
import { GroupedSection, Row } from "@/components/ui/grouped";
import { Input, Textarea } from "@/components/ui/input";
import { Note } from "@/components/ui/note";
import { Tile, TileGrid } from "@/components/ui/tiles";
import { useToast } from "@/components/ui/toast";
import {
  createTicket,
  fetchTickets,
  uploadTicketAttachment,
  type TicketAttachmentInput,
  type TicketInfo,
} from "@/lib/api";
import { getDeviceLimit, resolvePlanLabel } from "@/lib/access-policy";
import { getCopyText, getPortalPublicConfig } from "@/lib/portal";
import { userFacingErrorMessage } from "@/lib/public-error-messages";
import { usePortalSession } from "@/lib/session";
import { SUPPORT_ATTACHMENT_ACCEPT, validateSupportAttachment } from "@/lib/support-attachments";

type TicketCategory = "Не могу подключиться" | "Вопрос по оплате" | "Медленно работает" | "Другое";

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);
const CATEGORIES: TicketCategory[] = ["Не могу подключиться", "Вопрос по оплате", "Медленно работает", "Другое"];

const CATEGORY_PRESETS: Record<TicketCategory, { subject: string; body: string; hint: string }> = {
  "Не могу подключиться": {
    subject: "Не получается подключить устройство",
    body: "Что происходит:\n\nУстройство:\n\nЧто уже пробовали:",
    hint: "Устройство, шаг подключения и текст ошибки, если он есть.",
  },
  "Вопрос по оплате": {
    subject: "Вопрос по оплате или продлению",
    body: "Что ожидали увидеть:\n\nЧто произошло вместо этого:\n\nПримерное время оплаты:",
    hint: "Срок, способ оплаты и примерное время операции.",
  },
  "Медленно работает": {
    subject: "Нестабильная скорость или подключение",
    body: "Как выглядит проблема:\n\nУстройство:\n\nWi-Fi или мобильная сеть:",
    hint: "Где заметно замедление и когда оно началось.",
  },
  Другое: {
    subject: "Вопрос по кабинету POKROV",
    body: "Коротко опишите вопрос:\n\nКакой результат нужен:",
    hint: "Любой вопрос по кабинету, доступу или устройствам.",
  },
};

function statusLabel(status: string): string {
  const normalized = String(status || "").trim().toLowerCase();
  if (normalized === "open") return "Открыт";
  if (normalized === "in_progress") return "В работе";
  if (normalized === "closed") return "Закрыт";
  return normalized || "Неизвестно";
}

const FAQ_ENTRIES = [
  {
    question: "Как подключить устройство?",
    answer:
      "1. Скачайте приложение на странице «Загрузки»\n2. Войдите тем же способом, что и в кабинет, — почта или Telegram\n3. Нажмите «Подключить»\n\nЕсли приложение для вашего устройства недоступно, используйте раздел «Ручное подключение» в кабинете: скопируйте личную ссылку и добавьте её в Hiddify. Для Happ нужен вариант ссылки с ?format=happ.",
  },
  {
    question: "Оплатил, но доступ не обновился",
    answer:
      "Обычно доступ включается сам за пару минут. Если прошло больше 15 минут — проверьте срок на главной кабинета и создайте обращение, приложив чек или скрин оплаты. По чеку мы найдём платёж и включим доступ вручную, деньги не теряются.",
  },
  {
    question: "Не работает подключение",
    answer:
      "Попробуйте по порядку:\n1. Обновите доступ в приложении\n2. Полностью перезапустите приложение\n3. Проверьте обычный интернет без POKROV\n4. Смените локацию, если есть выбор\n5. Перезагрузите устройство\n\nНе помогло — создайте обращение и опишите, на каком шаге останавливается.",
  },
  {
    question: "Медленная скорость",
    answer:
      "Сначала проверьте скорость обычного интернета без POKROV — если он медленный, дело в сети. Затем смените локацию и перезапустите приложение. На бесплатном старте после лимита трафика скорость снижается, в платных режимах в обычном режиме снижения нет.",
  },
  {
    question: "Как перенести доступ на новое устройство?",
    answer:
      "Скачайте приложение на новое устройство и войдите в тот же аккаунт — доступ подтянется сам. Список связанных устройств виден на странице «Устройства».",
  },
  {
    question: "Промокод или код не сработал",
    answer:
      "Проверьте, нет ли опечатки — коды не зависят от регистра. У кода мог закончиться срок или лимит активаций, а часть кодов действует только для новых аккаунтов. Активировать код можно на странице «Активировать код». Если не получилось — напишите нам, разберёмся с конкретным кодом.",
  },
  {
    question: "Что такое ручное подключение и личная ссылка?",
    answer:
      "Это запасной способ для устройств, где приложение POKROV недоступно. В кабинете есть раздел «Ручное подключение» — скопируйте оттуда личную ссылку и добавьте её в Hiddify или другой совместимый клиент. Для Happ используйте вариант ссылки с ?format=happ. Ссылка — как ключ от квартиры: не делитесь ей. Если она попала не в те руки, сбросьте её в кабинете.",
  },
];

function formatDate(value?: string | null): string {
  if (!value) return "недавно";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "недавно";
  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(parsed);
}

function formatFileSize(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes <= 0) return "0 Б";
  if (bytes < 1024) return `${bytes} Б`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} КБ`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} МБ`;
}

export default function SupportPage() {
  const { user, dash } = usePortalSession();
  const { showToast } = useToast();
  const reduceMotion = useReducedMotion();
  const [tickets, setTickets] = useState<TicketInfo[]>([]);
  const [loadingTickets, setLoadingTickets] = useState(true);
  const [composeOpen, setComposeOpen] = useState(false);
  const [category, setCategory] = useState<TicketCategory>(CATEGORIES[0]);
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [attachmentFile, setAttachmentFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const supportLink = user?.support?.link || config.supportTelegramUrl;
  const latestTicket = tickets[0] || null;
  const openCount = tickets.filter((ticket) => String(ticket.status || "").toLowerCase() !== "closed").length;
  const activeConnections = dash?.connection_snapshot?.active_connections ?? dash?.active_sessions ?? 0;
  const deviceCount = user?.sync?.device_count ?? user?.devices?.length ?? 0;
  const deviceLimit = getDeviceLimit(dash, user);
  const preset = CATEGORY_PRESETS[category];

  const loadTickets = async (): Promise<void> => {
    setLoadingTickets(true);
    try {
      const rows = await fetchTickets(20);
      setTickets(rows);
      setError("");
    } catch (nextError) {
      setError(userFacingErrorMessage(nextError, "Не получилось обновить обращения. Попробуйте ещё раз."));
    } finally {
      setLoadingTickets(false);
    }
  };

  useEffect(() => {
    void loadTickets();
  }, []);

  useEffect(() => {
    if (!composeOpen) return;
    document.body.classList.add("modal-open");
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setComposeOpen(false);
    };
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.body.classList.remove("modal-open");
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [composeOpen]);

  const openComposer = (nextCategory: TicketCategory = category): void => {
    const nextPreset = CATEGORY_PRESETS[nextCategory];
    setCategory(nextCategory);
    setSubject((current) => current || nextPreset.subject);
    setBody((current) => current || nextPreset.body);
    setNotice("");
    setComposeOpen(true);
  };

  const onCreateTicket = async (): Promise<void> => {
    const normalizedBody = body.trim();
    const normalizedSubject = subject.trim();

    if (!normalizedBody) {
      setNotice("Добавьте пару строк: что делали, где сломалось и что видите сейчас.");
      return;
    }

    setBusy(true);
    setError("");
    setNotice("");

    try {
      let attachment: TicketAttachmentInput | undefined;
      if (attachmentFile) {
        await validateSupportAttachment(attachmentFile);
        const uploaded = await uploadTicketAttachment(attachmentFile);
        attachment = { attachment_id: uploaded.attachment_id };
      }

      const title = normalizedSubject ? `[${category}] ${normalizedSubject}` : `[${category}] Обращение из кабинета`;
      const created = await createTicket(title, normalizedBody, attachment || undefined);

      setComposeOpen(false);
      setSubject("");
      setBody("");
      setAttachmentFile(null);
      await loadTickets();
      showToast(`Обращение #${created.id} создано.`, "success");
    } catch (nextError) {
      setError(userFacingErrorMessage(nextError, "Не получилось создать обращение. Попробуйте ещё раз или напишите в Telegram-поддержку."));
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <main className="mx-auto flex w-full max-w-[860px] flex-col gap-5">
        <StatusHero
          title={getCopyText("webapp.support.title", "Помощь")}
          meta={latestTicket ? `${statusLabel(latestTicket.status)} · #${latestTicket.id}` : "Кабинет и Telegram"}
          body={
            latestTicket
              ? "Продолжайте уже открытое обращение: история, вложения и контекст останутся в одном месте."
              : "Опишите проблему коротко. Личные ссылки, коды оплаты и банковские данные присылать не нужно."
          }
          tone={openCount ? "info" : "neutral"}
          icon={LifeBuoy}
          action={
            <Button onClick={() => openComposer(CATEGORIES[0])} className="w-full sm:w-auto">
              Новый вопрос
            </Button>
          }
        />

        <GroupedSection
          title="Последнее обращение"
          action={
            latestTicket ? (
              <AppRouteLink href={`/support/thread/?id=${latestTicket.id}`} className="text-sm font-semibold text-brand hover:text-brand-strong">
                Открыть
              </AppRouteLink>
            ) : null
          }
        >
          {loadingTickets ? (
            <Row icon={Hourglass} label="Загружаем обращения" hint="Обычно это занимает несколько секунд" />
          ) : latestTicket ? (
            <Row
              icon={MessagesSquare}
              label={latestTicket.subject || `Обращение #${latestTicket.id}`}
              hint={latestTicket.last_message_preview || "Сообщений пока нет"}
              value={formatDate(latestTicket.updated_at || latestTicket.created_at)}
              href={`/support/thread/?id=${latestTicket.id}`}
            />
          ) : (
            <Row icon={MessageCircle} label={getCopyText("webapp.support.empty_tickets", "Обращений пока нет")} hint="Создайте первый вопрос, если что-то пошло не так" />
          )}
        </GroupedSection>

        <GroupedSection title="Быстрые действия">
          <Row icon={BookOpenText} label="Все инструкции" hint="Пошаговые задачи с ветками ошибок" href="/guides/" />
          <Row
            icon={MessageSquarePlus}
            label="Новый вопрос"
            hint="Короткая форма с вложением"
            action={
              <button type="button" onClick={() => openComposer(CATEGORIES[0])} className="text-sm font-semibold text-brand hover:text-brand-strong">
                Написать
              </button>
            }
          />
          <Row
            icon={Send}
            label="Telegram"
            hint="Удобно для быстрого живого ответа"
            action={
              <AppRouteLink href={supportLink} target="_blank" hardNavigate={false} className="text-sm font-semibold text-brand hover:text-brand-strong">
                Открыть
              </AppRouteLink>
            }
          />
          <Row icon={Download} label="Скачать приложение" hint="Android и Windows" href="/downloads/" />
          <Row icon={KeyRound} label="Активировать код" hint="Оплата, подарок или промокод" href="/redeem/" />
          <Row icon={FileText} label="Документы" hint="Оплата и условия" href="/support/legal/" />
        </GroupedSection>

        <section className="flex flex-col gap-2.5">
          <h2 className="px-1 text-xs font-bold tracking-[0.08em] text-ink-soft uppercase">Частые вопросы</h2>
          <FaqAccordion entries={FAQ_ENTRIES} />
        </section>

        <section className="flex flex-col gap-2.5">
          <h2 className="px-1 text-xs font-bold tracking-[0.08em] text-ink-soft uppercase">Диагностика</h2>
          <TileGrid className="xl:grid-cols-3">
            <Tile icon={ShieldCheck} label="Доступ" value={resolvePlanLabel(dash, user)} hint="Без личных ключей" tone="success" />
            <Tile icon={MonitorSmartphone} label="Устройства" value={`${deviceCount} из ${deviceLimit}`} hint="Связано с профилем" tone="neutral" href="/devices/" />
            <Tile icon={Wifi} label="Подключения" value={String(activeConnections)} hint="Безопасная сводка" tone="info" />
          </TileGrid>
        </section>

        {notice ? <p className="px-1 text-sm font-semibold text-brand">{notice}</p> : null}
        {error ? <p className="px-1 text-sm text-danger-text">{error}</p> : null}
      </main>

      <AnimatePresence>
        {composeOpen ? (
          <motion.div
            className="fixed inset-0 z-[230] grid place-items-end bg-black/45 p-0 backdrop-blur-sm sm:place-items-center sm:p-4"
            onClick={() => setComposeOpen(false)}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: reduceMotion ? 0 : 0.22, ease: [0.22, 1, 0.36, 1] }}
          >
            <motion.div
              role="dialog"
              aria-modal="true"
              aria-label="Новое обращение"
              className="max-h-[92vh] w-full max-w-2xl overflow-y-auto rounded-t-modal border border-line bg-surface p-5 shadow-medium sm:rounded-modal sm:p-6"
              onClick={(event) => event.stopPropagation()}
              initial={reduceMotion ? { opacity: 0 } : { opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              exit={reduceMotion ? { opacity: 0 } : { opacity: 0, y: 24 }}
              transition={{ duration: reduceMotion ? 0 : 0.22, ease: [0.22, 1, 0.36, 1] }}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <p className="text-xs font-bold tracking-[0.08em] text-ink-soft uppercase">Новое обращение</p>
                  <h2 className="mt-2 text-2xl leading-tight font-semibold text-ink">Новый вопрос</h2>
                  <p className="mt-2 text-sm leading-6 text-ink-soft">{preset.hint}</p>
                </div>
                <Button variant="ghost" size="sm" onClick={() => setComposeOpen(false)} aria-label="Закрыть" className="!px-2">
                  <X size={18} strokeWidth={2} aria-hidden="true" />
                </Button>
              </div>

              <div className="mt-5 flex flex-wrap gap-2">
                {CATEGORIES.map((item) => (
                  <Chip
                    key={item}
                    active={item === category}
                    onClick={() => {
                      const nextPreset = CATEGORY_PRESETS[item];
                      setCategory(item);
                      setSubject(nextPreset.subject);
                      setBody(nextPreset.body);
                    }}
                  >
                    {item}
                  </Chip>
                ))}
              </div>

              <div className="mt-5 space-y-4">
                <Input
                  value={subject}
                  onChange={(event) => setSubject(event.target.value)}
                  placeholder="Коротко: что случилось"
                  autoFocus
                />
                <Textarea
                  value={body}
                  onChange={(event) => setBody(event.target.value)}
                  rows={7}
                  placeholder="Опишите, что делали, где сломалось и что видите сейчас."
                />

                <label className="block rounded-control border border-dashed border-line bg-canvas-alt px-4 py-4 text-sm">
                  <span className="block font-medium text-ink">Вложение</span>
                  <span className="mt-1 block text-xs leading-5 text-ink-soft">
                    PNG, JPEG, WebP, PDF или TXT до 20 МБ.
                  </span>
                  <input
                    type="file"
                    accept={SUPPORT_ATTACHMENT_ACCEPT}
                    className="mt-3 block w-full cursor-pointer text-sm text-ink-soft file:mr-3 file:rounded-control file:border-0 file:bg-brand-soft file:px-4 file:py-2 file:font-medium file:text-brand"
                    onChange={(event) => {
                      setError("");
                      setAttachmentFile(event.target.files?.[0] ?? null);
                    }}
                  />
                  {attachmentFile ? (
                    <div className="mt-3 flex items-center justify-between gap-3 rounded-tile bg-surface px-3 py-2 text-xs">
                      <span className="truncate">{attachmentFile.name}</span>
                      <button type="button" onClick={() => setAttachmentFile(null)} className="text-danger-text">
                        Убрать
                      </button>
                    </div>
                  ) : null}
                  {attachmentFile ? <p className="mt-2 text-xs text-ink-soft">{formatFileSize(attachmentFile.size)}</p> : null}
                </label>

                <div className="flex flex-wrap gap-3">
                  <Button loading={busy} disabled={!body.trim()} onClick={() => void onCreateTicket()}>
                    Отправить вопрос
                  </Button>
                  <Button
                    variant="secondary"
                    onClick={() => {
                      setSubject("");
                      setBody("");
                      setAttachmentFile(null);
                      setNotice("");
                    }}
                  >
                    Очистить
                  </Button>
                </div>
                {notice ? <Note tone="warning">{notice}</Note> : null}
                {error ? <Note tone="danger">{error}</Note> : null}
              </div>
            </motion.div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </>
  );
}
