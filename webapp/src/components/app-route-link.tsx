"use client";

import Link, { type LinkProps } from "next/link";
import { forwardRef, type AnchorHTMLAttributes, type MouseEvent } from "react";

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
  { hardNavigate = true, prefetch = false, onClick, target, href, ...props },
  ref,
) {
  return (
    <Link
      {...props}
      ref={ref}
      href={href}
      prefetch={prefetch}
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
