"use client";

import {
  flexRender,
  getCoreRowModel,
  useReactTable,
  type ColumnDef
} from "@tanstack/react-table";

import { cn } from "@/components/utils";

export interface DataTableProps<T> {
  data: T[];
  columns: ColumnDef<T>[];
  empty?: string;
  className?: string;
}

export function DataTable<T>({ data, columns, empty = "Нет данных", className }: DataTableProps<T>) {
  // TanStack Table returns callable table helpers that React Compiler intentionally skips.
  // eslint-disable-next-line react-hooks/incompatible-library
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel()
  });

  return (
    <div className={cn("ops-data-table ops-scrollbar overflow-auto rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)]", className)}>
      <table className="w-full min-w-[760px] border-collapse text-left text-xs">
        <thead className="sticky top-0 z-10 bg-[color:var(--pokrov-table-header-bg)] text-[10px] uppercase tracking-[0.055em] text-[color:var(--atlas-text-muted)]">
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <th key={header.id} className="border-b border-[color:var(--pokrov-table-divider)] px-3 py-2 font-semibold">
                  {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.length ? (
            table.getRowModel().rows.map((row) => (
              <tr key={row.id} className="h-[var(--pokrov-table-row-height)] border-b border-[color:var(--pokrov-table-divider)] transition-colors hover:bg-[color:var(--pokrov-table-row-hover-bg)]">
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-3 py-2 align-middle text-[color:var(--atlas-text)]">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={Math.max(1, columns.length)} className="px-3 py-8 text-center text-sm text-[color:var(--atlas-text-muted)]">
                {empty}
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

export type { ColumnDef } from "@tanstack/react-table";
