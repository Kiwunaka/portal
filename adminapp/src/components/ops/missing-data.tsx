export const MISSING_DATA_TEXT = "— · Нет данных";

export function MissingData({ inline = false, className = "" }: { inline?: boolean; className?: string }) {
  if (inline) {
    return <span className={className}><span className="font-semibold">—</span><span className="text-[color:var(--atlas-text-muted)]"> · Нет данных</span></span>;
  }
  return (
    <span className={className}>
      <span className="font-semibold">—</span>
      <span className="block text-[11px] text-[color:var(--atlas-text-muted)]">Нет данных</span>
    </span>
  );
}
