"use client";

import Link, { type LinkProps } from "next/link";
import { forwardRef, type AnchorHTMLAttributes, type MouseEvent } from "react";

import { cn, FOCUS_RING } from "./utils";

type AnchorProps = Omit<AnchorHTMLAttributes<HTMLAnchorElement>, keyof LinkProps>;

type AppRouteLinkProps = LinkProps &
  AnchorProps & {
    /** Force a full document navigation. Reserved for auth-boundary flows
     * (login/logout, OIDC redirects, handoff-token URLs) and external hosts. */
    hardNavigate?: boolean;
  };

type RouteNavigationLock = {
  key: string;
  startedAt: number;
};

type RouteWindow = Window & {
  __pokrovRouteNavigationLock?: RouteNavigationLock;
};

const DUPLICATE_NAVIGATION_WINDOW_MS = 1200;

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

function internalNavigationKey(href: string): string | null {
  if (typeof window === "undefined") return null;
  try {
    const targetUrl = new URL(href, window.location.href);
    const currentPath = `${normalizeAppPath(window.location.pathname)}${window.location.search}${window.location.hash}`;
    const targetPath = `${normalizeAppPath(targetUrl.pathname)}${targetUrl.search}${targetUrl.hash}`;
    return targetUrl.origin === window.location.origin && targetPath !== currentPath ? targetPath : null;
  } catch {
    return null;
  }
}

function dispatchRouteActivity(href: string): void {
  if (typeof window === "undefined") return;
  try {
    const targetUrl = new URL(href, window.location.href);
    if (internalNavigationKey(href)) {
      window.dispatchEvent(new CustomEvent("pokrov-route-activity", { detail: { href: targetUrl.href } }));
    }
  } catch {
    // Ignore unusual href values and let Next handle the click.
  }
}

function shouldSuppressDuplicateNavigation(href: string): boolean {
  if (typeof window === "undefined") return false;
  const key = internalNavigationKey(href);
  if (!key) return false;

  const routeWindow = window as RouteWindow;
  const now = window.performance?.now?.() ?? Date.now();
  const lock = routeWindow.__pokrovRouteNavigationLock;
  if (lock && lock.key === key && now - lock.startedAt < DUPLICATE_NAVIGATION_WINDOW_MS) {
    return true;
  }

  routeWindow.__pokrovRouteNavigationLock = { key, startedAt: now };
  window.setTimeout(() => {
    if (routeWindow.__pokrovRouteNavigationLock?.key === key) {
      delete routeWindow.__pokrovRouteNavigationLock;
    }
  }, DUPLICATE_NAVIGATION_WINDOW_MS);
  return false;
}

const AppRouteLink = forwardRef<HTMLAnchorElement, AppRouteLinkProps>(function AppRouteLink(
  { hardNavigate = false, onClick, target, rel, className, href, prefetch = false, ...props },
  ref,
) {
  const nextRel = target === "_blank" ? [rel, "noopener noreferrer"].filter(Boolean).join(" ") : rel;

  return (
    <Link
      {...props}
      className={cn(FOCUS_RING, className)}
      ref={ref}
      href={href}
      prefetch={prefetch}
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
        const targetHref = event.currentTarget.href;
        if (hardNavigate) {
          event.preventDefault();
          window.location.assign(targetHref);
          return;
        }
        if (shouldSuppressDuplicateNavigation(targetHref)) {
          event.preventDefault();
          return;
        }
        // Client-side navigation: Next Link handles the transition, the shell
        // shows route activity until the pathname changes.
        dispatchRouteActivity(targetHref);
      }}
    />
  );
});

export default AppRouteLink;
