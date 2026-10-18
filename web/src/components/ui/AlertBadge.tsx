import React from "react";
import { cn } from "@/utils/cn";
import type { AlertSeverity } from "@/types";

const severityStyles: Record<AlertSeverity, string> = {
  INFO: "bg-[#dcebd6] text-[#2f5a3a]",
  WARNING: "bg-[#fdeec2] text-amber-400",
  CRITICAL: "bg-[#fbd9c8] text-red-400",
  EMERGENCY: "bg-[#e7d6f0] text-purple-400",
};

export function AlertBadge({ severity }: { severity: AlertSeverity }) {
  return (
    <span className={cn("rounded-full px-2.5 py-0.5 text-xs font-bold uppercase", severityStyles[severity])}>
      {severity}
    </span>
  );
}
