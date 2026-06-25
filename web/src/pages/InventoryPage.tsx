/**
 * Inventory page — searchable, filterable table with issue/restock/transfer/add actions.
 */
import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Search,
  Plus,
  ArrowDown,
  ArrowUp,
  ArrowLeftRight,
  X,
  Package,
  Clock,
  Trash2,
  Bus,
} from "lucide-react";
import toast from "react-hot-toast";
import { inventoryService, warehouseService, busService } from "@/services/inventoryService";
import { extractError as getError } from "@/services/api";
import { StockBadge } from "@/components/ui/StockBadge";
import { useTranslation } from "react-i18next";
import type { InventoryItem, Transaction } from "@/types";

// ── Shared modal shell ──────────────────────────────────────────────────────

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

function ModalActions({
  onClose,
  onConfirm,
  pending,
  label,
  confirmClass = "bg-brand-600 hover:bg-brand-700 text-white",
}: {
  onClose: () => void;
  onConfirm: () => void;
  pending: boolean;
  label: string;
  confirmClass?: string;
}) {
  return (
    <div className="flex gap-3 mt-6">
      <button
        onClick={onClose}
        className="flex-1 px-4 py-2 bg-surface-700 hover:bg-surface-600 text-slate-300 rounded-lg text-sm transition-colors"
      >
        Cancel
      </button>
      <button
        onClick={onConfirm}
        disabled={pending}
        className={`flex-1 px-4 py-2 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-sm font-medium transition-colors ${confirmClass}`}
      >
        {pending ? "Processing..." : label}
      </button>
    </div>
  );
}

// ── Field helper ────────────────────────────────────────────────────────────

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="text-sm text-slate-400 block mb-1">{label}</label>
      {children}
    </div>
  );
}

const inputCls =
  "w-full bg-surface-700 border border-surface-600 rounded-lg px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-brand-500 text-sm";

// ── Issue modal ─────────────────────────────────────────────────────────────

function IssueModal({ item, onClose }: { item: InventoryItem; onClose: () => void }) {
  const qc = useQueryClient();
  const [qty, setQty] = useState("1");
  const [notes, setNotes] = useState("");
  const [busId, setBusId] = useState("");

  const { data: buses = [] } = useQuery({
    queryKey: ["buses"],
    queryFn: () => busService.listBuses(),
  });

  const mutation = useMutation({
    mutationFn: () =>
      inventoryService.issueItem({
        item_id: item.id,
        quantity: parseFloat(qty),
        notes: notes || undefined,
        bus_id: busId || undefined,
      }),
    onSuccess: () => {
      const bus = buses.find((b) => b.id === busId);
      const busLabel = bus ? ` → Bus ${bus.fleet_number}` : "";
      toast.success(`Issued ${qty} ${item.unit} of ${item.name}${busLabel}`);
      qc.invalidateQueries({ queryKey: ["inventory"] });
      onClose();
    },
    onError: (err) => toast.error(getError(err)),
  });

  return (
    <Modal title={<>Issue: <span className="text-brand-400">{item.name}</span></>} onClose={onClose}>
      <div className="space-y-4">
        <Field label={`Quantity (available: ${item.available_quantity} ${item.unit})`}>
          <input
            type="number"
            value={qty}
            onChange={(e) => setQty(e.target.value)}
            min="0.001"
            max={item.available_quantity}
            step="0.001"
            className={inputCls}
          />
        </Field>
        <Field label="Assign to Bus (optional)">
          <select value={busId} onChange={(e) => setBusId(e.target.value)} className={inputCls}>
            <option value="">No bus / general issue</option>
            {buses.map((b) => (
              <option key={b.id} value={b.id}>
                {b.fleet_number} — {b.make} {b.model} ({b.year})
              </option>
            ))}
          </select>
        </Field>
        <Field label="Notes">
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={2}
            className={`${inputCls} resize-none`}
          />
        </Field>
      </div>
      <ModalActions
        onClose={onClose}
        onConfirm={() => mutation.mutate()}
        pending={mutation.isPending}
        label="Issue"
        confirmClass="bg-red-600 hover:bg-red-700 text-white"
      />
    </Modal>
  );
}

// ── Restock modal ───────────────────────────────────────────────────────────

function RestockModal({ item, onClose }: { item: InventoryItem; onClose: () => void }) {
  const qc = useQueryClient();
  const [qty, setQty] = useState("1");
  const [reference, setReference] = useState("");
  const [notes, setNotes] = useState("");

  const mutation = useMutation({
    mutationFn: () =>
      inventoryService.restockItem({
        item_id: item.id,
        quantity: parseFloat(qty),
        reference_number: reference || undefined,
        notes: notes || undefined,
      }),
    onSuccess: () => {
      toast.success(`Restocked ${qty} ${item.unit} of ${item.name}`);
      qc.invalidateQueries({ queryKey: ["inventory"] });
      onClose();
    },
    onError: (err) => toast.error(getError(err)),
  });

  return (
    <Modal title={<>Restock: <span className="text-emerald-400">{item.name}</span></>} onClose={onClose}>
      <div className="space-y-4">
        <Field label={`Quantity to add (current: ${item.quantity} ${item.unit})`}>
          <input
            type="number"
            value={qty}
            onChange={(e) => setQty(e.target.value)}
            min="0.001"
            step="0.001"
            className={inputCls}
          />
        </Field>
        <Field label="Purchase order / reference (optional)">
          <input
            value={reference}
            onChange={(e) => setReference(e.target.value)}
            placeholder="PO-2026-001"
            className={inputCls}
          />
        </Field>
        <Field label="Notes">
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={2}
            className={`${inputCls} resize-none`}
          />
        </Field>
      </div>
      <ModalActions
        onClose={onClose}
        onConfirm={() => mutation.mutate()}
        pending={mutation.isPending}
        label="Restock"
        confirmClass="bg-emerald-600 hover:bg-emerald-700 text-white"
      />
    </Modal>
  );
}

// ── Add Item modal ──────────────────────────────────────────────────────────

function AddItemModal({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient();
  const { data: warehouses = [] } = useQuery({
    queryKey: ["warehouses", "active"],
    queryFn: () => warehouseService.listWarehouses(true),
  });
  const [form, setForm] = useState({
    sku: "",
    name: "",
    unit: "pcs",
    quantity: "0",
    low_stock_threshold: "10",
    critical_stock_threshold: "3",
    warehouse_id: "",
    description: "",
    supplier_name: "",
    unit_cost: "",
    lead_time_days: "",
  });

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  const mutation = useMutation({
    mutationFn: () =>
      inventoryService.createItem({
        sku: form.sku,
        name: form.name,
        unit: form.unit,
        quantity: parseFloat(form.quantity),
        low_stock_threshold: parseFloat(form.low_stock_threshold),
        critical_stock_threshold: parseFloat(form.critical_stock_threshold),
        warehouse_id: form.warehouse_id,
        description: form.description || undefined,
        supplier_name: form.supplier_name || undefined,
        unit_cost: form.unit_cost ? parseFloat(form.unit_cost) : undefined,
        lead_time_days: form.lead_time_days ? parseInt(form.lead_time_days) : undefined,
      }),
    onSuccess: (item) => {
      toast.success(`Created "${item.name}"`);
      qc.invalidateQueries({ queryKey: ["inventory"] });
      onClose();
    },
    onError: (err) => toast.error(getError(err)),
  });

  const valid = form.sku && form.name && form.warehouse_id;

  return (
    <Modal title="Add Inventory Item" onClose={onClose}>
      <div className="space-y-3 max-h-[60vh] overflow-y-auto pr-1">
        <div className="grid grid-cols-2 gap-3">
          <Field label="SKU *">
            <input value={form.sku} onChange={set("sku")} placeholder="BRK-001" className={inputCls} />
          </Field>
          <Field label="Unit *">
            <input value={form.unit} onChange={set("unit")} placeholder="pcs / L / kg" className={inputCls} />
          </Field>
        </div>
        <Field label="Name *">
          <input value={form.name} onChange={set("name")} placeholder="Brake pad set" className={inputCls} />
        </Field>
        <Field label="Warehouse *">
          <select
            value={form.warehouse_id}
            onChange={(e) => setForm((f) => ({ ...f, warehouse_id: e.target.value }))}
            className={inputCls}
          >
            <option value="">Select warehouse…</option>
            {warehouses.map((w) => (
              <option key={w.id} value={w.id}>{w.name} ({w.code})</option>
            ))}
          </select>
        </Field>
        <div className="grid grid-cols-3 gap-3">
          <Field label="Initial qty">
            <input type="number" value={form.quantity} onChange={set("quantity")} min="0" className={inputCls} />
          </Field>
          <Field label="Low threshold">
            <input type="number" value={form.low_stock_threshold} onChange={set("low_stock_threshold")} min="0" className={inputCls} />
          </Field>
          <Field label="Critical threshold">
            <input type="number" value={form.critical_stock_threshold} onChange={set("critical_stock_threshold")} min="0" className={inputCls} />
          </Field>
        </div>
        <Field label="Supplier (optional)">
          <input value={form.supplier_name} onChange={set("supplier_name")} placeholder="Supplier name" className={inputCls} />
        </Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Unit cost ($)">
            <input type="number" value={form.unit_cost} onChange={set("unit_cost")} min="0" step="0.01" placeholder="0.00" className={inputCls} />
          </Field>
          <Field label="Lead time (days)">
            <input type="number" value={form.lead_time_days} onChange={set("lead_time_days")} min="0" placeholder="7" className={inputCls} />
          </Field>
        </div>
        <Field label="Description">
          <textarea
            value={form.description}
            onChange={set("description")}
            rows={2}
            className={`${inputCls} resize-none`}
          />
        </Field>
      </div>
      <ModalActions
        onClose={onClose}
        onConfirm={() => mutation.mutate()}
        pending={mutation.isPending}
        label="Create Item"
        confirmClass={`text-white ${valid ? "bg-brand-600 hover:bg-brand-700" : "bg-brand-600/50 cursor-not-allowed"}`}
      />
    </Modal>
  );
}

// ── Transfer modal ──────────────────────────────────────────────────────────

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
    queryFn: () =>
      inventoryService.listItems({
        warehouse_id: destWarehouseId,
        search: search || undefined,
        limit: 20,
      }),
    enabled: !!destWarehouseId && !destItem,
  });

  const destItems = destItemsData?.items ?? [];

  const mutation = useMutation({
    mutationFn: () =>
      inventoryService.transferItem({
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
          <p className="text-slate-400 text-xs mb-0.5">Source</p>
          <p className="text-white font-medium">{item.name}</p>
          <p className="text-slate-500 text-xs font-mono">
            Available: {item.available_quantity} {item.unit}
          </p>
        </div>

        <Field label="Destination Warehouse">
          <select
            value={destWarehouseId}
            onChange={(e) => {
              setDestWarehouseId(e.target.value);
              setDestItem(null);
              setSearch("");
            }}
            className={inputCls}
          >
            <option value="">Select warehouse…</option>
            {warehouses
              .filter((w) => w.id !== item.warehouse_id)
              .map((w) => (
                <option key={w.id} value={w.id}>
                  {w.name} ({w.code})
                </option>
              ))}
          </select>
        </Field>

        {destWarehouseId && (
          <Field label="Destination Item">
            {destItem ? (
              <div className="flex items-center justify-between bg-surface-700 rounded-lg p-2.5">
                <div>
                  <p className="text-white text-sm font-medium">{destItem.name}</p>
                  <p className="text-slate-400 text-xs">
                    {destItem.available_quantity} {destItem.unit} available
                  </p>
                </div>
                <button
                  onClick={() => setDestItem(null)}
                  className="text-slate-500 hover:text-slate-300 transition-colors"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ) : (
              <div>
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search by name or SKU…"
                  className={inputCls}
                />
                {destItems.length > 0 && (
                  <div className="mt-1 bg-surface-700 border border-surface-600 rounded-lg overflow-hidden max-h-36 overflow-y-auto">
                    {destItems.map((di) => (
                      <button
                        key={di.id}
                        onClick={() => setDestItem(di)}
                        className="w-full text-left px-3 py-2 hover:bg-surface-600 text-sm flex items-center justify-between transition-colors"
                      >
                        <span className="text-white">{di.name}</span>
                        <span className="text-slate-400 text-xs tabular-nums">
                          {di.available_quantity} {di.unit}
                        </span>
                      </button>
                    ))}
                  </div>
                )}
                {destItems.length === 0 && (
                  <p className="text-amber-400/80 text-xs mt-1 px-1">
                    {search
                      ? "No matching item in this warehouse."
                      : "Type to search items in this warehouse."}{" "}
                    A transfer moves stock into an existing destination item — if none exists, create one in that warehouse first.
                  </p>
                )}
              </div>
            )}
          </Field>
        )}

        <Field label={`Quantity (available: ${item.available_quantity} ${item.unit})`}>
          <input
            type="number"
            value={qty}
            onChange={(e) => setQty(e.target.value)}
            min="0.001"
            max={item.available_quantity}
            step="0.001"
            className={inputCls}
          />
        </Field>
        <Field label="Notes">
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={2}
            className={`${inputCls} resize-none`}
          />
        </Field>
      </div>
      <ModalActions
        onClose={onClose}
        onConfirm={() => mutation.mutate()}
        pending={mutation.isPending}
        label="Transfer"
        confirmClass={`text-white ${valid ? "bg-blue-600 hover:bg-blue-700" : "bg-blue-600/50 cursor-not-allowed"}`}
      />
    </Modal>
  );
}

// ── Item Detail Drawer ──────────────────────────────────────────────────────

function ItemDetailDrawer({ item, onClose }: { item: InventoryItem; onClose: () => void }) {
  const { data: txData } = useQuery({
    queryKey: ["transactions", item.id],
    queryFn: () => inventoryService.listTransactions({ item_id: item.id }),
  });

  const transactions: Transaction[] = txData?.transactions ?? [];

  const txTypeColors: Record<string, string> = {
    ISSUE: "text-red-400",
    RESTOCK: "text-emerald-400",
    TRANSFER: "text-blue-400",
    ADJUSTMENT: "text-amber-400",
    WRITE_OFF: "text-slate-400",
  };

  return (
    <div className="fixed inset-0 z-40 flex justify-end">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />

      {/* Drawer */}
      <div className="relative w-full max-w-md bg-surface-900 border-l border-surface-700 shadow-2xl flex flex-col h-full overflow-hidden">
        {/* Header */}
        <div className="flex items-start justify-between p-6 border-b border-surface-700 shrink-0">
          <div>
            <div className="flex items-center gap-2">
              <Package className="h-5 w-5 text-brand-400" />
              <h2 className="text-lg font-semibold text-white">{item.name}</h2>
            </div>
            <p className="text-slate-500 text-xs font-mono mt-0.5">{item.sku}</p>
          </div>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-300 transition-colors mt-0.5">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Stock summary */}
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: "Total", value: item.quantity, cls: "text-white" },
              { label: "Reserved", value: item.reserved_quantity, cls: "text-amber-400" },
              { label: "Available", value: item.available_quantity, cls: "text-emerald-400" },
            ].map(({ label, value, cls }) => (
              <div key={label} className="bg-surface-800 rounded-lg p-3 text-center">
                <p className="text-slate-500 text-xs">{label}</p>
                <p className={`text-xl font-bold mt-0.5 ${cls}`}>{value}</p>
                <p className="text-slate-600 text-xs">{item.unit}</p>
              </div>
            ))}
          </div>

          {/* Thresholds */}
          <div className="bg-surface-800 rounded-lg p-4 space-y-2">
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Thresholds</p>
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">Low stock alert</span>
              <span className="text-amber-400 font-medium">{item.low_stock_threshold} {item.unit}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">Critical stock alert</span>
              <span className="text-red-400 font-medium">{item.critical_stock_threshold} {item.unit}</span>
            </div>
          </div>

          {/* Meta */}
          {(item.supplier_name || item.unit_cost != null || item.lead_time_days != null) && (
            <div className="bg-surface-800 rounded-lg p-4 space-y-2">
              <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Procurement</p>
              {item.supplier_name && (
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Supplier</span>
                  <span className="text-white">{item.supplier_name}</span>
                </div>
              )}
              {item.unit_cost != null && (
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Unit cost</span>
                  <span className="text-white">${item.unit_cost.toFixed(2)}</span>
                </div>
              )}
              {item.lead_time_days != null && (
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Lead time</span>
                  <span className="text-white">{item.lead_time_days} days</span>
                </div>
              )}
            </div>
          )}

          {/* Description */}
          {item.description && (
            <div className="bg-surface-800 rounded-lg p-4">
              <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">Description</p>
              <p className="text-slate-300 text-sm">{item.description}</p>
            </div>
          )}

          {/* Transaction history */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Clock className="h-4 w-4 text-slate-500" />
              <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">
                Recent Transactions
              </p>
            </div>
            {transactions.length === 0 ? (
              <p className="text-slate-600 text-sm text-center py-4">No transactions yet</p>
            ) : (
              <div className="space-y-2">
                {transactions.slice(0, 20).map((tx) => (
                  <div
                    key={tx.id}
                    className="bg-surface-800 rounded-lg px-3 py-2.5 flex items-center justify-between text-sm"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <span className={`text-xs font-semibold shrink-0 ${txTypeColors[tx.type] ?? "text-slate-400"}`}>
                        {tx.type}
                      </span>
                      {tx.notes && (
                        <span className="text-slate-500 text-xs truncate">{tx.notes}</span>
                      )}
                    </div>
                    <div className="text-right shrink-0 ml-2">
                      <span className={`font-medium tabular-nums ${tx.quantity_delta > 0 ? "text-emerald-400" : "text-red-400"}`}>
                        {tx.quantity_delta > 0 ? "+" : ""}{tx.quantity_delta}
                      </span>
                      <p className="text-slate-600 text-xs">
                        {new Date(tx.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Main page ───────────────────────────────────────────────────────────────

export function InventoryPage() {
  const qc = useQueryClient();
  const { t } = useTranslation();
  const [search, setSearch] = useState("");
  const [lowStockOnly, setLowStockOnly] = useState(false);
  const [page, setPage] = useState(0);
  const limit = 50;

  const [detailItem, setDetailItem] = useState<InventoryItem | null>(null);
  const [issueTarget, setIssueTarget] = useState<InventoryItem | null>(null);
  const [restockTarget, setRestockTarget] = useState<InventoryItem | null>(null);
  const [transferTarget, setTransferTarget] = useState<InventoryItem | null>(null);
  const [showAddItem, setShowAddItem] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<InventoryItem | null>(null);
  const [writeOffTarget, setWriteOffTarget] = useState<InventoryItem | null>(null);

  const deleteMutation = useMutation({
    mutationFn: (id: string) => inventoryService.deleteItem(id),
    onSuccess: () => {
      toast.success("Item deleted");
      qc.invalidateQueries({ queryKey: ["inventory"] });
      setDeleteTarget(null);
    },
    onError: (err) => toast.error(getError(err)),
  });

  const writeOffMutation = useMutation({
    mutationFn: (item: InventoryItem) =>
      inventoryService.writeOffItem(item.id, item.available_quantity, "Write-off: removed from warehouse"),
    onSuccess: () => {
      toast.success("Stock written off");
      qc.invalidateQueries({ queryKey: ["inventory"] });
      setWriteOffTarget(null);
    },
    onError: (err) => toast.error(getError(err)),
  });

  const { data, isLoading } = useQuery({
    queryKey: ["inventory", "items", { search, lowStockOnly, page }],
    queryFn: () =>
      inventoryService.listItems({
        search: search || undefined,
        low_stock_only: lowStockOnly,
        offset: page * limit,
        limit,
      }),
    refetchInterval: 30_000,
  });

  const items = data?.items ?? [];
  const total = data?.total ?? 0;

  return (
    <div className="space-y-4">
      {/* Modals */}
      {issueTarget && <IssueModal item={issueTarget} onClose={() => setIssueTarget(null)} />}
      {restockTarget && <RestockModal item={restockTarget} onClose={() => setRestockTarget(null)} />}
      {transferTarget && <TransferModal item={transferTarget} onClose={() => setTransferTarget(null)} />}
      {showAddItem && <AddItemModal onClose={() => setShowAddItem(false)} />}

      {/* Delete confirmation */}
      {deleteTarget && (
        <Modal title="Delete Item" onClose={() => setDeleteTarget(null)}>
          <p className="text-slate-300 text-sm mb-1">
            Permanently delete <span className="text-white font-semibold">{deleteTarget.name}</span>?
          </p>
          <p className="text-slate-500 text-xs mb-6">
            This cannot be undone. Items with existing transactions cannot be deleted — write off the stock first.
          </p>
          <ModalActions
            onClose={() => setDeleteTarget(null)}
            onConfirm={() => deleteMutation.mutate(deleteTarget.id)}
            pending={deleteMutation.isPending}
            label="Delete"
            confirmClass="bg-red-700 hover:bg-red-800 text-white"
          />
        </Modal>
      )}

      {/* Write-off confirmation */}
      {writeOffTarget && (
        <Modal title="Write Off Stock" onClose={() => setWriteOffTarget(null)}>
          <p className="text-slate-300 text-sm mb-1">
            Write off all <span className="text-white font-semibold">{writeOffTarget.available_quantity} {writeOffTarget.unit}</span> of{" "}
            <span className="text-white font-semibold">{writeOffTarget.name}</span>?
          </p>
          <p className="text-slate-500 text-xs mb-6">
            Stock will be set to zero. The transaction is recorded in the audit log.
          </p>
          <ModalActions
            onClose={() => setWriteOffTarget(null)}
            onConfirm={() => writeOffMutation.mutate(writeOffTarget)}
            pending={writeOffMutation.isPending}
            label="Write Off"
            confirmClass="bg-amber-700 hover:bg-amber-800 text-white"
          />
        </Modal>
      )}

      {/* Detail drawer */}
      {detailItem && <ItemDetailDrawer item={detailItem} onClose={() => setDetailItem(null)} />}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">{t("inventory.title")}</h1>
          <p className="text-slate-400 text-sm mt-1">{total} {t("inventory.title").toLowerCase()}</p>
        </div>
        <button
          onClick={() => setShowAddItem(true)}
          className="flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg text-sm font-medium transition-colors"
        >
          <Plus className="h-4 w-4" />
          {t("inventory.addItem")}
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-3 items-center flex-wrap">
        <div className="relative flex-1 min-w-48">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
          <input
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(0); }}
            placeholder="Search SKU or name..."
            className="w-full pl-9 pr-4 py-2 bg-surface-700 border border-surface-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-brand-500 text-sm"
          />
        </div>
        <label className="flex items-center gap-2 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={lowStockOnly}
            onChange={(e) => { setLowStockOnly(e.target.checked); setPage(0); }}
            className="rounded"
          />
          <span className="text-sm text-slate-300">Low stock only</span>
        </label>
      </div>

      {/* Table */}
      <div className="bg-surface-800 rounded-xl border border-surface-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-700 text-slate-400 text-xs uppercase tracking-wider">
                <th className="px-4 py-3 text-left">{t("inventory.sku")}</th>
                <th className="px-4 py-3 text-left">{t("inventory.name")}</th>
                <th className="px-4 py-3 text-right">{t("inventory.quantity")}</th>
                <th className="px-4 py-3 text-right">{t("inventory.reserved")}</th>
                <th className="px-4 py-3 text-right">{t("inventory.available")}</th>
                <th className="px-4 py-3 text-left">{t("inventory.warehouse")}</th>
                <th className="px-4 py-3 text-right">{t("common.actions")}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-700">
              {isLoading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i}>
                    {Array.from({ length: 7 }).map((_, j) => (
                      <td key={j} className="px-4 py-3">
                        <div className="h-4 bg-surface-700 rounded animate-pulse" />
                      </td>
                    ))}
                  </tr>
                ))
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-12 text-center text-slate-500">
                    {t("inventory.noItems")}
                  </td>
                </tr>
              ) : (
                items.map((item) => (
                  <tr
                    key={item.id}
                    className="hover:bg-surface-700/50 transition-colors cursor-pointer"
                    onClick={() => setDetailItem(item)}
                  >
                    <td className="px-4 py-3 font-mono text-slate-300 text-xs">{item.sku}</td>
                    <td className="px-4 py-3 text-white font-medium">{item.name}</td>
                    <td className="px-4 py-3 text-right">
                      <StockBadge
                        quantity={item.quantity}
                        lowThreshold={item.low_stock_threshold}
                        criticalThreshold={item.critical_stock_threshold}
                        unit={item.unit}
                      />
                    </td>
                    <td className="px-4 py-3 text-right text-slate-400 tabular-nums">
                      {item.reserved_quantity}
                    </td>
                    <td className="px-4 py-3 text-right text-slate-300 tabular-nums font-medium">
                      {item.available_quantity}
                    </td>
                    <td className="px-4 py-3 text-slate-400 text-xs font-mono">
                      {item.warehouse_id?.slice(0, 8)}…
                    </td>
                    <td className="px-4 py-3 text-right" onClick={(e) => e.stopPropagation()}>
                      <div className="flex items-center justify-end gap-1">
                        <button
                          onClick={() => setIssueTarget(item)}
                          className="p-1.5 rounded text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                          title="Issue to Bus"
                        >
                          <Bus className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => setRestockTarget(item)}
                          className="p-1.5 rounded text-slate-400 hover:text-emerald-400 hover:bg-emerald-500/10 transition-colors"
                          title="Restock"
                        >
                          <ArrowUp className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => setTransferTarget(item)}
                          className="p-1.5 rounded text-slate-400 hover:text-blue-400 hover:bg-blue-500/10 transition-colors"
                          title="Transfer between warehouses"
                        >
                          <ArrowLeftRight className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => setWriteOffTarget(item)}
                          disabled={item.available_quantity <= 0}
                          className="p-1.5 rounded text-slate-400 hover:text-amber-400 hover:bg-amber-500/10 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                          title="Write off stock"
                        >
                          <ArrowDown className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => setDeleteTarget(item)}
                          className="p-1.5 rounded text-slate-400 hover:text-red-500 hover:bg-red-500/10 transition-colors"
                          title="Delete item"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {total > limit && (
          <div className="px-4 py-3 border-t border-surface-700 flex items-center justify-between text-sm text-slate-400">
            <span>
              Showing {page * limit + 1}–{Math.min((page + 1) * limit, total)} of {total}
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
                className="px-3 py-1 bg-surface-700 hover:bg-surface-600 disabled:opacity-40 rounded text-slate-300 transition-colors"
              >
                Previous
              </button>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={(page + 1) * limit >= total}
                className="px-3 py-1 bg-surface-700 hover:bg-surface-600 disabled:opacity-40 rounded text-slate-300 transition-colors"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
