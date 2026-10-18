/**
 * Heat indicator badge for stock level — red/orange/green.
 */
import React from "react";
import { cn } from "@/utils/cn";

interface StockBadgeProps {
  quantity: number;
  lowThreshold: number;
  criticalThreshold: number;
  unit?: string;
}

export function StockBadge({ quantity, lowThreshold, criticalThreshold, unit = "" }: StockBadgeProps) {
  const isCritical = quantity <= criticalThreshold;
  const isLow = quantity <= lowThreshold;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold tabular-nums",
        isCritical
          ? "bg-[#fbd9c8] text-red-400"
          : isLow
          ? "bg-[#fdeec2] text-amber-400"
          : "bg-[#dcebd6] text-emerald-400"
      )}
    >
      {isCritical && <span className="h-1.5 w-1.5 rounded-full bg-red-400" />}
      {isLow && !isCritical && <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />}
      {quantity} {unit}
    </span>
  );
}
