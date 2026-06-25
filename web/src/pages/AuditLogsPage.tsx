import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ShieldCheck } from "lucide-react";
import { auditService } from "@/services/inventoryService";
import { useTranslation } from "react-i18next";

function fmt(iso: string | null) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("en-GB", {
    day: "2-digit", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit", second: "2-digit",
  });
}

export function AuditLogsPage() {
  const { t } = useTranslation();
  const [resourceType, setResourceType] = useState("");
  const [actionFilter, setActionFilter] = useState("");
  const [page, setPage] = useState(0);
  const limit = 50;

  const { data, isLoading } = useQuery({
    queryKey: ["audit", resourceType, actionFilter, page],
    queryFn: () =>
      auditService.listAuditLogs({
        resource_type: resourceType || undefined,
        action: actionFilter || undefined,
        offset: page * limit,
        limit,
      }),
    refetchInterval: 30_000,
  });

  const logs = data?.logs ?? [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-white">{t("audit.title")}</h1>
          <p className="text-slate-400 text-sm mt-1">Immutable record of all system actions</p>
        </div>
        <div className="flex gap-2">
          <input
            value={resourceType}
            onChange={(e) => { setResourceType(e.target.value); setPage(0); }}
            placeholder="Resource type…"
            className="bg-surface-700 border border-surface-600 rounded-lg px-3 py-2 text-slate-300 text-sm focus:outline-none focus:border-brand-500 w-40"
          />
          <input
            value={actionFilter}
            onChange={(e) => { setActionFilter(e.target.value); setPage(0); }}
            placeholder="Action…"
            className="bg-surface-700 border border-surface-600 rounded-lg px-3 py-2 text-slate-300 text-sm focus:outline-none focus:border-brand-500 w-40"
          />
        </div>
      </div>

      <div className="bg-surface-800 rounded-xl border border-surface-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-700 text-slate-400 text-xs uppercase tracking-wider">
                <th className="px-4 py-3 text-left">{t("audit.timestamp")}</th>
                <th className="px-4 py-3 text-left">{t("audit.user")}</th>
                <th className="px-4 py-3 text-left">{t("audit.action")}</th>
                <th className="px-4 py-3 text-left">{t("audit.resource")}</th>
                <th className="px-4 py-3 text-left">Resource ID</th>
                <th className="px-4 py-3 text-left">{t("transactions.notes")}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-700">
              {isLoading ? (
                Array.from({ length: 8 }).map((_, i) => (
                  <tr key={i}>
                    {Array.from({ length: 6 }).map((_, j) => (
                      <td key={j} className="px-4 py-3">
                        <div className="h-4 bg-surface-700 rounded animate-pulse" />
                      </td>
                    ))}
                  </tr>
                ))
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-16 text-center">
                    <ShieldCheck className="h-10 w-10 text-slate-600 mx-auto mb-2" />
                    <p className="text-slate-500">{t("audit.noLogs")}</p>
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id} className="hover:bg-surface-700/50 transition-colors">
                    <td className="px-4 py-3 text-slate-400 text-xs whitespace-nowrap">{fmt(log.created_at)}</td>
                    <td className="px-4 py-3 text-slate-300 text-xs">{log.username ?? log.user_id?.slice(0, 8) ?? "system"}</td>
                    <td className="px-4 py-3">
                      <span className="inline-block px-2 py-0.5 bg-brand-500/10 text-brand-400 rounded text-xs font-mono">
                        {log.action}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-400 text-xs font-mono">{log.resource_type}</td>
                    <td className="px-4 py-3 text-slate-500 text-xs font-mono">{log.resource_id ?? "—"}</td>
                    <td className="px-4 py-3 text-slate-500 text-xs max-w-[200px] truncate">{log.notes ?? "—"}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {logs.length === limit && (
          <div className="px-4 py-3 border-t border-surface-700 flex items-center justify-between text-sm text-slate-400">
            <span>Page {page + 1}</span>
            <div className="flex gap-2">
              <button onClick={() => setPage((p) => Math.max(0, p - 1))} disabled={page === 0}
                className="px-3 py-1 bg-surface-700 hover:bg-surface-600 disabled:opacity-40 rounded text-slate-300 transition-colors">
                Previous
              </button>
              <button onClick={() => setPage((p) => p + 1)} disabled={logs.length < limit}
                className="px-3 py-1 bg-surface-700 hover:bg-surface-600 disabled:opacity-40 rounded text-slate-300 transition-colors">
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
