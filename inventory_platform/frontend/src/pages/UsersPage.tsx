import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2, X, Users } from "lucide-react";
import toast from "react-hot-toast";
import { usersService } from "@/services/inventoryService";
import { extractError as getError } from "@/services/api";
import { useTranslation } from "react-i18next";

// ── Modal shell ───────────────────────────────────────────────────────────────

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

const ROLES = ["Viewer", "Technician", "WarehouseManager", "SuperAdmin"] as const;

const roleColors: Record<string, string> = {
  SuperAdmin: "bg-red-500/15 text-red-400",
  WarehouseManager: "bg-blue-500/15 text-blue-400",
  Technician: "bg-amber-500/15 text-amber-400",
  Viewer: "bg-slate-500/15 text-slate-400",
};

// ── Invite User Modal ─────────────────────────────────────────────────────────

function InviteUserModal({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient();
  const [form, setForm] = useState({
    email: "",
    full_name: "",
    username: "",
    password: "",
    role: "Viewer",
  });

  const set =
    (k: keyof typeof form) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
      setForm((f) => ({ ...f, [k]: e.target.value }));

  const mutation = useMutation({
    mutationFn: () => usersService.createUser(form),
    onSuccess: () => {
      toast.success(`User ${form.email} invited as ${form.role}`);
      qc.invalidateQueries({ queryKey: ["users"] });
      onClose();
    },
    onError: (err) => toast.error(getError(err)),
  });

  const valid = form.email && form.full_name && form.username && form.password.length >= 8;

  return (
    <Modal title="Invite User" onClose={onClose}>
      <div className="space-y-3">
        <Field label="Email *">
          <input
            type="email"
            value={form.email}
            onChange={set("email")}
            placeholder="user@depot.com"
            className={inputCls}
          />
        </Field>
        <Field label="Full Name *">
          <input
            value={form.full_name}
            onChange={set("full_name")}
            placeholder="John Smith"
            className={inputCls}
          />
        </Field>
        <Field label="Username *">
          <input
            value={form.username}
            onChange={set("username")}
            placeholder="jsmith"
            className={inputCls}
          />
        </Field>
        <Field label="Password * (min 8 chars)">
          <input
            type="password"
            value={form.password}
            onChange={set("password")}
            placeholder="••••••••"
            className={inputCls}
          />
        </Field>
        <Field label="Role">
          <select value={form.role} onChange={set("role")} className={inputCls}>
            {ROLES.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
        </Field>
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
          {mutation.isPending ? "Inviting…" : "Invite"}
        </button>
      </div>
    </Modal>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export function UsersPage() {
  const qc = useQueryClient();
  const { t } = useTranslation();
  const [showInvite, setShowInvite] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["users"],
    queryFn: usersService.listUsers,
    refetchInterval: 120_000,
  });

  const users: any[] = data?.users ?? [];

  const roleMutation = useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: string }) =>
      usersService.assignRole(userId, role),
    onSuccess: (_, vars) => {
      toast.success(t("users.roleUpdated", { role: vars.role }));
      qc.invalidateQueries({ queryKey: ["users"] });
    },
    onError: (err) => toast.error(getError(err)),
  });

  const deleteMutation = useMutation({
    mutationFn: (userId: string) => usersService.deleteUser(userId),
    onSuccess: () => {
      toast.success(t("users.userDeleted"));
      qc.invalidateQueries({ queryKey: ["users"] });
    },
    onError: (err) => toast.error(getError(err)),
  });

  const handleDelete = (user: any) => {
    if (window.confirm(t("users.deleteConfirm", { email: user.email }))) {
      deleteMutation.mutate(user.id);
    }
  };

  return (
    <div className="space-y-4">
      {showInvite && <InviteUserModal onClose={() => setShowInvite(false)} />}

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">{t("users.title")}</h1>
          <p className="text-slate-400 text-sm mt-1">{users.length} {t("users.title").toLowerCase()}</p>
        </div>
        <button
          onClick={() => setShowInvite(true)}
          className="flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg text-sm font-medium transition-colors"
        >
          <Plus className="h-4 w-4" />
          {t("users.inviteUser")}
        </button>
      </div>

      <div className="bg-surface-800 rounded-xl border border-surface-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-700 text-slate-400 text-xs uppercase tracking-wider">
                <th className="px-4 py-3 text-left">{t("users.email")}</th>
                <th className="px-4 py-3 text-left">{t("users.fullName")}</th>
                <th className="px-4 py-3 text-left">{t("users.username")}</th>
                <th className="px-4 py-3 text-left">{t("users.role")}</th>
                <th className="px-4 py-3 text-left">{t("users.created")}</th>
                <th className="px-4 py-3 text-right">{t("users.actions")}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-700">
              {isLoading ? (
                Array.from({ length: 3 }).map((_, i) => (
                  <tr key={i}>
                    {Array.from({ length: 6 }).map((_, j) => (
                      <td key={j} className="px-4 py-3">
                        <div className="h-4 bg-surface-700 rounded animate-pulse" />
                      </td>
                    ))}
                  </tr>
                ))
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center">
                    <Users className="h-10 w-10 text-slate-600 mx-auto mb-2" />
                    <p className="text-slate-500">{t("users.noUsers")}</p>
                  </td>
                </tr>
              ) : (
                users.map((user) => {
                  const role = user.roles?.[0] ?? "Viewer";
                  return (
                    <tr key={user.id} className="hover:bg-surface-700/50 transition-colors">
                      <td className="px-4 py-3 text-white">{user.email}</td>
                      <td className="px-4 py-3 text-slate-300">{user.full_name || "—"}</td>
                      <td className="px-4 py-3 text-slate-400 font-mono text-xs">{user.username || "—"}</td>
                      <td className="px-4 py-3">
                        <select
                          value={role}
                          onChange={(e) => roleMutation.mutate({ userId: user.id, role: e.target.value })}
                          className={`text-xs font-medium px-2 py-1 rounded-full border-0 cursor-pointer focus:outline-none focus:ring-1 focus:ring-brand-500 ${
                            roleColors[role] ?? roleColors["Viewer"]
                          } bg-transparent`}
                        >
                          {ROLES.map((r) => (
                            <option key={r} value={r} className="bg-surface-800 text-white">
                              {r}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td className="px-4 py-3 text-slate-500 text-xs">
                        {user.created_at ? new Date(user.created_at).toLocaleDateString() : "—"}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => handleDelete(user)}
                          disabled={deleteMutation.isPending}
                          className="p-1.5 rounded text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                          title="Delete user"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
