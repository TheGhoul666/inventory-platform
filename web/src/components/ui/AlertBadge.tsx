import React from "react";
import { cn } from "@/utils/cn";
import type { AlertSeverity } from "@/types";

const severityStyles: Record<AlertSeverity, string> = {
  INFO: "bg-blue-500/20 text-blue-400",
  WARNING: "bg-amber-500/20 text-amber-400",
  CRITICAL: "bg-red-500/20 text-red-400",
  EMERGENCY: "bg-purple-500/20 text-purple-400",
};

export function AlertBadge({ severity }: { severity: AlertSeverity }) {
  return (
    <span className={cn("rounded-sm border border-current/30 px-2 py-0.5 text-xs font-bold uppercase", severityStyles[severity])}>
      {severity}
    </span>
  );
}
