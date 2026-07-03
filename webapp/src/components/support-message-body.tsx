import type { ReactNode } from "react";

type SupportMessageBodyProps = {
  body: string;
  className?: string;
};

const NUMBERED_RE = /^(\d{1,2})[.)]\s+(.+)$/;
const BULLET_RE = /^[-*•]\s+(.+)$/;
const MARKDOWN_HEADING_RE = /^#{1,3}\s+(.+)$/;
const STRONG_PREFIX_RE = /^\*\*([^*]+)\*\*:?\s*(.*)$/;
const LABEL_PREFIX_RE =
  /^(Коротко|Что сделать|Если не поможет|Если не помогло|Важно|Проверьте|Что написать в поддержку|Безопасность|Дальше|Итог):\s*(.*)$/i;

function renderInline(text: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  const pattern = /(\*\*[^*]+\*\*|`[^`]+`)/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = pattern.exec(text)) !== null) {
    if (match.index > lastIndex) {
      nodes.push(text.slice(lastIndex, match.index));
    }

    const token = match[0];
    if (token.startsWith("**")) {
      nodes.push(
        <strong key={`${match.index}-strong`} className="font-semibold text-[var(--atlas-text)]">
          {token.slice(2, -2)}
        </strong>,
      );
    } else {
      nodes.push(
        <code key={`${match.index}-code`} className="rounded-md bg-[color:var(--atlas-canvas-alt)] px-1 py-0.5 text-[0.92em] text-[var(--atlas-text)]">
          {token.slice(1, -1)}
        </code>,
      );
    }
    lastIndex = pattern.lastIndex;
  }

  if (lastIndex < text.length) {
    nodes.push(text.slice(lastIndex));
  }
  return nodes;
}

function renderHeading(label: string, rest: string, key: string): ReactNode {
  if (rest.trim()) {
    return (
      <div key={key} className="space-y-1">
        <p className="text-[0.72rem] font-semibold uppercase tracking-[0.12em] text-[var(--atlas-text-muted)]">{label}</p>
        <p>{renderInline(rest.trim())}</p>
      </div>
    );
  }
  return (
    <p key={key} className="pt-1 text-[0.72rem] font-semibold uppercase tracking-[0.12em] text-[var(--atlas-text-muted)]">
      {label}
    </p>
  );
}

function renderLine(line: string, index: number): ReactNode {
  const key = `line-${index}`;
  const heading = line.match(MARKDOWN_HEADING_RE);
  if (heading) {
    return renderHeading(heading[1].trim(), "", key);
  }

  const strongPrefix = line.match(STRONG_PREFIX_RE);
  if (strongPrefix) {
    return renderHeading(strongPrefix[1].trim(), strongPrefix[2] || "", key);
  }

  const labelPrefix = line.match(LABEL_PREFIX_RE);
  if (labelPrefix) {
    return renderHeading(labelPrefix[1].trim(), labelPrefix[2] || "", key);
  }

  const numbered = line.match(NUMBERED_RE);
  if (numbered) {
    return (
      <div key={key} className="grid grid-cols-[1.45rem,1fr] gap-2">
        <span className="mt-0.5 inline-flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500/12 text-[0.68rem] font-semibold text-[color:var(--atlas-status-success-text)]">
          {numbered[1]}
        </span>
        <p>{renderInline(numbered[2].trim())}</p>
      </div>
    );
  }

  const bullet = line.match(BULLET_RE);
  if (bullet) {
    return (
      <div key={key} className="grid grid-cols-[0.8rem,1fr] gap-2">
        <span className="mt-[0.62rem] h-1.5 w-1.5 rounded-full bg-emerald-500/70" />
        <p>{renderInline(bullet[1].trim())}</p>
      </div>
    );
  }

  return <p key={key}>{renderInline(line)}</p>;
}

export function SupportMessageBody({ body, className = "" }: SupportMessageBodyProps) {
  const lines = String(body || "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

  if (!lines.length) {
    return null;
  }

  return <div className={`space-y-2 break-words ${className}`.trim()}>{lines.map(renderLine)}</div>;
}
