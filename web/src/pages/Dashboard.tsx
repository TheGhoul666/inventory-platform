/**
 * Operations Dashboard — stock health, run-out forecast, alerts and latest movements.
 */
import React from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { RefreshCw } from "lucide-react";
import { analyticsService, alertService } from "@/services/inventoryService";
import { AlertBadge } from "@/components/ui/AlertBadge";
import { useTranslation } from "react-i18next";
import { useAuthStore } from "@/store/authStore";
import { fmtDateTime } from "@/utils/format";
import { cn } from "@/utils/cn";
import type { StockLevel } from "@/utils/analytics";
import type { Alert } from "@/types";

const STATUS_STYLE = {
  critical: { bar: "bg-clay", pill: "bg-[#fbd9c8] text-red-400", num: "text-clay" },
  low: { bar: "bg-[#c79a14]", pill: "bg-[#fdeec2] text-amber-400", num: "text-amber-400" },
  ok: { bar: "bg-brand-600", pill: "bg-[#dcebd6] text-emerald-400", num: "text-emerald-400" },
} as const;

function greetingKey(): "greetingMorning" | "greetingAfternoon" | "greetingEvening" {
  const h = new Date().getHours();
  return h < 12 ? "greetingMorning" : h < 18 ? "greetingAfternoon" : "greetingEvening";
}

function KpiCard({ tone, title, value, sub }: { tone: string; title: string; value: number | string; sub: string }) {
  return (
    <div className={cn("rounded-2xl p-5", tone)}>
      <p className="text-sm font-bold">{title}</p>
      <p className="mt-1 text-5xl font-extrabold leading-none tabular-nums">{value}</p>
      <p className="mt-2 text-sm">{sub}</p>
    </div>
  );
}

function StockRow({ level }: { level: StockLevel }) {
  const { t } = useTranslation();
  const st = STATUS_STYLE[level.status];
  const statusLabel = t(`dashboard.status${level.status === "ok" ? "Ok" : level.status === "low" ? "Low" : "Critical"}`);
  const pct = Math.min(100, (level.quantity / level.scale) * 100);
  const forecast =
    level.daysLeft === null
      ? t("dashboard.noUsage")
      : level.status === "critical"
      ? t("dashboard.daysLeftSoon", { n: Math.max(1, Math.round(level.daysLeft)) })
      : t("dashboard.daysLeft", { n: Math.max(1, Math.round(level.daysLeft)) });
  return (
    <li>
      <div className="mb-2 flex items-center justify-between gap-3">
        <div className="min-w-0">
          <span className="font-bold text-ink">{level.name}</span>{" "}
          <span className="text-sm text-slate-400">· {level.sku}</span>
        </div>
        <div className="flex shrink-0 items-center gap-3">
          <span className={cn("rounded-full px-3 py-0.5 text-sm font-bold", st.pill)}>{forecast}</span>
          <span className={cn("text-lg font-extrabold tabular-nums", st.num)}>{level.quantity}</span>
        </div>
      </div>
      <div
        role="img"
        aria-label={t("dashboard.levelAria", { qty: level.quantity, scale: Math.round(level.scale), status: statusLabel })}
        className="relative h-3.5 rounded-full bg-surface-700"
      >
        <div className={cn("h-full rounded-full", st.bar)} style={{ width: `${pct}%` }} />
        <span className="absolute -inset-y-[3px] w-0.5 bg-clay" style={{ insetInlineStart: `${(level.critical / level.scale) * 100}%` }} />
        <span className="absolute -inset-y-[3px] w-0.5 bg-[#c79a14]" style={{ insetInlineStart: `${(level.low / level.scale) * 100}%` }} />
      </div>
    </li>
  );
}

export function Dashboard() {
  const { t } = useTranslation();
  const user = useAuthStore((s) => s.user);
  const firstName = ((user?.user_metadata?.full_name as string | undefined) ?? user?.email ?? "").split(/[ @]/)[0];

  const { data: overview, isLoading, refetch } = useQuery({
    queryKey: ["analytics", "dashboard-overview"],
    queryFn: () => analyticsService.getDashboardOverview(),
    refetchInterval: 60_000,
  });

  const { data: alertsData } = useQuery({
    queryKey: ["alerts", "dashboard"],
    queryFn: () => alertService.listAlerts({ status: "OPEN", limit: 4 }),
    refetchInterval: 30_000,
  });

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center text-slate-400">
        <RefreshCw className="me-3 h-8 w-8 animate-spin" />
        {t("dashboard.loading")}
      </div>
    );
  }

  const counts = overview?.counts ?? { total: 0, critical: 0, low: 0, ok: 0 };
  const levels = overview?.levels ?? [];
  const recent = overview?.recent ?? [];
  const openAlerts: Alert[] = alertsData?.alerts ?? [];
  const attention = counts.critical + counts.low;
  const donutCrit = counts.total ? (counts.ok / counts.total) * 100 : 0;
  const donutLow = counts.total ? donutCrit + (counts.low / counts.total) * 100 : 0;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl text-ink">
            {t(`dashboard.${greetingKey()}`)}
            {firstName ? `, ${firstName}` : ""}
          </h1>
          <p className="mt-1 text-slate-400">
            {attention > 0 ? t("dashboard.attention", { count: attention }) : t("dashboard.allGood")}
          </p>
        </div>
        <button onClick={() => refetch()} className="btn-secondary flex items-center gap-2 px-4 py-2 text-sm">
          <RefreshCw className="h-4 w-4" aria-hidden="true" />
          {t("dashboard.refresh")}
        </button>
      </div>

      <section aria-label={t("dashboard.title")} className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <KpiCard tone="bg-[#fbd9c8] text-[#7a2d0f]" title={t("dashboard.kpiCritical")} value={counts.critical} sub={t("dashboard.kpiCriticalSub")} />
        <KpiCard tone="bg-[#fdeec2] text-[#6b4e00]" title={t("dashboard.kpiLow")} value={counts.low} sub={t("dashboard.kpiLowSub")} />
        <KpiCard tone="bg-[#dcebd6] text-[#2f5a3a]" title={t("dashboard.kpiOk")} value={counts.ok} sub={t("dashboard.kpiOutOf", { total: counts.total })} />
        <KpiCard tone="bg-[#d7e9ef] text-[#1d4d5c]" title={t("dashboard.openAlerts")} value={openAlerts.length} sub={t("dashboard.kpiAlertsSub")} />
      </section>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-[3fr_2fr]">
        <section aria-labelledby="levels-title" className="card p-6">
          <div className="mb-1 flex items-baseline justify-between">
            <h2 id="levels-title" className="text-xl text-ink">{t("dashboard.levelsTitle")}</h2>
            <Link to="/inventory" className="text-sm font-semibold text-brand-300 underline underline-offset-2">{t("dashboard.allInventory")}</Link>
          </div>
          <p className="mb-5 text-xs text-slate-400">{t("dashboard.legend")} {t("dashboard.forecastNote")}</p>
          {levels.length === 0 ? (
            <p className="py-8 text-center text-slate-400">{t("dashboard.noItems")}</p>
          ) : (
            <ul className="space-y-5">
              {levels.map((l) => (
                <StockRow key={l.id} level={l} />
              ))}
            </ul>
          )}
        </section>

        <div className="space-y-5">
          <section aria-labelledby="alerts-title" className="card p-5">
            <h2 id="alerts-title" className="mb-3 text-lg text-ink">{t("dashboard.openAlertsTitle")}</h2>
            {openAlerts.length === 0 ? (
              <p className="py-3 text-slate-400">{t("dashboard.noAlerts")}</p>
            ) : (
              <ul className="space-y-2.5">
                {openAlerts.map((a) => (
                  <li key={a.id} className="flex items-start gap-3 rounded-xl bg-surface-900 px-3.5 py-3">
                    <AlertBadge severity={a.severity} />
                    <div className="min-w-0 text-sm leading-snug">
                      <p className="truncate font-bold text-ink">{a.title}</p>
                      <p className="text-slate-400">{fmtDateTime(a.created_at)}</p>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section aria-labelledby="status-title" className="card flex items-center gap-5 p-5">
            <div
              role="img"
              aria-label={`${t("dashboard.statusOk")} ${counts.ok}, ${t("dashboard.statusLow")} ${counts.low}, ${t("dashboard.statusCritical")} ${counts.critical}`}
              className="flex h-24 w-24 shrink-0 items-center justify-center rounded-full"
              style={{
                background: counts.total
                  ? `conic-gradient(#3f6b4a 0 ${donutCrit}%, #c79a14 0 ${donutLow}%, #b4421d 0 100%)`
                  : "#efe6d3",
              }}
            >
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-surface-800 text-xl font-extrabold">{counts.total}</div>
            </div>
            <div>
              <h2 id="status-title" className="mb-2 text-lg text-ink">{t("dashboard.statusBreakdown")}</h2>
              <ul className="space-y-1 text-sm">
                <li><span className="inline-block h-2.5 w-2.5 rounded-full bg-brand-600" aria-hidden="true" /> {t("dashboard.statusOk")} · {counts.ok}</li>
                <li><span className="inline-block h-2.5 w-2.5 rounded-full bg-[#c79a14]" aria-hidden="true" /> {t("dashboard.statusLow")} · {counts.low}</li>
                <li><span className="inline-block h-2.5 w-2.5 rounded-full bg-clay" aria-hidden="true" /> {t("dashboard.statusCritical")} · {counts.critical}</li>
              </ul>
            </div>
          </section>

          <section aria-labelledby="mv-title" className="card p-5">
            <h2 id="mv-title" className="mb-2 text-lg text-ink">{t("dashboard.recentMovements")}</h2>
            {recent.length === 0 ? (
              <p className="py-2 text-sm text-slate-400">{t("dashboard.noMovements")}</p>
            ) : (
              <ul className="divide-y divide-surface-700 text-sm">
                {recent.map((m) => (
                  <li key={m.id} className="flex items-center justify-between gap-3 py-2">
                    <span>
                      {t(`dashboard.mv.${m.transaction_type}`, { defaultValue: m.transaction_type })} · {m.item?.name ?? "—"} · {Math.abs(Number(m.quantity_delta))} {m.item?.unit ?? ""}
                    </span>
                    <span className="shrink-0 text-slate-400">{fmtDateTime(m.created_at)}</span>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}
