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

const AppRouteLink = forwardRef<HTMLAnchorElement, AppRouteLinkProps>(function AppRouteLink(
  { hardNavigate = false, onClick, target, rel, className, href, ...props },
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
        if (!hardNavigate || target === "_blank" || !shouldUseBrowserNavigation(event)) {
          return;
        }
        event.preventDefault();
        window.location.assign(event.currentTarget.href);
      }}
    />
  );
});

export default AppRouteLink;
