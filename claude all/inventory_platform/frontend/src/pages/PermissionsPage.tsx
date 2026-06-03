import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ShieldCheck, Plus, Trash2, X, Check, Lock } from "lucide-react";
import toast from "react-hot-toast";
import { rolesService } from "@/services/inventoryService";
import { extractError as getError } from "@/services/api";
import { useTranslation } from "react-i18next";

const PERMISSION_LABELS: Record<string, string> = {
  "inventory:read": "קריאת מלאי",
  "inventory:write": "עדכון מלאי",
  "inventory:admin": "ניהול מלאי",
  "warehouse:read": "קריאת מחסנים",
  "warehouse:admin": "ניהול מחסנים",
  "alerts:read": "קריאת התראות",
  "alerts:write": "ניהול התראות",
  "analytics:read": "קריאת אנליטיקה",
  "audit:read": "קריאת יומן ביקורת",
  "users:manage": "ניהול משתמשים",
};

const roleColors: Record<string, string> = {
  SuperAdmin: "border-red-500/40 bg-red-500/5",
  WarehouseManager: "border-blue-500/40 bg-blue-500/5",
  Technician: "border-amber-500/40 bg-amber-500/5",
  Viewer: "border-slate-500/40 bg-slate-500/5",
};

const inputCls =
  "w-full bg-surface-700 border border-surface-600 rounded-lg px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-brand-500 text-sm";

// ── Create Role Modal ─────────────────────────────────────────────────────────

function CreateRoleModal({
  allPermissions,
  onClose,
}: {
  allPermissions: string[];
  onClose: () => void;
}) {
  const qc = useQueryClient();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const toggle = (p: string) =>
    setSelected((s) => {
      const next = new Set(s);
      next.has(p) ? next.delete(p) : next.add(p);
      return next;
    });

  const mutation = useMutation({
    mutationFn: () =>
      rolesService.createRole({ name, description: description || undefined, permissions: [...selected] }),
    onSuccess: () => {
      toast.success(`תפקיד "${name}" נוצר`);
      qc.invalidateQueries({ queryKey: ["roles"] });
      onClose();
    },
    onError: (err) => toast.error(getError(err)),
  });

  const valid = name.trim().length >= 2;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-surface-800 rounded-xl border border-surface-700 p-6 w-full max-w-lg shadow-2xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">יצירת תפקיד מותאם</h3>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-300">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-3 mb-4">
          <div>
            <label className="text-sm text-slate-400 block mb-1">שם התפקיד *</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="לדוגמה: RegionalManager"
              className={inputCls}
            />
          </div>
          <div>
            <label className="text-sm text-slate-400 block mb-1">תיאור</label>
            <input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="תיאור קצר של התפקיד"
              className={inputCls}
            />
          </div>
        </div>

        <div className="mb-5">
          <p className="text-sm text-slate-400 mb-2">הרשאות</p>
          <div className="grid grid-cols-2 gap-1.5 max-h-52 overflow-y-auto pr-1">
            {allPermissions.map((p) => (
              <button
                key={p}
                onClick={() => toggle(p)}
                className={`flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs transition-colors text-left ${
                  selected.has(p)
                    ? "bg-brand-600 text-white"
                    : "bg-surface-700 text-slate-400 hover:text-white"
                }`}
              >
                <div className={`h-3.5 w-3.5 rounded border flex items-center justify-center shrink-0 ${
                  selected.has(p) ? "bg-white border-white" : "border-slate-500"
                }`}>
                  {selected.has(p) && <Check className="h-2.5 w-2.5 text-brand-600" />}
                </div>
                {PERMISSION_LABELS[p] ?? p}
              </button>
            ))}
          </div>
        </div>

        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 bg-surface-700 hover:bg-surface-600 text-slate-300 rounded-lg text-sm transition-colors"
          >
            ביטול
          </button>
          <button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending || !valid}
            className="flex-1 px-4 py-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors"
          >
            {mutation.isPending ? "יוצר…" : "צור תפקיד"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Role Card ─────────────────────────────────────────────────────────────────

function RoleCard({
  role,
  onDelete,
}: {
  role: { name: string; permissions: string[]; is_system: boolean; description?: string | null };
  onDelete: () => void;
}) {
  return (
    <div className={`rounded-xl border p-4 ${roleColors[role.name] ?? "border-surface-600 bg-surface-800"}`}>
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-white">{role.name}</h3>
            {role.is_system && (
              <span className="flex items-center gap-1 text-xs text-slate-500">
                <Lock className="h-3 w-3" /> מערכת
              </span>
            )}
          </div>
          {role.description && (
            <p className="text-xs text-slate-500 mt-0.5">{role.description}</p>
          )}
        </div>
        {!role.is_system && (
          <button
            onClick={onDelete}
            className="p-1 rounded text-slate-500 hover:text-red-400 hover:bg-red-500/10 transition-colors"
            title="מחק תפקיד"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        )}
      </div>

      <div className="flex flex-wrap gap-1.5">
        {role.permissions.length === 0 ? (
          <span className="text-xs text-slate-600">אין הרשאות</span>
        ) : (
          role.permissions.map((p) => (
            <span
              key={p}
              className="px-2 py-0.5 rounded-full text-xs bg-surface-700 text-slate-300 border border-surface-600"
            >
              {PERMISSION_LABELS[p] ?? p}
            </span>
          ))
        )}
      </div>

      <p className="text-xs text-slate-600 mt-2">{role.permissions.length} הרשאות</p>
    </div>
  );
}

// ── Permission Matrix Table ───────────────────────────────────────────────────

function PermissionMatrix({
  roles,
  allPermissions,
}: {
  roles: Array<{ name: string; permissions: string[] }>;
  allPermissions: string[];
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs border-collapse">
        <thead>
          <tr>
            <th className="px-3 py-2 text-left text-slate-400 font-medium border-b border-surface-700 bg-surface-800 sticky left-0 z-10 min-w-40">
              הרשאה
            </th>
            {roles.map((r) => (
              <th
                key={r.name}
                className="px-3 py-2 text-center text-slate-400 font-medium border-b border-surface-700 whitespace-nowrap"
              >
                {r.name}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-surface-700/50">
          {allPermissions.map((p) => (
            <tr key={p} className="hover:bg-surface-700/30">
              <td className="px-3 py-2 text-slate-300 font-mono bg-surface-800 sticky left-0 border-r border-surface-700">
                {PERMISSION_LABELS[p] ?? p}
                <span className="block text-slate-600 text-[10px]">{p}</span>
              </td>
              {roles.map((r) => (
                <td key={r.name} className="px-3 py-2 text-center">
                  {r.permissions.includes(p) ? (
                    <Check className="h-4 w-4 text-green-400 mx-auto" />
                  ) : (
                    <span className="text-slate-700">—</span>
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export function PermissionsPage() {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [activeTab, setActiveTab] = useState<"cards" | "matrix">("cards");

  const { data, isLoading } = useQuery({
    queryKey: ["roles"],
    queryFn: rolesService.listRoles,
  });

  const roles = data?.roles ?? [];
  const allPermissions: string[] = data?.all_permissions ?? [];

  const deleteMutation = useMutation({
    mutationFn: (name: string) => rolesService.deleteRole(name),
    onSuccess: (_, name) => {
      toast.success(`תפקיד "${name}" נמחק`);
      qc.invalidateQueries({ queryKey: ["roles"] });
    },
    onError: (err) => toast.error(getError(err)),
  });

  const handleDelete = (name: string) => {
    if (window.confirm(`למחוק את התפקיד "${name}"?`)) {
      deleteMutation.mutate(name);
    }
  };

  return (
    <div className="space-y-5">
      {showCreate && (
        <CreateRoleModal allPermissions={allPermissions} onClose={() => setShowCreate(false)} />
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <ShieldCheck className="h-6 w-6 text-brand-500" />
            {t("permissions.title")}
          </h1>
          <p className="text-slate-400 text-sm mt-1">{t("permissions.subtitle")}</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg text-sm font-medium transition-colors"
        >
          <Plus className="h-4 w-4" />
          {t("permissions.createRole")}
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-surface-800 p-1 rounded-lg w-fit border border-surface-700">
        {(["cards", "matrix"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
              activeTab === tab
                ? "bg-brand-600 text-white"
                : "text-slate-400 hover:text-white"
            }`}
          >
            {tab === "cards" ? t("permissions.roleCards") : t("permissions.matrix")}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-40 rounded-xl bg-surface-800 border border-surface-700 animate-pulse" />
          ))}
        </div>
      ) : activeTab === "cards" ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {roles.map((role: any) => (
            <RoleCard key={role.name} role={role} onDelete={() => handleDelete(role.name)} />
          ))}
        </div>
      ) : (
        <div className="bg-surface-800 rounded-xl border border-surface-700 overflow-hidden">
          <PermissionMatrix roles={roles} allPermissions={allPermissions} />
        </div>
      )}
    </div>
  );
}
