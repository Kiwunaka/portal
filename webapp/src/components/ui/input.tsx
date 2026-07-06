import type { InputHTMLAttributes, ReactNode, TextareaHTMLAttributes } from "react";

import { cn, FOCUS_RING } from "@/components/utils";

const CONTROL_CLASS =
  "w-full rounded-control border border-line bg-surface px-3.5 py-2.5 text-[0.9375rem] text-ink placeholder:text-ink-muted transition-colors duration-200 hover:border-line-strong disabled:opacity-55 motion-reduce:transition-none";

type FieldProps = {
  label?: ReactNode;
  hint?: ReactNode;
  error?: ReactNode;
  children: ReactNode;
  className?: string;
};

export function Field({ label, hint, error, children, className }: FieldProps) {
  return (
    <label className={cn("flex flex-col gap-1.5", className)}>
      {label ? <span className="text-sm font-semibold text-ink">{label}</span> : null}
      {children}
      {error ? (
        <span role="alert" className="text-sm text-danger-text">
          {error}
        </span>
      ) : hint ? (
        <span className="text-sm text-ink-soft">{hint}</span>
      ) : null}
    </label>
  );
}

type InputProps = Omit<InputHTMLAttributes<HTMLInputElement>, "className"> & { className?: string };

export function Input({ className, ...props }: InputProps) {
  return <input className={cn(CONTROL_CLASS, FOCUS_RING, className)} {...props} />;
}

type TextareaProps = Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, "className"> & { className?: string };

export function Textarea({ className, ...props }: TextareaProps) {
  return <textarea className={cn(CONTROL_CLASS, "min-h-24 resize-y", FOCUS_RING, className)} {...props} />;
}
