"use client";

import Link, { type LinkProps } from "next/link";
import { useRouter } from "next/navigation";
import { forwardRef, type AnchorHTMLAttributes, type MouseEvent } from "react";

import { cn, FOCUS_RING } from "./utils";

type AnchorProps = Omit<AnchorHTMLAttributes<HTMLAnchorElement>, keyof LinkProps>;

type AppRouteLinkProps = LinkProps &
  AnchorProps & {
    hardNavigate?: boolean;
  };

function shouldUseBrowserNavigation(event: MouseEvent<HTMLAnchorElement>): boolean {
  return !(
    event.defaultPrevented ||
    event.button !== 0 ||
    event.metaKey ||
    event.altKey ||
    event.ctrlKey ||
    event.shiftKey
  );
}

function normalizeAppPath(pathname: string): string {
  if (pathname.length <= 1) return "/";
  return pathname.replace(/\/+$/, "");
}

function resolveInternalNavigationPath(href: string): string | null {
  if (typeof window === "undefined") return null;
  try {
    const targetUrl = new URL(href, window.location.href);
    const currentPath = `${normalizeAppPath(window.location.pathname)}${window.location.search}${window.location.hash}`;
    const targetPath = `${normalizeAppPath(targetUrl.pathname)}${targetUrl.search}${targetUrl.hash}`;
    if (targetUrl.origin !== window.location.origin || targetPath === currentPath) return null;
    return targetPath || "/";
  } catch {
    return null;
  }
}

function dispatchRouteActivity(href: string): void {
  if (typeof window === "undefined") return;
  try {
    const targetUrl = new URL(href, window.location.href);
    if (resolveInternalNavigationPath(href)) {
      window.dispatchEvent(new CustomEvent("pokrov-route-activity", { detail: { href: targetUrl.href } }));
    }
  } catch {
    // Ignore unusual href values and let Next handle the click.
  }
}

function scheduleNavigationFallback(targetPath: string, targetHref: string): void {
  if (typeof window === "undefined") return;
  const key = `${targetPath}:${Date.now()}:${Math.random().toString(36).slice(2)}`;
  const navWindow = window as Window & { __pokrovRouteNavKey?: string };
  navWindow.__pokrovRouteNavKey = key;
  window.setTimeout(() => {
    if (navWindow.__pokrovRouteNavKey !== key) return;
    const currentPath = `${normalizeAppPath(window.location.pathname)}${window.location.search}${window.location.hash}`;
    if (currentPath !== targetPath) {
      window.location.assign(targetHref);
    }
  }, 900);
}

const AppRouteLink = forwardRef<HTMLAnchorElement, AppRouteLinkProps>(function AppRouteLink(
  { hardNavigate = false, onClick, target, rel, className, href, ...props },
  ref,
) {
  const nextRel = target === "_blank" ? [rel, "noopener noreferrer"].filter(Boolean).join(" ") : rel;
  const router = useRouter();

  return (
    <Link
      {...props}
      className={cn(FOCUS_RING, className)}
      ref={ref}
      href={href}
      rel={nextRel}
      target={target}
      onClick={(event) => {
        onClick?.(event);
        if (event.defaultPrevented) {
          return;
        }
        if (target === "_blank" || !shouldUseBrowserNavigation(event)) {
          return;
        }
        if (!hardNavigate) {
          const targetPath = resolveInternalNavigationPath(event.currentTarget.href);
          if (targetPath) {
            event.preventDefault();
            dispatchRouteActivity(event.currentTarget.href);
            router.push(targetPath);
            scheduleNavigationFallback(targetPath, event.currentTarget.href);
          }
          return;
        }
        event.preventDefault();
        window.location.assign(event.currentTarget.href);
      }}
    />
  );
});

export default AppRouteLink;
