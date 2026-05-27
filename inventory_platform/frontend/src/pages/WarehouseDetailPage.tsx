import React, { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft, Search, ArrowLeftRight, Bus, X, Package, Trash2, ArrowDown,
} from "lucide-react";
import toast from "react-hot-toast";
import { inventoryService, warehouseService, busService } from "@/services/inventoryService";
import { extractError as getError } from "@/services/api";
import { StockBadge } from "@/components/ui/StockBadge";
import { useTranslation } from "react-i18next";
import type { InventoryItem } from "@/types";

// ── Shared primitives ─────────────────────────────────────────────────────────

function Modal({
  title,
  onClose,
  children,
}: {
  title: React.ReactNode;
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

function ModalActions({
  onClose, onConfirm, pending, label, confirmClass = "bg-brand-600 hover:bg-brand-700 text-white",
}: {
  onClose: () => void; onConfirm: () => void; pending: boolean;
  label: string; confirmClass?: string;
}) {
  return (
    <div className="flex gap-3 mt-6">
      <button onClick={onClose} className="flex-1 px-4 py-2 bg-surface-700 hover:bg-surface-600 text-slate-300 rounded-lg text-sm transition-colors">
        Cancel
      </button>
      <button onClick={onConfirm} disabled={pending}
        className={`flex-1 px-4 py-2 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-sm font-medium transition-colors ${confirmClass}`}>
        {pending ? "Processing…" : label}
      </button>
    </div>
  );
}

// ── Transfer Modal ────────────────────────────────────────────────────────────

function TransferModal({ item, onClose }: { item: InventoryItem; onClose: () => void }) {
  const qc = useQueryClient();
  const [destWarehouseId, setDestWarehouseId] = useState("");
  const [search, setSearch] = useState("");
  const [destItem, setDestItem] = useState<InventoryItem | null>(null);
  const [qty, setQty] = useState("1");
  const [notes, setNotes] = useState("");

  const { data: warehouses = [] } = useQuery({
    queryKey: ["warehouses", "active"],
    queryFn: () => warehouseService.listWarehouses(true),
  });

  const { data: destItemsData } = useQuery({
    queryKey: ["inventory", "transfer-search", destWarehouseId, search],
    queryFn: () => inventoryService.listItems({ warehouse_id: destWarehouseId, search: search || undefined, limit: 20 }),
    enabled: !!destWarehouseId && !destItem,
  });

  const destItems = destItemsData?.items ?? [];

  const mutation = useMutation({
    mutationFn: () => inventoryService.transferItem({
      source_item_id: item.id,
      dest_item_id: destItem!.id,
      source_warehouse_id: item.warehouse_id,
      dest_warehouse_id: destWarehouseId,
      quantity: parseFloat(qty),
      notes: notes || undefined,
    }),
    onSuccess: () => {
      toast.success(`Transferred ${qty} ${item.unit} of ${item.name}`);
      qc.invalidateQueries({ queryKey: ["inventory"] });
      onClose();
    },
    onError: (err) => toast.error(getError(err)),
  });

  const valid = !!destItem && parseFloat(qty) > 0 && parseFloat(qty) <= item.available_quantity;

  return (
    <Modal title={<>Transfer: <span className="text-blue-400">{item.name}</span></>} onClose={onClose}>
      <div className="space-y-4">
        <div className="bg-surface-700 rounded-lg p-3 text-sm">
          <p className="text-slate-400 text-xs mb-0.5">Source item</p>
          <p className="text-white font-medium">{item.name}</p>
          <p className="text-slate-500 text-xs font-mono">Available: {item.available_quantity} {item.unit}</p>
        </div>

        <Field label="Destination Warehouse">
          <select value={destWarehouseId}
            onChange={(e) => { setDestWarehouseId(e.target.value); setDestItem(null); setSearch(""); }}
            className={inputCls}>
            <option value="">Select warehouse…</option>
            {warehouses.filter((w) => w.id !== item.warehouse_id).map((w) => (
              <option key={w.id} value={w.id}>{w.name} ({w.code})</option>
            ))}
          </select>
        </Field>

        {destWarehouseId && (
          <Field label="Destination Item (must exist in that warehouse)">
            {destItem ? (
              <div className="flex items-center justify-between bg-surface-700 rounded-lg p-2.5">
                <div>
                  <p className="text-white text-sm font-medium">{destItem.name}</p>
                  <p className="text-slate-400 text-xs">{destItem.available_quantity} {destItem.unit} available</p>
                </div>
                <button onClick={() => setDestItem(null)} className="text-slate-500 hover:text-slate-300 transition-colors">
                  <X className="h-4 w-4" />
                </button>
              </div>
            ) : (
              <div>
                <input value={search} onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search by name or SKU…" className={inputCls} />
                {destItems.length > 0 && (
                  <div className="mt-1 bg-surface-700 border border-surface-600 rounded-lg overflow-hidden max-h-36 overflow-y-auto">
                    {destItems.map((di) => (
                      <button key={di.id} onClick={() => setDestItem(di)}
                        className="w-full text-left px-3 py-2 hover:bg-surface-600 text-sm flex items-center justify-between transition-colors">
                        <span className="text-white">{di.name}</span>
                        <span className="text-slate-400 text-xs tabular-nums">{di.available_quantity} {di.unit}</span>
                      </button>
                    ))}
                  </div>
                )}
                {destItems.length === 0 && search && (
                  <p className="text-slate-500 text-xs mt-1 px-1">No matching items in this warehouse</p>
                )}
              </div>
            )}
          </Field>
        )}

        <Field label={`Quantity (max: ${item.available_quantity} ${item.unit})`}>
          <input type="number" value={qty} onChange={(e) => setQty(e.target.value)}
            min="0.001" max={item.available_quantity} step="0.001" className={inputCls} />
        </Field>
        <Field label="Notes">
          <textarea value={notes} onChange={(e) => setNotes(e.target.value)}
            rows={2} className={`${inputCls} resize-none`} />
        </Field>
      </div>
      <ModalActions onClose={onClose} onConfirm={() => mutation.mutate()} pending={mutation.isPending}
        label="Transfer" confirmClass={`text-white ${valid ? "bg-blue-600 hover:bg-blue-700" : "bg-blue-600/50 cursor-not-allowed"}`} />
    </Modal>
  );
}

// ── Bus Assign Modal ──────────────────────────────────────────────────────────

function BusAssignModal({ item, onClose }: { item: InventoryItem; onClose: () => void }) {
  const qc = useQueryClient();
  const [busId, setBusId] = useState("");
  const [qty, setQty] = useState("1");
  const [notes, setNotes] = useState("");

  const { data: buses = [] } = useQuery({
    queryKey: ["buses"],
    queryFn: () => busService.listBuses(),
  });

  const mutation = useMutation({
    mutationFn: () => inventoryService.issueItem({
      item_id: item.id,
      quantity: parseFloat(qty),
      bus_id: busId,
      notes: notes || undefined,
    }),
    onSuccess: () => {
      const bus = buses.find((b) => b.id === busId);
      toast.success(`Assigned ${qty} ${item.unit} of ${item.name} to Bus ${bus?.fleet_number ?? busId}`);
      qc.invalidateQueries({ queryKey: ["inventory"] });
      onClose();
    },
    onError: (err) => toast.error(getError(err)),
  });

  const valid = !!busId && parseFloat(qty) > 0 && parseFloat(qty) <= item.available_quantity;

  return (
    <Modal title={<><Bus className="inline h-4 w-4 mr-1.5 text-amber-400" />Assign to Bus: <span className="text-amber-400">{item.name}</span></>} onClose={onClose}>
      <div className="space-y-4">
        <div className="bg-surface-700 rounded-lg p-3 text-sm">
          <p className="text-slate-400 text-xs mb-0.5">Part</p>
          <p className="text-white font-medium">{item.name}</p>
          <p className="text-slate-500 text-xs font-mono">{item.sku} · Available: {item.available_quantity} {item.unit}</p>
        </div>

        <Field label="Select Bus *">
          {buses.length === 0 ? (
            <p className="text-slate-500 text-sm py-2">No buses in the fleet yet. Add buses first.</p>
          ) : (
            <select value={busId} onChange={(e) => setBusId(e.target.value)}
              className={`${inputCls} text-amber-300`}>
              <option value="">Choose a bus…</option>
              {buses.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.fleet_number} — {b.make} {b.model} ({b.year})
                </option>
              ))}
            </select>
          )}
        </Field>

        <Field label={`Quantity (max: ${item.available_quantity} ${item.unit})`}>
          <input type="number" value={qty} onChange={(e) => setQty(e.target.value)}
            min="0.001" max={item.available_quantity} step="0.001" className={inputCls} />
        </Field>

        <Field label="Notes (optional)">
          <textarea value={notes} onChange={(e) => setNotes(e.target.value)}
            rows={2} placeholder="Maintenance job, fault code…"
            className={`${inputCls} resize-none`} />
        </Field>
      </div>
      <ModalActions onClose={onClose} onConfirm={() => mutation.mutate()} pending={mutation.isPending}
        label="Assign to Bus"
        confirmClass={`text-white ${valid ? "bg-amber-600 hover:bg-amber-700" : "bg-amber-600/50 cursor-not-allowed"}`} />
    </Modal>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export function WarehouseDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const { t } = useTranslation();
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(0);
  const limit = 50;

  const [transferTarget, setTransferTarget] = useState<InventoryItem | null>(null);
  const [busTarget, setBusTarget] = useState<InventoryItem | null>(null);
  const [writeOffTarget, setWriteOffTarget] = useState<InventoryItem | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<InventoryItem | null>(null);

  const writeOffMutation = useMutation({
    mutationFn: (item: InventoryItem) =>
      inventoryService.writeOffItem(item.id, item.available_quantity, "Write-off: dropped from warehouse"),
    onSuccess: () => {
      toast.success("Stock written off");
      qc.invalidateQueries({ queryKey: ["inventory"] });
      setWriteOffTarget(null);
    },
    onError: (err) => toast.error((err as Error).message),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => inventoryService.deleteItem(id),
    onSuccess: () => {
      toast.success("Item deleted");
      qc.invalidateQueries({ queryKey: ["inventory"] });
      setDeleteTarget(null);
    },
    onError: (err) => toast.error((err as Error).message),
  });

  const { data: warehouse, isLoading: whLoading } = useQuery({
    queryKey: ["warehouse", id],
    queryFn: () => warehouseService.getWarehouse(id!),
    enabled: !!id,
  });

  const { data, isLoading: itemsLoading } = useQuery({
    queryKey: ["inventory", "items", { warehouse_id: id, search, page }],
    queryFn: () => inventoryService.listItems({
      warehouse_id: id,
      search: search || undefined,
      offset: page * limit,
      limit,
    }),
    enabled: !!id,
    refetchInterval: 30_000,
  });

  const items = data?.items ?? [];
  const total = data?.total ?? 0;

  if (whLoading) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-400 text-sm">
        Loading warehouse…
      </div>
    );
  }

  if (!warehouse) {
    return (
      <div className="text-center py-20">
        <p className="text-slate-400">Warehouse not found.</p>
        <button onClick={() => navigate("/warehouses")} className="mt-3 text-brand-400 text-sm hover:underline">
          ← Back to Warehouses
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Modals */}
      {transferTarget && <TransferModal item={transferTarget} onClose={() => setTransferTarget(null)} />}
      {busTarget && <BusAssignModal item={busTarget} onClose={() => setBusTarget(null)} />}

      {writeOffTarget && (
        <Modal title="Write Off Stock" onClose={() => setWriteOffTarget(null)}>
          <p className="text-slate-300 text-sm mb-1">
            Drop all <span className="text-white font-semibold">{writeOffTarget.available_quantity} {writeOffTarget.unit}</span> of{" "}
            <span className="text-white font-semibold">{writeOffTarget.name}</span> from this warehouse?
          </p>
          <p className="text-slate-500 text-xs mb-6">Stock will be zeroed out. Recorded in the audit log.</p>
          <div className="flex gap-3 mt-2">
            <button onClick={() => setWriteOffTarget(null)} className="flex-1 px-4 py-2 bg-surface-700 hover:bg-surface-600 text-slate-300 rounded-lg text-sm transition-colors">Cancel</button>
            <button onClick={() => writeOffMutation.mutate(writeOffTarget)} disabled={writeOffMutation.isPending}
              className="flex-1 px-4 py-2 bg-amber-700 hover:bg-amber-800 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition-colors">
              {writeOffMutation.isPending ? "Processing…" : "Drop Stock"}
            </button>
          </div>
        </Modal>
      )}

      {deleteTarget && (
        <Modal title="Delete Item" onClose={() => setDeleteTarget(null)}>
          <p className="text-slate-300 text-sm mb-1">
            Permanently delete <span className="text-white font-semibold">{deleteTarget.name}</span>?
          </p>
          <p className="text-slate-500 text-xs mb-6">Cannot be undone. Write off stock first if any remains.</p>
          <div className="flex gap-3 mt-2">
            <button onClick={() => setDeleteTarget(null)} className="flex-1 px-4 py-2 bg-surface-700 hover:bg-surface-600 text-slate-300 rounded-lg text-sm transition-colors">Cancel</button>
            <button onClick={() => deleteMutation.mutate(deleteTarget.id)} disabled={deleteMutation.isPending}
              className="flex-1 px-4 py-2 bg-red-700 hover:bg-red-800 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition-colors">
              {deleteMutation.isPending ? "Deleting…" : "Delete"}
            </button>
          </div>
        </Modal>
      )}

      {/* Header */}
      <div className="flex items-start gap-4">
        <button onClick={() => navigate("/warehouses")}
          className="mt-1 p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-surface-700 transition-colors">
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-white">{warehouse.name}</h1>
            <span className="text-xs font-mono bg-surface-700 text-slate-300 px-2 py-0.5 rounded">
              {warehouse.code}
            </span>
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
              warehouse.is_active ? "bg-emerald-500/15 text-emerald-400" : "bg-slate-500/15 text-slate-400"
            }`}>
              {warehouse.is_active ? "Active" : "Inactive"}
            </span>
          </div>
          <p className="text-slate-400 text-sm mt-0.5">
            {[warehouse.city, warehouse.country].filter(Boolean).join(", ")}
            {warehouse.address && ` · ${warehouse.address}`}
          </p>
        </div>
        <div className="text-right text-sm text-slate-400">
          <p className="text-2xl font-bold text-white">{total}</p>
          <p>parts tracked</p>
        </div>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
        <input
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(0); }}
          placeholder="Search parts by name or SKU…"
          className="w-full pl-9 pr-4 py-2 bg-surface-700 border border-surface-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-brand-500 text-sm"
        />
      </div>

      {/* Parts table */}
      <div className="bg-surface-800 rounded-xl border border-surface-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-700 text-slate-400 text-xs uppercase tracking-wider">
                <th className="px-4 py-3 text-left">SKU</th>
                <th className="px-4 py-3 text-left">Part Name</th>
                <th className="px-4 py-3 text-right">Stock</th>
                <th className="px-4 py-3 text-right">Reserved</th>
                <th className="px-4 py-3 text-right">Available</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-700">
              {itemsLoading ? (
                Array.from({ length: 6 }).map((_, i) => (
                  <tr key={i}>
                    {Array.from({ length: 6 }).map((_, j) => (
                      <td key={j} className="px-4 py-3">
                        <div className="h-4 bg-surface-700 rounded animate-pulse" />
                      </td>
                    ))}
                  </tr>
                ))
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-16 text-center">
                    <Package className="h-10 w-10 text-slate-600 mx-auto mb-2" />
                    <p className="text-slate-500">
                      {search ? "No parts match your search" : "No parts in this warehouse yet"}
                    </p>
                  </td>
                </tr>
              ) : (
                items.map((item) => (
                  <tr key={item.id} className="hover:bg-surface-700/50 transition-colors">
                    <td className="px-4 py-3 font-mono text-slate-300 text-xs">{item.sku}</td>
                    <td className="px-4 py-3">
                      <p className="text-white font-medium">{item.name}</p>
                      {item.supplier_name && (
                        <p className="text-slate-500 text-xs">{item.supplier_name}</p>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <StockBadge
                        quantity={item.quantity}
                        lowThreshold={item.low_stock_threshold}
                        criticalThreshold={item.critical_stock_threshold}
                        unit={item.unit}
                      />
                    </td>
                    <td className="px-4 py-3 text-right text-slate-400 tabular-nums">
                      {item.reserved_quantity} {item.unit}
                    </td>
                    <td className="px-4 py-3 text-right text-emerald-400 font-medium tabular-nums">
                      {item.available_quantity} {item.unit}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          onClick={() => setBusTarget(item)}
                          className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium text-amber-400 bg-amber-500/10 hover:bg-amber-500/20 transition-colors"
                          title="Assign to Bus"
                        >
                          <Bus className="h-3.5 w-3.5" />
                          Bus
                        </button>
                        <button
                          onClick={() => setTransferTarget(item)}
                          className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium text-blue-400 bg-blue-500/10 hover:bg-blue-500/20 transition-colors"
                          title="Transfer to another warehouse"
                        >
                          <ArrowLeftRight className="h-3.5 w-3.5" />
                          Transfer
                        </button>
                        <button
                          onClick={() => setWriteOffTarget(item)}
                          disabled={item.available_quantity <= 0}
                          className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium text-orange-400 bg-orange-500/10 hover:bg-orange-500/20 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                          title="Drop all stock from warehouse"
                        >
                          <ArrowDown className="h-3.5 w-3.5" />
                          Drop
                        </button>
                        <button
                          onClick={() => setDeleteTarget(item)}
                          className="p-1.5 rounded text-slate-500 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                          title="Delete item"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {total > limit && (
          <div className="px-4 py-3 border-t border-surface-700 flex items-center justify-between text-sm text-slate-400">
            <span>Showing {page * limit + 1}–{Math.min((page + 1) * limit, total)} of {total}</span>
            <div className="flex gap-2">
              <button onClick={() => setPage((p) => Math.max(0, p - 1))} disabled={page === 0}
                className="px-3 py-1 bg-surface-700 hover:bg-surface-600 disabled:opacity-40 rounded text-slate-300 transition-colors">
                Previous
              </button>
              <button onClick={() => setPage((p) => p + 1)} disabled={(page + 1) * limit >= total}
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
