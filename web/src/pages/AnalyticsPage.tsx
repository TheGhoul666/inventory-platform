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
    queryKey: ["analytics", "depletion", itemId],
    queryFn: () => analyticsService.getPredictedDepletion(itemId),
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
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <BarChart3 className="h-6 w-6 text-brand-400" />
          {t("analytics.title")}
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          {t("analytics.consumption")}
        </p>
      </div>

      {/* Item selector */}
      <div className="bg-surface-800 rounded-xl border border-surface-700 p-4">
        <label className="text-sm text-slate-400 block mb-2">Select item to analyze</label>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500 pointer-events-none" />
          <input
            value={selectedItem ? `${selectedItem.sku} — ${selectedItem.name}` : search}
            onFocus={() => { setShowDropdown(true); if (selectedItem) { setSearch(""); setSelectedItem(null); } }}
            onChange={(e) => { setSearch(e.target.value); setShowDropdown(true); setSelectedItem(null); }}
            onBlur={() => setTimeout(() => setShowDropdown(false), 150)}
            placeholder="Search by SKU or name…"
            className="w-full pl-9 pr-4 py-2 bg-surface-700 border border-surface-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-brand-500 text-sm"
          />
          {showDropdown && items.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-surface-700 border border-surface-600 rounded-lg shadow-xl z-20 overflow-hidden">
              {items.map((item) => (
                <button
                  key={item.id}
                  onMouseDown={() => { setSelectedItem(item); setShowDropdown(false); }}
                  className="w-full px-4 py-2.5 text-left hover:bg-surface-600 transition-colors flex items-center justify-between gap-4"
                >
                  <div>
                    <span className="text-white text-sm font-medium">{item.name}</span>
                    <span className="text-slate-500 text-xs ml-2 font-mono">{item.sku}</span>
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
            <div className="bg-surface-800 rounded-xl border border-surface-700 p-6">
              <p className="text-slate-400 text-sm">Daily Consumption Rate</p>
              <p className="text-3xl font-bold text-white mt-1">
                {usage?.daily_consumption_rate?.toFixed(2) ?? "—"}
              </p>
              <p className="text-slate-500 text-xs mt-1">{selectedItem.unit}/day (30d avg)</p>
            </div>

            <div className="bg-surface-800 rounded-xl border border-surface-700 p-6">
              <p className="text-slate-400 text-sm">Predicted Depletion</p>
              <p
                className={`text-3xl font-bold mt-1 ${
                  depletion?.predicted_days_left != null && depletion.predicted_days_left < 7
                    ? "text-red-400"
                    : "text-emerald-400"
                }`}
              >
                {depletion?.predicted_days_left != null
                  ? `${depletion.predicted_days_left.toFixed(1)} days`
                  : "—"}
              </p>
              <p className="text-slate-500 text-xs mt-1">At current consumption rate</p>
            </div>

            <div className="bg-surface-800 rounded-xl border border-surface-700 p-6">
              <p className="text-slate-400 text-sm">Usage Anomaly</p>
              {anomaly ? (
                <>
                  <p className={`text-3xl font-bold mt-1 ${anomaly.is_anomaly ? "text-red-400" : "text-emerald-400"}`}>
                    {anomaly.is_anomaly ? "SPIKE" : "Normal"}
                  </p>
                  <p className="text-slate-500 text-xs mt-1">7d/30d ratio: {anomaly.ratio}x</p>
                </>
              ) : (
                <p className="text-3xl font-bold text-slate-600 mt-1">—</p>
              )}
            </div>
          </div>

          {/* EMA chart */}
          {emaData.length > 0 && (
            <div className="bg-surface-800 rounded-xl border border-surface-700 p-6">
              <h2 className="font-semibold text-white mb-4">
                Exponential Moving Average — 7-Day Consumption Trend
              </h2>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={emaData}>
                  <defs>
                    <linearGradient id="emaGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#1e293b",
                      border: "1px solid #334155",
                      borderRadius: "8px",
                    }}
                    labelStyle={{ color: "#e2e8f0" }}
                    itemStyle={{ color: "#94a3b8" }}
                  />
                  <Area
                    type="monotone"
                    dataKey="ema"
                    stroke="#3b82f6"
                    fill="url(#emaGrad)"
                    strokeWidth={2}
                    name="EMA (units/day)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}

          {emaData.length === 0 && usage && (
            <div className="bg-surface-800 rounded-xl border border-surface-700 p-8 text-center">
              <p className="text-slate-500 text-sm">
                Not enough transaction history to plot a trend for this item.
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
