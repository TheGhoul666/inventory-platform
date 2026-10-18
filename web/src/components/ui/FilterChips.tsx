import React from "react";
import { cn } from "@/utils/cn";

export interface ChipOption<T extends string> {
  value: T;
  label: React.ReactNode;
}

/** Pill-shaped single-choice filter (like the sign-in tabs). */
export function FilterChips<T extends string>({
  options,
  value,
  onChange,
  label,
}: {
  options: ChipOption<T>[];
  value: T;
  onChange: (v: T) => void;
  label: string;
}) {
  return (
    <div role="group" aria-label={label} className="flex flex-wrap gap-1 rounded-full bg-surface-700 p-1">
      {options.map((o) => (
        <button
          key={o.value}
          type="button"
          aria-pressed={value === o.value}
          onClick={() => onChange(o.value)}
          className={cn(
            "rounded-full px-3.5 py-1.5 text-sm font-medium transition-colors",
            value === o.value ? "bg-brand-600 text-white" : "text-slate-400 hover:text-ink"
          )}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}
