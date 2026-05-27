import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ArrowDownCircle, ArrowUpCircle, ArrowLeftRight, RotateCcw } from "lucide-react";
import { inventoryService } from "@/services/inventoryService";
import { useTranslation } from "react-i18next";

const TYPE_CONFIG: Record<string, { label: string; cls: string; Icon: React.ElementType }> = {
  ISSUE: { label: "Issue", cls: "bg-red-500/15 text-red-400", Icon: ArrowDownCircle },
  RESTOCK: { label: "Restock", cls: "bg-emerald-500/15 text-emerald-400", Icon: ArrowUpCircle },
  TRANSFER: { label: "Transfer", cls: "bg-blue-500/15 text-blue-400", Icon: ArrowLeftRight },
  ROLLBACK: { label: "Rollback", cls: "bg-amber-500/15 text-amber-400", Icon: RotateCcw },
};

function TypeBadge({ type }: { type: string }) {
  const cfg = TYPE_CONFIG[type] ?? { label: type, cls: "bg-slate-500/15 text-slate-400", Icon: ArrowLeftRight };
  const { label, cls, Icon } = cfg;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${cls}`}>
      <Icon className="h-3 w-3" />
      {label}
    </span>
  );
}

export function TransactionsPage() {
  const { t } = useTranslation();
  const [typeFilter, setTypeFilter] = useState("");
  const [page, setPage] = useState(0);
  const limit = 50;

  const { data, isLoading } = useQuery({
    queryKey: ["transactions", typeFilter, page],
    queryFn: () => inventoryService.listTransactions({ offset: page * limit, limit }),
    refetchInterval: 30_000,
  });

  const allTxns = data?.transactions ?? [];
  const filtered = typeFilter ? allTxns.filter((t: any) => t.type === typeFilter) : allTxns;
  const paged = filtered;

  function fmt(iso: string | null) {
    if (!iso) return "—";
    return new Date(iso).toLocaleString("en-GB", {
      day: "2-digit", month: "short", year: "numeric",
      hour: "2-digit", minute: "2-digit",
    });
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">{t("transactions.title")}</h1>
          <p className="text-slate-400 text-sm mt-1">{filtered.length} {t("transactions.title").toLowerCase()}</p>
        </div>
        <select
          value={typeFilter}
          onChange={(e) => { setTypeFilter(e.target.value); setPage(0); }}
          className="bg-surface-700 border border-surface-600 rounded-lg px-3 py-2 text-slate-300 text-sm focus:outline-none focus:border-brand-500"
        >
          <option value="">{t("common.all")}</option>
          <option value="ISSUE">{t("transactions.issue")}</option>
          <option value="RESTOCK">{t("transactions.restock")}</option>
          <option value="TRANSFER">{t("transactions.transfer")}</option>
          <option value="ROLLBACK">{t("transactions.adjustment")}</option>
        </select>
      </div>

      <div className="bg-surface-800 rounded-xl border border-surface-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-700 text-slate-400 text-xs uppercase tracking-wider">
                <th className="px-4 py-3 text-left">Type</th>
                <th className="px-4 py-3 text-left">Item</th>
                <th className="px-4 py-3 text-right">Qty Δ</th>
                <th className="px-4 py-3 text-right">Before</th>
                <th className="px-4 py-3 text-right">After</th>
                <th className="px-4 py-3 text-left">Date</th>
                <th className="px-4 py-3 text-left">Notes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-700">
              {isLoading ? (
                Array.from({ length: 8 }).map((_, i) => (
                  <tr key={i}>
                    {Array.from({ length: 7 }).map((_, j) => (
                      <td key={j} className="px-4 py-3">
                        <div className="h-4 bg-surface-700 rounded animate-pulse" />
                      </td>
                    ))}
                  </tr>
                ))
              ) : paged.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-16 text-center text-slate-500">
                    No transactions yet.
                  </td>
                </tr>
              ) : (
                paged.map((t: any) => (
                  <tr key={t.id} className="hover:bg-surface-700/50 transition-colors">
                    <td className="px-4 py-3">
                      <TypeBadge type={t.type} />
                    </td>
                    <td className="px-4 py-3">
                      {t.item_name ? (
                        <div>
                          <p className="text-white text-sm">{t.item_name}</p>
                          <p className="text-slate-500 text-xs font-mono">{t.item_sku}</p>
                        </div>
                      ) : (
                        <span className="text-slate-500 text-xs font-mono">{t.item_id ? t.item_id.slice(0, 8) + "…" : "—"}</span>
                      )}
                    </td>
                    <td className={`px-4 py-3 text-right tabular-nums font-medium ${t.quantity_delta > 0 ? "text-emerald-400" : "text-red-400"}`}>
                      {t.quantity_delta > 0 ? "+" : ""}{t.quantity_delta}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums text-slate-400">{t.quantity_before}</td>
                    <td className="px-4 py-3 text-right tabular-nums text-slate-400">{t.quantity_after}</td>
                    <td className="px-4 py-3 text-slate-400 text-xs whitespace-nowrap">{fmt(t.created_at)}</td>
                    <td className="px-4 py-3 text-slate-500 text-xs max-w-[200px] truncate">{t.notes || "—"}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {(page > 0 || allTxns.length === limit) && (
          <div className="px-4 py-3 border-t border-surface-700 flex items-center justify-between text-sm text-slate-400">
            <span>Page {page + 1}</span>
            <div className="flex gap-2">
              <button onClick={() => setPage((p) => Math.max(0, p - 1))} disabled={page === 0}
                className="px-3 py-1 bg-surface-700 hover:bg-surface-600 disabled:opacity-40 rounded text-slate-300 transition-colors">
                Previous
              </button>
              <button onClick={() => setPage((p) => p + 1)} disabled={allTxns.length < limit}
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
