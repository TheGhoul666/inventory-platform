import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { BarChart3, Search } from "lucide-react";
import { analyticsService, inventoryService } from "@/services/inventoryService";
import { useTranslation } from "react-i18next";
import type { InventoryItem } from "@/types";

export function AnalyticsPage() {
  const { t } = useTranslation();
  const [search, setSearch] = useState("");
  const [selectedItem, setSelectedItem] = useState<InventoryItem | null>(null);
  const [showDropdown, setShowDropdown] = useState(false);

  const { data: itemsData } = useQuery({
    queryKey: ["inventory", "items", { search, analytics: true }],
    queryFn: () => inventoryService.listItems({ search: search || undefined, limit: 20 }),
    enabled: showDropdown,
  });

  const itemId = selectedItem?.id ?? "";

  const { data: usage } = useQuery({
    queryKey: ["analytics", "usage", itemId],
    queryFn: () => analyticsService.getItemUsage(itemId, 30),
    enabled: !!itemId,
  });

  const { data: depletion } = useQuery({
    queryKey: ["analytics", "depletion", itemId, selectedItem?.quantity],
    queryFn: () => analyticsService.getPredictedDepletion(itemId, Number(selectedItem?.quantity ?? 0)),
    enabled: !!itemId,
  });

  const { data: anomaly } = useQuery({
    queryKey: ["analytics", "anomaly", itemId],
    queryFn: () => analyticsService.getAnomalies(itemId),
    enabled: !!itemId,
  });

  const emaData = depletion?.ema_trend ?? [];
  const items: InventoryItem[] = itemsData?.items ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ink flex items-center gap-2">
          <BarChart3 className="h-6 w-6 text-brand-400" />
          {t("analytics.title")}
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          {t("analytics.consumption")}
        </p>
      </div>

      {/* Item selector */}
      <div className="card p-4">
        <label htmlFor="analytics-item" className="text-sm text-slate-400 block mb-2">{t("analytics.selectItem")}</label>
        <div className="relative">
          <Search className="absolute start-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none" />
          <input
            id="analytics-item"
            value={selectedItem ? `${selectedItem.sku} — ${selectedItem.name}` : search}
            onFocus={() => { setShowDropdown(true); if (selectedItem) { setSearch(""); setSelectedItem(null); } }}
            onChange={(e) => { setSearch(e.target.value); setShowDropdown(true); setSelectedItem(null); }}
            onBlur={() => setTimeout(() => setShowDropdown(false), 150)}
            placeholder={t("analytics.searchPlaceholder")}
            className="w-full ps-9 pe-4 py-2 bg-white border border-surface-600 rounded-lg text-ink placeholder-slate-400 focus:outline-none focus:border-brand-500 text-sm"
          />
          {showDropdown && items.length > 0 && (
            <div className="absolute top-full start-0 end-0 mt-1 bg-white border border-surface-600 rounded-lg shadow-xl z-20 overflow-hidden">
              {items.map((item) => (
                <button
                  key={item.id}
                  onMouseDown={() => { setSelectedItem(item); setShowDropdown(false); }}
                  className="w-full px-4 py-2.5 text-start hover:bg-surface-600 transition-colors flex items-center justify-between gap-4"
                >
                  <div>
                    <span className="text-ink text-sm font-medium">{item.name}</span>
                    <span className="text-slate-400 text-xs ms-2 font-mono">{item.sku}</span>
                  </div>
                  <span className="text-slate-400 text-xs shrink-0">
                    {item.quantity} {item.unit}
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {selectedItem && (
        <>
          {/* Key metrics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="card p-6">
              <p className="text-slate-400 text-sm">{t("analytics.dailyRate")}</p>
              <p className="text-3xl font-bold text-ink mt-1">
                {usage?.daily_consumption_rate?.toFixed(2) ?? "—"}
              </p>
              <p className="text-slate-400 text-xs mt-1">{t("analytics.perDayAvg", { unit: selectedItem.unit })}</p>
            </div>

            <div className="card p-6">
              <p className="text-slate-400 text-sm">{t("analytics.predictedDepletion")}</p>
              <p
                className={`text-3xl font-bold mt-1 ${
                  depletion?.predicted_days_left != null && depletion.predicted_days_left < 7
                    ? "text-red-400"
                    : "text-emerald-400"
                }`}
              >
                {depletion?.predicted_days_left != null
                  ? t("analytics.daysUnit", { n: depletion.predicted_days_left.toFixed(1) })
                  : "—"}
              </p>
              <p className="text-slate-400 text-xs mt-1">{t("analytics.atCurrentRate")}</p>
            </div>

            <div className="card p-6">
              <p className="text-slate-400 text-sm">{t("analytics.anomaly")}</p>
              {anomaly ? (
                <>
                  <p className={`text-3xl font-bold mt-1 ${anomaly.is_anomaly ? "text-red-400" : "text-emerald-400"}`}>
                    {anomaly.is_anomaly ? t("analytics.spike") : t("analytics.normal")}
                  </p>
                  <p className="text-slate-400 text-xs mt-1">{t("analytics.ratio", { ratio: anomaly.ratio })}</p>
                </>
              ) : (
                <p className="text-3xl font-bold text-slate-400 mt-1">—</p>
              )}
            </div>
          </div>

          {/* EMA chart */}
          {emaData.length > 0 && (
            <div className="card p-6">
              <h2 className="font-semibold text-ink mb-4">
                {t("analytics.emaTitle")}
              </h2>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={emaData}>
                  <defs>
                    <linearGradient id="emaGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#2d6a2b" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#2d6a2b" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#dde3f0" />
                  <XAxis dataKey="date" stroke="#475569" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#475569" tick={{ fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#ffffff",
                      border: "1px solid #c9d2e6",
                      borderRadius: "8px",
                    }}
                    labelStyle={{ color: "#0f172a" }}
                    itemStyle={{ color: "#475569" }}
                  />
                  <Area
                    type="monotone"
                    dataKey="ema"
                    stroke="#2d6a2b"
                    fill="url(#emaGrad)"
                    strokeWidth={2}
                    name={t("analytics.emaSeries")}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}

          {emaData.length === 0 && usage && (
            <div className="card p-8 text-center">
              <p className="text-slate-400 text-sm">
                {t("analytics.notEnough")}
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
