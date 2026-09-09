"use client";

import { Children, Fragment, cloneElement, useCallback, useEffect, useId, useRef, useState, type ComponentPropsWithRef, type ReactElement, type RefObject } from "react";
import { defaultRangeExtractor, useVirtualizer, type Range } from "@tanstack/react-virtual";

import { cn } from "@/components/utils";
import { Button } from "./button";

type TableRow = ReactElement<ComponentPropsWithRef<"tr"> & { "data-index"?: number }>;

export function WindowedTable({
  label,
  header,
  rows,
  columnCount,
  className,
  tableClassName,
  scrollRef,
}: {
  label: string;
  header: ReactElement<ComponentPropsWithRef<"thead">>;
  rows: TableRow[];
  columnCount: number;
  className?: string;
  tableClassName?: string;
  scrollRef?: RefObject<HTMLDivElement | null>;
}) {
  const id = useId();
  const localScrollRef = useRef<HTMLDivElement>(null);
  const viewport = scrollRef ?? localScrollRef;
  const headerRef = useRef<HTMLTableSectionElement>(null);
  const [headerHeight, setHeaderHeight] = useState(0);
  const [reading, setReading] = useState(false);
  const [focusedKey, setFocusedKey] = useState<string | null>(null);
  const long = rows.length > 40;
  const windowed = long && !reading;
  const headerRows = Children.count(header.props.children);
  const itemKey = useCallback((index: number) => rows[index].key ?? index, [rows]);
  const rangeExtractor = useCallback((range: Range) => {
    const indexes = defaultRangeExtractor(range);
    const focusedIndex = focusedKey === null ? -1 : rows.findIndex((row, index) => String(row.key ?? index) === focusedKey);
    // Keep the focused control and its neighbours mounted during wheel/keyboard scrolling.
    if (focusedIndex >= 0) {
      for (let index = Math.max(0, focusedIndex - 1); index <= Math.min(rows.length - 1, focusedIndex + 1); index += 1) indexes.push(index);
    }
    return [...new Set(indexes)].sort((left, right) => left - right);
  }, [focusedKey, rows]);
  // TanStack Virtual keeps mutable measurements; React Compiler skips this component.
  // eslint-disable-next-line react-hooks/incompatible-library
  const virtualizer = useVirtualizer<HTMLDivElement, HTMLTableRowElement>({
    count: rows.length,
    getScrollElement: () => viewport.current,
    getItemKey: itemKey,
    estimateSize: () => 64,
    overscan: 8,
    paddingStart: headerHeight,
    scrollPaddingStart: headerHeight,
    rangeExtractor,
    enabled: windowed,
  });

  useEffect(() => {
    const element = headerRef.current;
    if (!windowed || !element) return;
    const observer = new ResizeObserver(() => setHeaderHeight(element.getBoundingClientRect().height));
    observer.observe(element);
    return () => observer.disconnect();
  }, [windowed]);

  const items = virtualizer.getVirtualItems();
  const totalHeight = virtualizer.getTotalSize();
  const spacer = (height: number) => <tr aria-hidden="true" role="presentation"><td colSpan={columnCount} style={{ height, padding: 0, border: 0 }} /></tr>;

  return (
    <div className="min-w-0 space-y-2">
      {long ? (
        <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-[color:var(--atlas-text-soft)]">
          <span id={`${id}-help`}>{rows.length} строк · {reading ? "Все строки открыты для чтения и поиска на странице." : "Прокрутите таблицу или откройте все строки для чтения."}</span>
          <Button size="compact" aria-controls={id} aria-pressed={reading} onClick={() => setReading((current) => !current)}>{reading ? "Вернуть компактный вид" : "Режим чтения"}</Button>
        </div>
      ) : null}
      <div
        ref={viewport}
        role={long ? "region" : undefined}
        aria-label={long ? `${label}: прокрутка` : undefined}
        aria-describedby={long ? `${id}-help` : undefined}
        tabIndex={windowed ? 0 : undefined}
        className={cn("ops-scrollbar overflow-auto rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[color:var(--atlas-focus)]", className)}
        style={long ? { maxHeight: reading ? "none" : "min(60dvh, 32rem)" } : undefined}
        onKeyDown={(event) => {
          if (!windowed || event.target !== event.currentTarget || event.ctrlKey || event.metaKey || event.altKey) return;
          if (event.key === "Home" || event.key === "End") {
            event.preventDefault();
            virtualizer.scrollToIndex(event.key === "Home" ? 0 : rows.length - 1, { align: event.key === "Home" ? "start" : "end" });
          }
        }}
        onFocusCapture={(event) => {
          if (!windowed) return;
          const row = (event.target as HTMLElement).closest<HTMLTableRowElement>("tr[data-index]");
          setFocusedKey(row ? String(itemKey(Number(row.dataset.index))) : null);
        }}
        onBlurCapture={(event) => {
          if (windowed && !event.currentTarget.contains(event.relatedTarget)) setFocusedKey(null);
        }}
      >
        <table id={id} aria-label={label} aria-rowcount={windowed ? rows.length + headerRows : undefined} className={tableClassName}>
          {cloneElement(header, { ref: headerRef, className: cn(header.props.className, windowed && "sticky top-0 z-10 bg-[color:var(--pokrov-table-header-bg)]") })}
          <tbody>
            {windowed ? items.map((item, itemIndex) => {
              const gap = item.start - (itemIndex ? items[itemIndex - 1].end : headerHeight);
              return <Fragment key={`row:${item.key}`}>
                {gap > 0 ? spacer(gap) : null}
                {cloneElement(rows[item.index], { "data-index": item.index, "aria-rowindex": headerRows + item.index + 1, ref: virtualizer.measureElement })}
              </Fragment>;
            }) : rows}
            {windowed && totalHeight > (items.at(-1)?.end ?? headerHeight) ? spacer(totalHeight - (items.at(-1)?.end ?? headerHeight)) : null}
          </tbody>
        </table>
      </div>
    </div>
  );
}
