import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Bell, CheckCircle, XCircle, Filter } from "lucide-react";
import toast from "react-hot-toast";
import { alertService } from "@/services/inventoryService";
import { AlertBadge } from "@/components/ui/AlertBadge";
import { useTranslation } from "react-i18next";
import type { Alert, AlertSeverity, AlertStatus } from "@/types";

export function AlertsPage() {
  const qc = useQueryClient();
  const { t } = useTranslation();
  const [statusFilter, setStatusFilter] = useState<string>("OPEN");

  const { data, isLoading } = useQuery({
    queryKey: ["alerts", statusFilter],
    queryFn: () => alertService.listAlerts({ status: statusFilter || undefined }),
    refetchInterval: 15_000,
  });

  const acknowledgeMutation = useMutation({
    mutationFn: (id: string) => alertService.acknowledgeAlert(id),
    onSuccess: () => {
      toast.success(t("alerts.alertAcknowledged"));
      qc.invalidateQueries({ queryKey: ["alerts"] });
    },
  });

  const resolveMutation = useMutation({
    mutationFn: (id: string) => alertService.resolveAlert(id),
    onSuccess: () => {
      toast.success(t("alerts.alertResolved"));
      qc.invalidateQueries({ queryKey: ["alerts"] });
    },
  });

  const alerts: Alert[] = data?.alerts ?? [];

  const statusColors: Record<AlertStatus, string> = {
    OPEN: "text-amber-400",
    ACKNOWLEDGED: "text-blue-400",
    RESOLVED: "text-emerald-400",
    ESCALATED: "text-red-400",
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Bell className="h-6 w-6 text-amber-400" />
            {t("alerts.title")}
          </h1>
          <p className="text-slate-400 text-sm mt-1">{alerts.length} {t("alerts.title").toLowerCase()}</p>
        </div>
        <div className="flex gap-2">
          {(["", "OPEN", "ACKNOWLEDGED", "RESOLVED"] as const).map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                statusFilter === s
                  ? "bg-brand-600 text-white"
                  : "bg-surface-700 text-slate-400 hover:text-white"
              }`}
            >
              {s || "All"}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-3">
        {isLoading
          ? Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="bg-surface-800 rounded-xl border border-surface-700 p-4 animate-pulse h-24" />
            ))
          : alerts.length === 0
          ? (
            <div className="bg-surface-800 rounded-xl border border-surface-700 p-12 text-center">
              <CheckCircle className="h-12 w-12 text-emerald-400 mx-auto mb-3" />
              <p className="text-slate-300 font-medium">{t("alerts.noAlerts")}</p>
              <p className="text-slate-500 text-sm mt-1">{t("alerts.allClear")}</p>
            </div>
          )
          : alerts.map((alert) => (
            <div
              key={alert.id}
              className="bg-surface-800 rounded-xl border border-surface-700 p-4 hover:border-surface-600 transition-colors"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <AlertBadge severity={alert.severity} />
                    <span className={`text-xs font-medium ${statusColors[alert.status]}`}>
                      {alert.status}
                    </span>
                    <span className="text-xs text-slate-600">{alert.type}</span>
                  </div>
                  <h3 className="font-medium text-white">{alert.title}</h3>
                  <p className="text-slate-400 text-sm mt-0.5">{alert.message}</p>
                  <p className="text-slate-600 text-xs mt-2">
                    {new Date(alert.created_at).toLocaleString()}
                    {alert.acknowledged_at && (
                      <span className="ml-3">
                        Acknowledged: {new Date(alert.acknowledged_at).toLocaleString()}
                      </span>
                    )}
                  </p>
                </div>
                {alert.status === "OPEN" && (
                  <div className="flex gap-2 shrink-0">
                    <button
                      onClick={() => acknowledgeMutation.mutate(alert.id)}
                      disabled={acknowledgeMutation.isPending}
                      className="px-3 py-1.5 bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 rounded-lg text-xs font-medium transition-colors"
                    >
                      {t("alerts.acknowledge")}
                    </button>
                    <button
                      onClick={() => resolveMutation.mutate(alert.id)}
                      disabled={resolveMutation.isPending}
                      className="px-3 py-1.5 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 rounded-lg text-xs font-medium transition-colors"
                    >
                      {t("alerts.resolve")}
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
      </div>
    </div>
  );
}
