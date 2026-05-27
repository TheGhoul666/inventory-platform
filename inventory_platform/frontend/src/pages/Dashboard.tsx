/**
 * Operations Dashboard — real-time overview of critical metrics.
 */
import React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  Package,
  TrendingDown,
  Activity,
  RefreshCw,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from "recharts";
import { analyticsService, alertService } from "@/services/inventoryService";
import { StockBadge } from "@/components/ui/StockBadge";
import { AlertBadge } from "@/components/ui/AlertBadge";
import { useTranslation } from "react-i18next";
import type { Alert } from "@/types";

function StatCard({
  title,
  value,
  icon: Icon,
  color,
  subtitle,
}: {
  title: string;
  value: number | string;
  icon: React.ElementType;
  color: string;
  subtitle?: string;
}) {
  return (
    <div className="bg-surface-800 rounded-xl border border-surface-700 p-6">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-slate-400 text-sm font-medium">{title}</p>
          <p className={`text-3xl font-bold mt-1 ${color}`}>{value}</p>
          {subtitle && <p className="text-slate-500 text-xs mt-1">{subtitle}</p>}
        </div>
        <div className={`p-3 rounded-lg ${color.includes("red") ? "bg-red-500/10" : color.includes("amber") ? "bg-amber-500/10" : "bg-brand-500/10"}`}>
          <Icon className={`h-6 w-6 ${color}`} />
        </div>
      </div>
    </div>
  );
}

export function Dashboard() {
  const { t } = useTranslation();
  const { data: summary, isLoading: summaryLoading, refetch } = useQuery({
    queryKey: ["analytics", "dashboard"],
    queryFn: analyticsService.getDashboardSummary,
    refetchInterval: 60_000,
  });

  const { data: alertsData } = useQuery({
    queryKey: ["alerts", "dashboard"],
    queryFn: () => alertService.listAlerts({ status: "OPEN", limit: 5 }),
    refetchInterval: 30_000,
  });

  if (summaryLoading) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-400">
        <RefreshCw className="h-8 w-8 animate-spin mr-3" />
        {t("dashboard.loading")}
      </div>
    );
  }

  const openAlerts: Alert[] = alertsData?.alerts ?? [];
  const criticalItems = summary?.critical_items ?? [];

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">{t("dashboard.title")}</h1>
          <p className="text-slate-400 text-sm mt-1">
            {t("dashboard.subtitle")} •{" "}
            {summary?.generated_at
              ? new Date(summary.generated_at).toLocaleTimeString()
              : "—"}
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="flex items-center gap-2 px-4 py-2 bg-surface-700 hover:bg-surface-600 rounded-lg text-sm text-slate-300 transition-colors"
        >
          <RefreshCw className="h-4 w-4" />
          {t("dashboard.refresh")}
        </button>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title={t("dashboard.criticalStock")}
          value={summary?.critical_stock_count ?? 0}
          icon={AlertTriangle}
          color={summary?.critical_stock_count > 0 ? "text-red-400" : "text-emerald-400"}
          subtitle={t("dashboard.criticalSubtitle")}
        />
        <StatCard
          title={t("dashboard.lowStock")}
          value={summary?.low_stock_count ?? 0}
          icon={TrendingDown}
          color={summary?.low_stock_count > 0 ? "text-amber-400" : "text-emerald-400"}
          subtitle={t("dashboard.lowSubtitle")}
        />
        <StatCard
          title={t("dashboard.openAlerts")}
          value={openAlerts.length}
          icon={Activity}
          color={openAlerts.length > 0 ? "text-amber-400" : "text-emerald-400"}
          subtitle={t("dashboard.alertsSubtitle")}
        />
        <StatCard
          title={t("dashboard.itemsMonitored")}
          value={summary?.total_items_count ?? "—"}
          icon={Package}
          color="text-brand-400"
          subtitle={t("dashboard.itemsSubtitle")}
        />
      </div>

      {/* Critical items + open alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Critical stock table */}
        <div className="bg-surface-800 rounded-xl border border-surface-700">
          <div className="p-4 border-b border-surface-700">
            <h2 className="font-semibold text-white flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-red-400" />
              {t("dashboard.criticalStockTitle")}
            </h2>
          </div>
          <div className="divide-y divide-surface-700">
            {criticalItems.length === 0 ? (
              <p className="p-6 text-center text-slate-500 text-sm">{t("dashboard.noCritical")}</p>
            ) : (
              criticalItems.map((item: any) => (
                <div key={item.id} className="p-4 flex items-center justify-between hover:bg-surface-700/50 transition-colors">
                  <div>
                    <p className="font-medium text-white text-sm">{item.name}</p>
                    <p className="text-slate-500 text-xs font-mono">{item.sku}</p>
                  </div>
                  <StockBadge
                    quantity={item.quantity}
                    lowThreshold={item.threshold}
                    criticalThreshold={item.threshold}
                  />
                </div>
              ))
            )}
          </div>
        </div>

        {/* Open alerts */}
        <div className="bg-surface-800 rounded-xl border border-surface-700">
          <div className="p-4 border-b border-surface-700">
            <h2 className="font-semibold text-white flex items-center gap-2">
              <Activity className="h-4 w-4 text-amber-400" />
              {t("dashboard.openAlertsTitle")}
            </h2>
          </div>
          <div className="divide-y divide-surface-700">
            {openAlerts.length === 0 ? (
              <p className="p-6 text-center text-slate-500 text-sm">{t("dashboard.noAlerts")}</p>
            ) : (
              openAlerts.map((alert) => (
                <div key={alert.id} className="p-4 hover:bg-surface-700/50 transition-colors">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-white text-sm truncate">{alert.title}</p>
                      <p className="text-slate-400 text-xs mt-0.5 truncate">{alert.message}</p>
                    </div>
                    <AlertBadge severity={alert.severity} />
                  </div>
                  <p className="text-slate-600 text-xs mt-1.5">
                    {new Date(alert.created_at).toLocaleString()}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
