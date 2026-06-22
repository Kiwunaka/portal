import type { ReactNode } from "react";
import {
  ArrowLeft,
  AtSign,
  Award,
  BadgeCheck,
  Bot,
  CalendarCheck,
  CalendarDays,
  CalendarSync,
  ChevronRight,
  Circle,
  CircleCheck,
  CircleHelp,
  CirclePlus,
  CircleUser,
  ClipboardCheck,
  Clock,
  CloudDownload,
  Compass,
  CreditCard,
  Download,
  ExternalLink,
  FileText,
  Gauge,
  Gift,
  Globe,
  Hourglass,
  KeyRound,
  LayoutDashboard,
  LifeBuoy,
  Lock,
  LogIn,
  LogOut,
  type LucideIcon,
  Megaphone,
  Menu,
  MessageCircle,
  MessageSquarePlus,
  MessagesSquare,
  Monitor,
  MonitorSmartphone,
  Moon,
  Network,
  Paperclip,
  QrCode,
  RefreshCw,
  Search,
  Send,
  Settings,
  Shield,
  ShieldCheck,
  ShieldHalf,
  Smartphone,
  Sun,
  Tag,
  TriangleAlert,
  Users,
  Wallet,
  Wifi,
  X,
} from "lucide-react";

import { cn } from "@/components/utils";

/**
 * Single cabinet icon family.
 *
 * The cabinet historically used Google "Material Symbols" loaded as a webfont.
 * That shipped a second icon system (admin already uses lucide), forced two
 * render-blocking font stylesheets, and showed raw text names before the font
 * loaded. This module maps the legacy Material Symbol names to lucide-react so
 * every cabinet surface uses one family, with no external font dependency.
 */
const ICONS: Record<string, LucideIcon> = {
  // navigation / shell
  shield: Shield,
  shield_check: ShieldCheck,
  payments: CreditCard,
  support_agent: LifeBuoy,
  account_circle: CircleUser,
  admin_panel_settings: ShieldHalf,
  dashboard: LayoutDashboard,
  settings: Settings,
  menu: Menu,
  close: X,
  light_mode: Sun,
  dark_mode: Moon,
  open_in_new: ExternalLink,
  logout: LogOut,
  login: LogIn,
  chevron_right: ChevronRight,
  arrow_back: ArrowLeft,

  // status / access
  verified_user: ShieldCheck,
  warning: TriangleAlert,
  speed: Gauge,
  event_available: CalendarCheck,
  event_repeat: CalendarSync,
  calendar_month: CalendarDays,
  schedule: Clock,
  pending_actions: Clock,
  update: RefreshCw,
  workspace_premium: BadgeCheck,
  award: Award,

  // devices / network
  devices: MonitorSmartphone,
  smartphone: Smartphone,
  android: Smartphone,
  desktop_windows: Monitor,
  wifi_tethering: Wifi,
  hub: Network,
  group: Users,

  // actions
  key: KeyRound,
  add_circle: CirclePlus,
  add_comment: MessageSquarePlus,
  download: Download,
  backup: CloudDownload,
  qr_code_2: QrCode,
  search: Search,
  help: CircleHelp,
  check_circle: CircleCheck,
  fact_check: ClipboardCheck,
  send: Send,
  alternate_email: AtSign,
  campaign: Megaphone,
  gift: Gift,
  wallet: Wallet,
  attach: Paperclip,
  lock: Lock,

  // content
  description: FileText,
  contract: FileText,
  privacy_tip: ShieldCheck,
  label: Tag,
  forum: MessagesSquare,
  chat_bubble: MessageCircle,
  hourglass_empty: Hourglass,
  bot: Bot,

  // empty / not-found
  travel_explore: Globe,
  explore_off: Compass,
};

export type CabinetIconName = keyof typeof ICONS | (string & {});

type CabinetIconProps = {
  name: CabinetIconName;
  className?: string;
  strokeWidth?: number;
};

export function CabinetIcon({ name, className, strokeWidth = 1.75 }: CabinetIconProps) {
  const Glyph = ICONS[name] ?? Circle;
  return <Glyph className={cn("h-5 w-5", className)} strokeWidth={strokeWidth} aria-hidden="true" />;
}

/** Drop-in replacement for the per-page `icon(name)` helper. */
export function icon(name: CabinetIconName, className?: string): ReactNode {
  return <CabinetIcon name={name} className={className} />;
}

export default CabinetIcon;
