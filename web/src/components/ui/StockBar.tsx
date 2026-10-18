import React from "react";
import { cn } from "@/utils/cn";

export type StockStatus = "critical" | "low" | "ok";

export const stockStatus = (quantity: number, low: number, critical: number): StockStatus =>
  quantity <= critical ? "critical" : quantity <= low ? "low" : "ok";

const FILL: Record<StockStatus, string> = { critical: "bg-clay", low: "bg-[#c79a14]", ok: "bg-brand-600" };

/** Level bar with the critical (red) and low (yellow) threshold marks; `label` is the accessible text. */
export function StockBar({
  quantity,
  low,
  critical,
  label,
  className,
}: {
  quantity: number;
  low: number;
  critical: number;
  label: string;
  className?: string;
}) {
  const scale = Math.max(low * 2.5, quantity, 1);
  return (
    <div role="img" aria-label={label} className={cn("relative h-3.5 rounded-full bg-surface-700", className)}>
      <div
        className={cn("h-full rounded-full", FILL[stockStatus(quantity, low, critical)])}
        style={{ width: `${Math.min(100, (quantity / scale) * 100)}%` }}
      />
      <span className="absolute -inset-y-[3px] w-0.5 bg-clay" style={{ insetInlineStart: `${(critical / scale) * 100}%` }} />
      <span className="absolute -inset-y-[3px] w-0.5 bg-[#c79a14]" style={{ insetInlineStart: `${(low / scale) * 100}%` }} />
    </div>
  );
}
