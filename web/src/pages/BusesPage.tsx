import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Bus } from "lucide-react";
import toast from "react-hot-toast";
import { busService, warehouseService } from "@/services/inventoryService";
import { extractError as getError } from "@/services/api";
import { fmtNumber } from "@/utils/format";
import { useTranslation } from "react-i18next";
import { PageHeader } from "@/components/ui/PageHeader";
import { Field } from "@/components/ui/Field";
import { Modal } from "@/components/ui/Modal";
import { useDialog } from "@/hooks/useDialog";

// ── Primitives ────────────────────────────────────────────────────────────────

const inputCls =
  "w-full bg-white border border-surface-600 rounded-lg px-3 py-2 text-ink placeholder-slate-400 focus:outline-none focus:border-brand-500 text-sm";

const STATUS_COLORS: Record<string, string> = {
  ACTIVE: "bg-emerald-500/15 text-emerald-400",
  MAINTENANCE: "bg-amber-500/15 text-amber-400",
  OUT_OF_SERVICE: "bg-red-500/15 text-red-400",
  DECOMMISSIONED: "bg-slate-500/15 text-slate-400",
};

const STATUS_LABELS: Record<string, string> = {
  ACTIVE: "Active",
  MAINTENANCE: "In Maintenance",
  OUT_OF_SERVICE: "Out of Service",
  DECOMMISSIONED: "Decommissioned",
};

// ── Create Bus Modal ──────────────────────────────────────────────────────────

function CreateBusModal({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient();
  const [form, setForm] = useState({
    fleet_number: "",
    license_plate: "",
    make: "",
    model: "",
    year: new Date().getFullYear().toString(),
    vin: "",
    mileage_km: "0",
    depot_id: "",
    status: "ACTIVE",
  });

  const { data: warehouses = [] } = useQuery({
    queryKey: ["warehouses"],
    queryFn: () => warehouseService.listWarehouses(true),
  });

  const set =
    (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
      setForm((f) => ({ ...f, [k]: e.target.value }));

  const mutation = useMutation({
    mutationFn: () =>
      busService.createBus({
        fleet_number: form.fleet_number,
        license_plate: form.license_plate,
        make: form.make,
        model: form.model,
        year: parseInt(form.year),
        vin: form.vin || undefined,
        mileage_km: parseInt(form.mileage_km) || 0,
        depot_id: form.depot_id || undefined,
        status: form.status,
      }),
    onSuccess: () => {
      toast.success(`Bus "${form.fleet_number}" added to fleet`);
      qc.invalidateQueries({ queryKey: ["buses"] });
      onClose();
    },
    onError: (err) => toast.error(getError(err)),
  });

  const valid =
    form.fleet_number.trim() &&
    form.license_plate.trim() &&
    form.make.trim() &&
    form.model.trim() &&
    parseInt(form.year) > 1990;

  return (
    <Modal size="lg" title="Add Bus to Fleet" onClose={onClose}>
      <div className="space-y-3 max-h-[65vh] overflow-y-auto pe-1">
        <div className="grid grid-cols-2 gap-3">
          <Field label="Fleet Number *">
            <input value={form.fleet_number} onChange={set("fleet_number")} placeholder="BUS-001" className={inputCls} />
          </Field>
          <Field label="License Plate *">
            <input value={form.license_plate} onChange={set("license_plate")} placeholder="12-345-67" className={inputCls} />
          </Field>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Make *">
            <input value={form.make} onChange={set("make")} placeholder="Mercedes" className={inputCls} />
          </Field>
          <Field label="Model *">
            <input value={form.model} onChange={set("model")} placeholder="Citaro" className={inputCls} />
          </Field>
        </div>
        <div className="grid grid-cols-3 gap-3">
          <Field label="Year *">
            <input type="number" value={form.year} onChange={set("year")} min="1990" max="2030" className={inputCls} />
          </Field>
          <Field label="Mileage (km)">
            <input type="number" value={form.mileage_km} onChange={set("mileage_km")} min="0" className={inputCls} />
          </Field>
          <Field label="Status">
            <select value={form.status} onChange={set("status")} className={inputCls}>
              <option value="ACTIVE">Active</option>
              <option value="MAINTENANCE">In Maintenance</option>
              <option value="OUT_OF_SERVICE">Out of Service</option>
            </select>
          </Field>
        </div>
        <Field label="VIN (optional)">
          <input value={form.vin} onChange={set("vin")} placeholder="1HGBH41JXMN109186" className={inputCls} />
        </Field>
        <Field label="Home Depot / Warehouse">
          <select value={form.depot_id} onChange={set("depot_id")} className={inputCls}>
            <option value="">None</option>
            {warehouses.map((w) => (
              <option key={w.id} value={w.id}>{w.name} ({w.code})</option>
            ))}
          </select>
        </Field>
      </div>
      <div className="flex gap-3 mt-6">
        <button onClick={onClose}
          className="flex-1 px-4 py-2 bg-surface-700 hover:bg-surface-600 text-slate-300 rounded-lg text-sm transition-colors">
          Cancel
        </button>
        <button onClick={() => mutation.mutate()} disabled={mutation.isPending || !valid}
          className="flex-1 px-4 py-2 btn-primary text-sm font-medium transition-colors">
          {mutation.isPending ? "Adding…" : "Add Bus"}
        </button>
      </div>
    </Modal>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export function BusesPage() {
  const qc = useQueryClient();
  const { t } = useTranslation();
  const [showCreate, setShowCreate] = useState(false);
  const [pendingBusId, setPendingBusId] = useState<string | null>(null);

  const { data: buses = [], isLoading } = useQuery({
    queryKey: ["buses"],
    queryFn: () => busService.listBuses(),
    refetchInterval: 60_000,
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      busService.updateBus(id, { status }),
    onSuccess: (_, vars) => {
      toast.success(vars.status === "ACTIVE" ? "Bus set to Active" : "Bus set to In Maintenance");
      qc.invalidateQueries({ queryKey: ["buses"] });
      setPendingBusId(null);
    },
    onError: (err) => {
      toast.error(getError(err));
      setPendingBusId(null);
    },
  });

  return (
    <div className="space-y-4">
      {showCreate && <CreateBusModal onClose={() => setShowCreate(false)} />}

      <PageHeader
        title={<>{t("buses.title")}</>}
        subtitle={<>{buses.length} {t("buses.title").toLowerCase()}</>}
        actions={
          <>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2 btn-primary text-sm font-medium transition-colors"
        >
          <Plus className="h-4 w-4" />
          {t("buses.addBus")}
        </button>
          </>
        }
      />

      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="data-table w-full text-sm">
            <thead>
              <tr className="border-b border-surface-700 text-slate-400 text-xs uppercase tracking-wider">
                <th className="px-4 py-3 text-start">{t("buses.fleetNumber")}</th>
                <th className="px-4 py-3 text-start">{t("buses.model")}</th>
                <th className="px-4 py-3 text-center">{t("buses.year")}</th>
                <th className="px-4 py-3 text-start">{t("buses.plateNumber")}</th>
                <th className="px-4 py-3 text-end">{t("buses.mileage")}</th>
                <th className="px-4 py-3 text-center">{t("buses.status")}</th>
                <th className="px-4 py-3 text-end">{t("common.actions")}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-700">
              {isLoading ? (
                Array.from({ length: 4 }).map((_, i) => (
                  <tr key={i}>
                    {Array.from({ length: 7 }).map((_, j) => (
                      <td key={j} className="px-4 py-3">
                        <div className="h-4 bg-surface-700 rounded animate-pulse" />
                      </td>
                    ))}
                  </tr>
                ))
              ) : buses.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-16 text-center">
                    <Bus className="h-10 w-10 text-slate-400 mx-auto mb-2" />
                    <p className="text-slate-400">{t("buses.noBuses")}</p>
                  </td>
                </tr>
              ) : (
                buses.map((bus) => (
                  <tr key={bus.id} className="hover:bg-surface-700/50 transition-colors">
                    <td className="px-4 py-3 font-mono text-ink font-semibold text-xs">{bus.fleet_number}</td>
                    <td className="px-4 py-3">
                      <p className="text-ink font-medium">{bus.make} {bus.model}</p>
                    </td>
                    <td className="px-4 py-3 text-center text-slate-400">{bus.year}</td>
                    <td className="px-4 py-3 font-mono text-slate-300 text-xs">{bus.license_plate}</td>
                    <td className="px-4 py-3 text-end text-slate-400 tabular-nums">
                      {fmtNumber(bus.mileage_km)} km
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[bus.status] ?? "bg-slate-500/15 text-slate-400"}`}>
                        {STATUS_LABELS[bus.status] ?? bus.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-end">
                      {(bus.status === "ACTIVE" || bus.status === "MAINTENANCE") && (
                        <button
                          onClick={() => {
                            setPendingBusId(bus.id);
                            toggleMutation.mutate({
                              id: bus.id,
                              status: bus.status === "ACTIVE" ? "MAINTENANCE" : "ACTIVE",
                            });
                          }}
                          disabled={pendingBusId === bus.id}
                          className={`px-2.5 py-1 rounded text-xs font-medium transition-colors disabled:opacity-50 ${
                            bus.status === "ACTIVE"
                              ? "bg-amber-500/10 text-amber-400 hover:bg-amber-500/20"
                              : "bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20"
                          }`}
                        >
                          {pendingBusId === bus.id ? "…" : bus.status === "ACTIVE" ? "→ Maintenance" : "→ Active"}
                        </button>
                      )}
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
