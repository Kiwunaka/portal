"use client";

import Link, { type LinkProps } from "next/link";
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

function dispatchRouteActivity(href: string): void {
  if (typeof window === "undefined") return;
  try {
    const targetUrl = new URL(href, window.location.href);
    const currentPath = `${normalizeAppPath(window.location.pathname)}${window.location.search}${window.location.hash}`;
    const targetPath = `${normalizeAppPath(targetUrl.pathname)}${targetUrl.search}${targetUrl.hash}`;
    if (targetUrl.origin === window.location.origin && targetPath !== currentPath) {
      window.dispatchEvent(new CustomEvent("pokrov-route-activity", { detail: { href: targetUrl.href } }));
    }
  } catch {
    // Ignore unusual href values and let Next handle the click.
  }
}

const AppRouteLink = forwardRef<HTMLAnchorElement, AppRouteLinkProps>(function AppRouteLink(
  { hardNavigate = true, onClick, target, rel, className, href, ...props },
  ref,
) {
  const nextRel = target === "_blank" ? [rel, "noopener noreferrer"].filter(Boolean).join(" ") : rel;

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
        if (!hardNavigate || target === "_blank" || !shouldUseBrowserNavigation(event)) {
          if (!hardNavigate && target !== "_blank" && shouldUseBrowserNavigation(event)) {
            dispatchRouteActivity(event.currentTarget.href);
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
