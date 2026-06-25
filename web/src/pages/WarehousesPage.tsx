import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Plus, Warehouse, X, ToggleLeft, ToggleRight } from "lucide-react";
import toast from "react-hot-toast";
import { warehouseService } from "@/services/inventoryService";
import { extractError as getError } from "@/services/api";
import { useTranslation } from "react-i18next";

// ── Shared primitives ────────────────────────────────────────────────────────

function Modal({
  title,
  onClose,
  children,
}: {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-surface-800 rounded-xl border border-surface-700 p-6 w-full max-w-md shadow-2xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">{title}</h3>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-300 transition-colors">
            <X className="h-5 w-5" />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="text-sm text-slate-400 block mb-1">{label}</label>
      {children}
    </div>
  );
}

const inputCls =
  "w-full bg-surface-700 border border-surface-600 rounded-lg px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-brand-500 text-sm";

// ── Create Warehouse Modal ───────────────────────────────────────────────────

function CreateWarehouseModal({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient();
  const [form, setForm] = useState({
    name: "",
    code: "",
    city: "",
    country: "IL",
    address: "",
    phone: "",
    capacity_sqm: "",
  });

  const set =
    (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
      setForm((f) => ({ ...f, [k]: e.target.value }));

  const mutation = useMutation({
    mutationFn: () =>
      warehouseService.createWarehouse({
        name: form.name,
        code: form.code,
        city: form.city || undefined,
        country: form.country,
        address: form.address || undefined,
        phone: form.phone || undefined,
        capacity_sqm: form.capacity_sqm ? parseInt(form.capacity_sqm) : undefined,
      }),
    onSuccess: () => {
      toast.success(`Warehouse "${form.name}" created`);
      qc.invalidateQueries({ queryKey: ["warehouses"] });
      onClose();
    },
    onError: (err) => toast.error(getError(err)),
  });

  const valid = form.name.trim() && form.code.trim();

  return (
    <Modal title="Add Warehouse" onClose={onClose}>
      <div className="space-y-3 max-h-[60vh] overflow-y-auto pr-1">
        <div className="grid grid-cols-2 gap-3">
          <Field label="Name *">
            <input value={form.name} onChange={set("name")} placeholder="Main Depot" className={inputCls} />
          </Field>
          <Field label="Code *">
            <input
              value={form.code}
              onChange={set("code")}
              placeholder="WH-01"
              className={`${inputCls} uppercase`}
            />
          </Field>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <Field label="City">
            <input value={form.city} onChange={set("city")} placeholder="Tel Aviv" className={inputCls} />
          </Field>
          <Field label="Country">
            <input value={form.country} onChange={set("country")} placeholder="IL" className={inputCls} />
          </Field>
        </div>
        <Field label="Address">
          <input value={form.address} onChange={set("address")} placeholder="123 Depot St." className={inputCls} />
        </Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Phone">
            <input value={form.phone} onChange={set("phone")} placeholder="+972-3-..." className={inputCls} />
          </Field>
          <Field label="Capacity (m²)">
            <input
              type="number"
              value={form.capacity_sqm}
              onChange={set("capacity_sqm")}
              min="0"
              placeholder="500"
              className={inputCls}
            />
          </Field>
        </div>
      </div>
      <div className="flex gap-3 mt-6">
        <button
          onClick={onClose}
          className="flex-1 px-4 py-2 bg-surface-700 hover:bg-surface-600 text-slate-300 rounded-lg text-sm transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={() => mutation.mutate()}
          disabled={mutation.isPending || !valid}
          className="flex-1 px-4 py-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors"
        >
          {mutation.isPending ? "Creating…" : "Create"}
        </button>
      </div>
    </Modal>
  );
}

// ── Page ─────────────────────────────────────────────────────────────────────

type WarehouseRow = {
  id: string;
  name: string;
  code: string;
  city?: string;
  country: string;
  address?: string;
  phone?: string;
  capacity_sqm?: number;
  is_active: boolean;
};

export function WarehousesPage() {
  const qc = useQueryClient();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [showCreate, setShowCreate] = useState(false);

  const { data: warehouses = [], isLoading } = useQuery({
    queryKey: ["warehouses"],
    queryFn: () => warehouseService.listWarehouses(false),
    refetchInterval: 60_000,
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      warehouseService.updateWarehouse(id, { is_active }),
    onSuccess: (_, vars) => {
      toast.success(vars.is_active ? t("warehouses.activated") : t("warehouses.deactivated"));
      qc.invalidateQueries({ queryKey: ["warehouses"] });
    },
    onError: (err) => toast.error(getError(err)),
  });

  return (
    <div className="space-y-4">
      {showCreate && <CreateWarehouseModal onClose={() => setShowCreate(false)} />}

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">{t("warehouses.title")}</h1>
          <p className="text-slate-400 text-sm mt-1">{warehouses.length} {t("warehouses.title").toLowerCase()}</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg text-sm font-medium transition-colors"
        >
          <Plus className="h-4 w-4" />
          {t("warehouses.addWarehouse")}
        </button>
      </div>

      <div className="bg-surface-800 rounded-xl border border-surface-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-700 text-slate-400 text-xs uppercase tracking-wider">
                <th className="px-4 py-3 text-left">{t("warehouses.code")}</th>
                <th className="px-4 py-3 text-left">{t("warehouses.name")}</th>
                <th className="px-4 py-3 text-left">{t("warehouses.city")}</th>
                <th className="px-4 py-3 text-left">{t("warehouses.country")}</th>
                <th className="px-4 py-3 text-right">{t("warehouses.capacity")}</th>
                <th className="px-4 py-3 text-center">{t("warehouses.status")}</th>
                <th className="px-4 py-3 text-right">{t("warehouses.actions")}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-700">
              {isLoading ? (
                Array.from({ length: 3 }).map((_, i) => (
                  <tr key={i}>
                    {Array.from({ length: 7 }).map((_, j) => (
                      <td key={j} className="px-4 py-3">
                        <div className="h-4 bg-surface-700 rounded animate-pulse" />
                      </td>
                    ))}
                  </tr>
                ))
              ) : warehouses.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-12 text-center">
                    <Warehouse className="h-10 w-10 text-slate-600 mx-auto mb-2" />
                    <p className="text-slate-500">{t("warehouses.noWarehouses")}</p>
                  </td>
                </tr>
              ) : (
                (warehouses as WarehouseRow[]).map((wh) => (
                  <tr key={wh.id}
                    className="hover:bg-surface-700/50 transition-colors cursor-pointer"
                    onClick={(e) => { if ((e.target as HTMLElement).closest("button")) return; navigate(`/warehouses/${wh.id}`); }}
                  >
                    <td className="px-4 py-3 font-mono text-slate-300 text-xs font-semibold">{wh.code}</td>
                    <td className="px-4 py-3 text-white font-medium">{wh.name}</td>
                    <td className="px-4 py-3 text-slate-400">{wh.city || "—"}</td>
                    <td className="px-4 py-3 text-slate-400">{wh.country}</td>
                    <td className="px-4 py-3 text-right text-slate-400 tabular-nums">
                      {wh.capacity_sqm != null ? wh.capacity_sqm.toLocaleString() : "—"}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                          wh.is_active
                            ? "bg-emerald-500/15 text-emerald-400"
                            : "bg-slate-500/15 text-slate-400"
                        }`}
                      >
                        {wh.is_active ? t("common.active") : t("common.inactive")}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() =>
                          toggleMutation.mutate({ id: wh.id, is_active: !wh.is_active })
                        }
                        disabled={toggleMutation.isPending}
                        className={`p-1.5 rounded transition-colors ${
                          wh.is_active
                            ? "text-emerald-400 hover:text-slate-400 hover:bg-surface-600"
                            : "text-slate-400 hover:text-emerald-400 hover:bg-emerald-500/10"
                        }`}
                        title={wh.is_active ? "Deactivate" : "Activate"}
                      >
                        {wh.is_active ? (
                          <ToggleRight className="h-5 w-5" />
                        ) : (
                          <ToggleLeft className="h-5 w-5" />
                        )}
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
